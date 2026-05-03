<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class CamerasServiceController
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

        $stmt = $this->db->pdo()->prepare('SELECT idVideoSource AS id, name, sourceParameters, created_at FROM VideoSources WHERE idCreator = :uid ORDER BY name DESC LIMIT :limit OFFSET :offset');
        $stmt->bindValue(':uid', $uid, PDO::PARAM_INT);
        $stmt->bindValue(':limit', $size, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $page * $size, PDO::PARAM_INT);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        foreach ($rows as &$r) {
            $r['sourceParameters'] = $r['sourceParameters'] ? json_decode($r['sourceParameters'], true) : null;
        }

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/cameras
     * Body: { name, sourceParameters }
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $name = trim($body['name'] ?? '');
        $params = $body['sourceParameters'] ?? null;

        if ($name === '') return $this->json($res, ['error' => 'name_required'], 400);

        $stmt = $this->db->pdo()->prepare('INSERT INTO VideoSources (name, idCreator, sourceParameters) VALUES (:n, :uid, :p)');
        $stmt->execute(['n' => $name, 'uid' => $uid, 'p' => $params ? json_encode($params) : null]);
        $id = (int)$this->db->pdo()->lastInsertId();

        return $this->json($res, ['id' => $id, 'name' => $name], 201);
    }

    /**
     * PUT /api/cameras/{id}
     * Body: { name, sourceParameters }
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
        $check = $this->db->pdo()->prepare('SELECT idCreator FROM VideoSources WHERE idVideoSource = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idCreator'] !== (int)$uid) return $this->forbidden($res);

        $stmt = $this->db->pdo()->prepare('UPDATE VideoSources SET name = :n, sourceParameters = :p WHERE idVideoSource = :id');
        $stmt->execute(['n' => $name, 'p' => $params ? json_encode($params) : null, 'id' => $id]);

        return $this->json($res, ['id' => $id, 'name' => $name]);
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

        $check = $this->db->pdo()->prepare('SELECT idCreator FROM VideoSources WHERE idVideoSource = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idCreator'] !== (int)$uid) return $this->forbidden($res);

        $stmt = $this->db->pdo()->prepare('DELETE FROM VideoSources WHERE idVideoSource = :id');
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
