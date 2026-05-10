<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

class DashboardController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/controls
     * Query params: page (0-based), size
     *
     * Returns controls owned by the authenticated user:
     * idControl, Name, parameters (decoded), typename, idType, username
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['size'] ?? 50)));
        $offset = $page * $size;

        $sql = 'SELECT 
                    d.idControl,
                    d.Name,
                    d.parameters,
                    t.typename,
                    d.idType,
                    u.username
                FROM dashboardcontrolt AS d
                INNER JOIN controlstypes AS t ON d.idType = t.idControlsTypes
                INNER JOIN users AS u ON d.idUser = u.idUser
                WHERE d.idUser = :uid
                ORDER BY d.Name DESC
                LIMIT :limit OFFSET :offset';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->bindValue(':uid', (int)$uid, PDO::PARAM_INT);
            $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);
            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            foreach ($rows as &$r) {
                $r['parameters'] = $r['parameters'] !== null && $r['parameters'] !== ''
                    ? json_decode($r['parameters'], true)
                    : null;
            }

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Controls list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/controls/{id}
     * Returns single control (no ownership required to view template, but restrict to owner for consistency)
     */
    public function get(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_id']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $sql = 'SELECT 
                    d.idControl,
                    d.Name,
                    d.parameters,
                    t.typename,
                    t.controlTemplate,
                    d.idType,
                    d.idUser
                FROM dashboardcontrolt AS d
                INNER JOIN controlstypes AS t ON d.idType = t.idControlsTypes
                WHERE d.idControl = :id
                LIMIT 1';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                $res->getBody()->write(json_encode(['error' => 'not_found']));
                return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
            }

            // enforce owner-only access for control details (parameters/template)
            if ((int)$row['idUser'] !== (int)$uid) {
                return $this->forbidden($res);
            }

            $row['parameters'] = $row['parameters'] !== null && $row['parameters'] !== ''
                ? json_decode($row['parameters'], true)
                : null;

            // remove internal idUser from response
            unset($row['idUser']);

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Controls get error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/control-types
     * Returns available control types and templates.
     */
    public function types(Request $req, Response $res): Response
    {
        try {
            $stmt = $this->db->pdo()->query('SELECT idControlsTypes AS id, typename, controlTemplate FROM controlstypes');
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Control types error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * POST /api/controls
     * Body: { idControl (optional), name, idType, parameters }
     * If idControl present -> update (owner only), else create (owner = authenticated user)
     */
    public function save(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $idControl = isset($body['idControl']) ? (int)$body['idControl'] : null;
        $name = trim($body['Name'] ?? ($body['name'] ?? ''));
        $idType = isset($body['idType']) ? (int)$body['idType'] : 0;
        $parameters = $body['parameters'] ?? null;

        if ($name === '' || $idType <= 0) {
            return $this->json($res, ['error' => 'invalid_input'], 400);
        }

        try {
            if ($idControl && $idControl !== -1) {
                // update: ensure ownership
                $check = $this->db->pdo()->prepare('SELECT idUser FROM dashboardcontrolt WHERE idControl = :id LIMIT 1');
                $check->execute(['id' => $idControl]);
                $row = $check->fetch(PDO::FETCH_ASSOC);
                if (!$row || (int)$row['idUser'] !== (int)$uid) return $this->forbidden($res);

                $stmt = $this->db->pdo()->prepare('UPDATE dashboardcontrolt SET Name = :n, idType = :t, parameters = :p WHERE idControl = :id');
                $stmt->execute([
                    'n' => $name,
                    't' => $idType,
                    'p' => $parameters !== null ? json_encode($parameters) : null,
                    'id' => $idControl
                ]);

                return $this->json($res, ['id' => $idControl, 'name' => $name]);
            } else {
                // create
                $stmt = $this->db->pdo()->prepare('INSERT INTO dashboardcontrolt (Name, idType, idUser, parameters) VALUES (:n, :t, :uid, :p)');
                $stmt->execute([
                    'n' => $name,
                    't' => $idType,
                    'uid' => $uid,
                    'p' => $parameters !== null ? json_encode($parameters) : null
                ]);
                $id = (int)$this->db->pdo()->lastInsertId();
                return $this->json($res, ['id' => $id, 'name' => $name], 201);
            }
        } catch (Exception $e) {
            $this->logger->error('Controls save error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * DELETE /api/controls/{id}
     * Owner-only deletion.
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            return $this->json($res, ['error' => 'invalid_id'], 400);
        }

        try {
            $check = $this->db->pdo()->prepare('SELECT idUser FROM dashboardcontrolt WHERE idControl = :id LIMIT 1');
            $check->execute(['id' => $id]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row || (int)$row['idUser'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('DELETE FROM dashboardcontrolt WHERE idControl = :id');
            $stmt->execute(['id' => $id]);

            return $this->json($res, ['deleted' => $id]);
        } catch (Exception $e) {
            $this->logger->error('Controls delete error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    // ----------------------
    // Helpers
    // ----------------------
    private function unauth(Response $res): Response
    {
        $res->getBody()->write(json_encode(['error' => 'unauthenticated']));
        return $res->withHeader('Content-Type', 'application/json')->withStatus(401);
    }

    private function forbidden(Response $res): Response
    {
        $res->getBody()->write(json_encode(['error' => 'forbidden']));
        return $res->withHeader('Content-Type', 'application/json')->withStatus(403);
    }

    private function json(Response $res, $data, int $status = 200): Response
    {
        $res->getBody()->write(json_encode($data));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}
