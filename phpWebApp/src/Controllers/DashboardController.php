<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

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
     * Query params: page, size
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['size'] ?? 50)));

        $sql = 'SELECT d.idControl AS id, d.name, d.parameters, t.typename, d.idType, u.username
                FROM dashboardcontrolt d
                INNER JOIN controlstypes t ON d.idType = t.idControlsTypes
                INNER JOIN users u ON d.idUser = u.idUser
                WHERE d.idUser = :uid
                ORDER BY d.name DESC
                LIMIT :limit OFFSET :offset';

        $stmt = $this->db->pdo()->prepare($sql);
        $stmt->bindValue(':uid', $uid, PDO::PARAM_INT);
        $stmt->bindValue(':limit', $size, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $page * $size, PDO::PARAM_INT);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        foreach ($rows as &$r) {
            $r['parameters'] = $r['parameters'] ? json_decode($r['parameters'], true) : null;
        }

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * GET /api/controls/{id}
     */
    public function get(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];
        $sql = 'SELECT d.idControl AS id, d.name, d.parameters, t.typename, t.controlTemplate
                FROM dashboardcontrolt d
                INNER JOIN controlstypes t ON d.idType = t.idControlsTypes
                WHERE d.idControl = :id LIMIT 1';
        $stmt = $this->db->pdo()->prepare($sql);
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row) return $this->json($res, ['error' => 'not_found'], 404);

        $row['parameters'] = $row['parameters'] ? json_decode($row['parameters'], true) : null;
        $res->getBody()->write(json_encode($row));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * GET /api/control-types
     */
    public function types(Request $req, Response $res): Response
    {
        $stmt = $this->db->pdo()->query('SELECT idControlsTypes AS id, typename, controlTemplate FROM controlstypes');
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/controls
     * Body: { idControl (optional), name, idType, parameters }
     * If idControl present -> update, else create
     */
    public function save(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $idControl = isset($body['idControl']) ? (int)$body['idControl'] : null;
        $name = trim($body['Name'] ?? ($body['name'] ?? ''));
        $idType = (int)($body['idType'] ?? 0);
        $parameters = $body['parameters'] ?? null;

        if ($name === '' || $idType <= 0) return $this->json($res, ['error' => 'invalid_input'], 400);

        if ($idControl && $idControl !== -1) {
            // update (ensure ownership)
            $check = $this->db->pdo()->prepare('SELECT idUser FROM dashboardcontrolt WHERE idControl = :id LIMIT 1');
            $check->execute(['id' => $idControl]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row || (int)$row['idUser'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('UPDATE dashboardcontrolt SET Name = :n, idType = :t, parameters = :p WHERE idControl = :id');
            $stmt->execute(['n' => $name, 't' => $idType, 'p' => json_encode($parameters), 'id' => $idControl]);
            return $this->json($res, ['id' => $idControl, 'name' => $name]);
        } else {
            // create
            $stmt = $this->db->pdo()->prepare('INSERT INTO dashboardcontrolt (Name, idType, idUser, parameters) VALUES (:n, :t, :uid, :p)');
            $stmt->execute(['n' => $name, 't' => $idType, 'uid' => $uid, 'p' => json_encode($parameters)]);
            $id = (int)$this->db->pdo()->lastInsertId();
            return $this->json($res, ['id' => $id, 'name' => $name], 201);
        }
    }

    /**
     * DELETE /api/controls/{id}
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];
        $check = $this->db->pdo()->prepare('SELECT idUser FROM dashboardcontrolt WHERE idControl = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idUser'] !== (int)$uid) return $this->forbidden($res);

        $stmt = $this->db->pdo()->prepare('DELETE FROM dashboardcontrolt WHERE idControl = :id');
        $stmt->execute(['id' => $id]);

        return $this->json($res, ['deleted' => $id]);
    }

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

    private function json(Response $res, $data, $status = 200): Response
    {
        $res->getBody()->write(json_encode($data));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}
