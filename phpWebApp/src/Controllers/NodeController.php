<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class NodeController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/nodes
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

        $stmt = $this->db->pdo()->prepare('SELECT idNodesTable AS id, nodeName, nodePath, idDeviceProtocol, connectionParameters FROM nodestable WHERE idOwnerUser = :uid ORDER BY idNodesTable DESC LIMIT :limit OFFSET :offset');
        $stmt->bindValue(':uid', $uid, PDO::PARAM_INT);
        $stmt->bindValue(':limit', $size, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $page * $size, PDO::PARAM_INT);
        $stmt->execute();
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        foreach ($rows as &$r) {
            $r['connectionParameters'] = $r['connectionParameters'] ? json_decode($r['connectionParameters'], true) : null;
        }

        $res->getBody()->write(json_encode($rows));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/nodes
     * Body: { nodeName, nodePath, nodeProtocol, nodeParameters }
     * If id present -> update, else create
     */
    public function save(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $nodeName = trim($body['nodeName'] ?? '');
        $nodePath = trim($body['nodePath'] ?? '');
        $nodeProtocol = $body['nodeProtocol'] ?? null;
        $nodeParameters = $body['nodeParameters'] ?? null;
        $idNode = isset($body['idNode']) ? (int)$body['idNode'] : null;

        if ($nodeName === '' || $nodePath === '' || !$nodeProtocol) {
            return $this->json($res, ['error' => 'invalid_input'], 400);
        }

        if ($idNode && $idNode !== -1) {
            // update: ensure ownership
            $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM NodesTable WHERE idNodesTable = :id LIMIT 1');
            $check->execute(['id' => $idNode]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row || (int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('UPDATE NodesTable SET nodeName = :n, nodePath = :p, idDeviceProtocol = :proto, connectionParameters = :params WHERE idNodesTable = :id');
            $stmt->execute(['n' => $nodeName, 'p' => $nodePath, 'proto' => $nodeProtocol, 'params' => json_encode($nodeParameters), 'id' => $idNode]);
            return $this->json($res, ['id' => $idNode, 'name' => $nodeName]);
        } else {
            // create
            $stmt = $this->db->pdo()->prepare('INSERT INTO NodesTable (nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters) VALUES (:n, :p, :proto, :uid, :params)');
            $stmt->execute(['n' => $nodeName, 'p' => $nodePath, 'proto' => $nodeProtocol, 'uid' => $uid, 'params' => json_encode($nodeParameters)]);
            $id = (int)$this->db->pdo()->lastInsertId();
            return $this->json($res, ['id' => $id, 'name' => $nodeName], 201);
        }
    }

    /**
     * DELETE /api/nodes/{id}
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)$args['id'];

        $check = $this->db->pdo()->prepare('SELECT idOwnerUser FROM NodesTable WHERE idNodesTable = :id LIMIT 1');
        $check->execute(['id' => $id]);
        $row = $check->fetch(PDO::FETCH_ASSOC);
        if (!$row || (int)$row['idOwnerUser'] !== (int)$uid) return $this->forbidden($res);

        // delete devices under node first (legacy behavior)
        $delDevices = $this->db->pdo()->prepare('DELETE FROM devices WHERE idParentNode = :nid');
        $delDevices->execute(['nid' => $id]);

        $stmt = $this->db->pdo()->prepare('DELETE FROM NodesTable WHERE idNodesTable = :id');
        $stmt->execute(['id' => $id]);

        return $this->json($res, ['deleted' => $id]);
    }

    /**
     * GET /api/nodes/configs
     * Returns supported protocols (legacy supportedProtocols table)
     */
    public function configs(Request $req, Response $res): Response
    {
        $stmt = $this->db->pdo()->query('SELECT * FROM supportedProtocols');
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $res->getBody()->write(json_encode($rows));
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

    private function json(Response $res, $data, $status = 200): Response
    {
        $res->getBody()->write(json_encode($data));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}
