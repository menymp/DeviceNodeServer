<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

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
     * Query params: none (returns dashboards for authenticated user)
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $stmt = $this->db->pdo()->prepare('SELECT idvideoDashboard AS id, configJsonFetch AS config, created_at FROM videoDashboard WHERE idOwnerUser = :uid ORDER BY created_at DESC');
        $stmt->execute(['uid' => $uid]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/video-dashboards
     * Body: { "configJsonFetch": {...} }
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $config = $body['configJsonFetch'] ?? null;
        if ($config === null) {
            return $this->json($res, ['error' => 'config_required'], 400);
        }

        $stmt = $this->db->pdo()->prepare('INSERT INTO videoDashboard (configJsonFetch, idOwnerUser) VALUES (:cfg, :uid)');
        $stmt->execute(['cfg' => json_encode($config), 'uid' => $uid]);
        $id = (int)$this->db->pdo()->lastInsertId();

        return $this->json($res, ['id' => $id], 201);
    }

    /**
     * PUT /api/video-dashboards/{id}
     * Body: { "configJsonFetch": {...} }
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];
        $body = (array)$req->getParsedBody();
        $config = $body['configJsonFetch'] ?? null;
        if ($config === null) return $this->json($res, ['error' => 'config_required'], 400);

        // ownership check
        $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM videoDashboard WHERE idvideoDashboard = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

        $stmt = $this->db->pdo()->prepare('UPDATE videoDashboard SET configJsonFetch = :cfg WHERE idvideoDashboard = :id');
        $stmt->execute(['cfg' => json_encode($config), 'id' => $id]);

        return $this->json($res, ['id' => $id]);
    }

    /**
     * DELETE /api/video-dashboards/{id}
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];

        // ownership check
        $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM videoDashboard WHERE idvideoDashboard = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

        $stmt = $this->db->pdo()->prepare('DELETE FROM videoDashboard WHERE idvideoDashboard = :id');
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
