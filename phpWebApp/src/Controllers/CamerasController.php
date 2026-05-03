<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class CamerasController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/cameras
     * Optional query params: page, size
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) {
            $res->getBody()->write(json_encode(['error' => 'unauthenticated']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(401);
        }

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['size'] ?? 50)));

        $stmt = $this->db->pdo()->prepare('SELECT id, name, source_parameters, created_at FROM cameras WHERE owner_id = :uid ORDER BY created_at DESC LIMIT :limit OFFSET :offset');
        $stmt->bindValue(':uid', $uid, PDO::PARAM_INT);
        $stmt->bindValue(':limit', $size, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $page * $size, PDO::PARAM_INT);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // decode JSON column for each row
        foreach ($rows as &$r) {
            $r['source_parameters'] = $r['source_parameters'] ? json_decode($r['source_parameters'], true) : null;
        }

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/cameras
     * Body: { "name": "...", "sourceParameters": {...} }
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) {
            $res->getBody()->write(json_encode(['error' => 'unauthenticated']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(401);
        }

        $body = (array)$req->getParsedBody();
        $name = trim($body['name'] ?? '');
        $params = $body['sourceParameters'] ?? null;

        if ($name === '') {
            $res->getBody()->write(json_encode(['error' => 'name_required']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $stmt = $this->db->pdo()->prepare('INSERT INTO cameras (name, source_parameters, owner_id) VALUES (:n, :p, :uid)');
        $stmt->execute(['n' => $name, 'p' => $params ? json_encode($params) : null, 'uid' => $uid]);
        $id = (int)$this->db->pdo()->lastInsertId();

        $res->getBody()->write(json_encode(['id' => $id, 'name' => $name]));
        return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
    }

    /**
     * PUT /api/cameras/{id}
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];
        $body = (array)$req->getParsedBody();
        $name = trim($body['name'] ?? '');
        $params = $body['sourceParameters'] ?? null;

        // ownership check
        $check = $this->db->pdo()->prepare('SELECT owner_id FROM cameras WHERE id = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['owner_id'] !== (int)$uid) {
            return $this->forbidden($res);
        }

        $stmt = $this->db->pdo()->prepare('UPDATE cameras SET name = :n, source_parameters = :p WHERE id = :id');
        $stmt->execute(['n' => $name, 'p' => $params ? json_encode($params) : null, 'id' => $id]);

        $res->getBody()->write(json_encode(['id' => $id, 'name' => $name]));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * DELETE /api/cameras/{id}
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];

        $check = $this->db->pdo()->prepare('SELECT owner_id FROM cameras WHERE id = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['owner_id'] !== (int)$uid) {
            return $this->forbidden($res);
        }

        $stmt = $this->db->pdo()->prepare('DELETE FROM cameras WHERE id = :id');
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

