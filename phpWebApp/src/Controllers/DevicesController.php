<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class DevicesController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/devices
     * Query params: optional page, size, name
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) {
            return $this->unauth($res);
        }

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['size'] ?? 50)));
        $nameFilter = isset($params['name']) ? "%{$params['name']}%" : null;

        $sql = 'SELECT id, name, channel_path, created_at FROM devices WHERE owner_id = :uid';
        if ($nameFilter) $sql .= ' AND name LIKE :name';
        $sql .= ' ORDER BY created_at DESC LIMIT :limit OFFSET :offset';

        $stmt = $this->db->pdo()->prepare($sql);
        $stmt->bindValue(':uid', $uid, PDO::PARAM_INT);
        if ($nameFilter) $stmt->bindValue(':name', $nameFilter, PDO::PARAM_STR);
        $stmt->bindValue(':limit', $size, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $page * $size, PDO::PARAM_INT);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/devices
     * Body: { "name": "...", "channelPath": "..." }
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $name = trim($body['name'] ?? '');
        $channel = trim($body['channelPath'] ?? '');

        if ($name === '') {
            $res->getBody()->write(json_encode(['error' => 'name_required']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $stmt = $this->db->pdo()->prepare('INSERT INTO devices (name, channel_path, owner_id) VALUES (:n, :c, :uid)');
        $stmt->execute(['n' => $name, 'c' => $channel, 'uid' => $uid]);
        $id = (int)$this->db->pdo()->lastInsertId();

        $res->getBody()->write(json_encode(['id' => $id, 'name' => $name]));
        return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
    }

    /**
     * PUT /api/devices/{id}
     * Body: { "name": "...", "channelPath": "..." }
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];
        $body = (array)$req->getParsedBody();
        $name = trim($body['name'] ?? '');
        $channel = trim($body['channelPath'] ?? '');

        // Ensure device belongs to user
        $check = $this->db->pdo()->prepare('SELECT owner_id FROM devices WHERE id = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['owner_id'] !== (int)$uid) {
            return $this->forbidden($res);
        }

        $stmt = $this->db->pdo()->prepare('UPDATE devices SET name = :n, channel_path = :c WHERE id = :id');
        $stmt->execute(['n' => $name, 'c' => $channel, 'id' => $id]);

        $res->getBody()->write(json_encode(['id' => $id, 'name' => $name]));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * DELETE /api/devices/{id}
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];

        // Ensure device belongs to user
        $check = $this->db->pdo()->prepare('SELECT owner_id FROM devices WHERE id = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['owner_id'] !== (int)$uid) {
            return $this->forbidden($res);
        }

        $stmt = $this->db->pdo()->prepare('DELETE FROM devices WHERE id = :id');
        $stmt->execute(['id' => $id]);

        $res->getBody()->write(json_encode(['deleted' => $id]));
        return $res->withHeader('Content-Type', 'application/json');
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
}
