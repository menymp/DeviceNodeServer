<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

class CamerasDashboardController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/video-dashboards
     * Returns all dashboards owned by the authenticated user
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $sql = 'SELECT idvideoDashboard AS id, configJsonFetch AS config, idOwnerUser, created_at
                FROM videodashboard
                WHERE idOwnerUser = :uid
                ORDER BY created_at DESC';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['uid' => (int)$uid]);
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            foreach ($rows as &$r) {
                $r['config'] = $r['config'] !== null && $r['config'] !== ''
                    ? json_decode($r['config'], true)
                    : null;
                unset($r['configJsonFetch']);
            }

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Video dashboards list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/video-dashboards/{id}
     * Returns single dashboard owned by the authenticated user
     */
    public function get(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            return $this->jsonError($res, 'invalid_id', 400);
        }

        $sql = 'SELECT idvideoDashboard AS id, configJsonFetch AS config, idOwnerUser
                FROM videodashboard
                WHERE idvideoDashboard = :id
                LIMIT 1';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'not_found', 404);

            if ((int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

            $row['config'] = $row['config'] !== null && $row['config'] !== ''
                ? json_decode($row['config'], true)
                : null;
            unset($row['idOwnerUser']);

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Video dashboard get error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * POST /api/video-dashboards
     * Body: { configJsonFetch: {...} }
     * Creates a new dashboard owned by the authenticated user
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $config = $body['configJsonFetch'] ?? null;
        if ($config === null) return $this->jsonError($res, 'config_required', 400);

        try {
            $stmt = $this->db->pdo()->prepare('INSERT INTO videodashboard (configJsonFetch, idOwnerUser) VALUES (:cfg, :uid)');
            $stmt->execute([
                'cfg' => json_encode($config),
                'uid' => (int)$uid
            ]);
            $id = (int)$this->db->pdo()->lastInsertId();

            $res->getBody()->write(json_encode(['id' => $id]));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
        } catch (Exception $e) {
            $this->logger->error('Video dashboard create error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * PUT /api/video-dashboards/{id}
     * Body: { configJsonFetch: {...} }
     * Updates an existing dashboard owned by the authenticated user
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) return $this->jsonError($res, 'invalid_id', 400);

        $body = (array)$req->getParsedBody();
        $config = $body['configJsonFetch'] ?? null;
        if ($config === null) return $this->jsonError($res, 'config_required', 400);

        try {
            $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM videodashboard WHERE idvideoDashboard = :id LIMIT 1');
            $check->execute(['id' => $id]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'not_found', 404);
            if ((int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('UPDATE videodashboard SET configJsonFetch = :cfg WHERE idvideoDashboard = :id');
            $stmt->execute(['cfg' => json_encode($config), 'id' => $id]);

            $res->getBody()->write(json_encode(['id' => $id, 'updated' => true]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Video dashboard update error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * DELETE /api/video-dashboards/{id}
     * Deletes a dashboard owned by the authenticated user
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) return $this->jsonError($res, 'invalid_id', 400);

        try {
            $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM videodashboard WHERE idvideoDashboard = :id LIMIT 1');
            $check->execute(['id' => $id]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'not_found', 404);
            if ((int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('DELETE FROM videodashboard WHERE idvideoDashboard = :id');
            $stmt->execute(['id' => $id]);

            $res->getBody()->write(json_encode(['deleted' => $id]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Video dashboard delete error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    // Helpers
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

    private function jsonError(Response $res, string $msg, int $status = 400): Response
    {
        $res->getBody()->write(json_encode(['error' => $msg]));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}

