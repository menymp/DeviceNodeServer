<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

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
     * Query params: page (0-based), size
     *
     * Returns rows from nodestable for the authenticated user:
     * idNodesTable, nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters (decoded JSON or null)
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['size'] ?? 50)));

        $sql = 'SELECT idNodesTable, nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters
                FROM nodestable
                ORDER BY idNodesTable DESC
                LIMIT :limit OFFSET :offset';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)($page * $size), PDO::PARAM_INT);
            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            foreach ($rows as &$r) {
                $r['connectionParameters'] = $r['connectionParameters'] !== null && $r['connectionParameters'] !== ''
                    ? json_decode($r['connectionParameters'], true)
                    : null;
            }

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Nodes list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/node/{id}
     * Returns single node row for the authenticated user.
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

        $sql = 'SELECT idNodesTable, nodeName, nodePath, idDeviceProtocol, idOwnerUser, connectionParameters
                FROM nodestable
                WHERE idNodesTable = :id
                LIMIT 1';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                $res->getBody()->write(json_encode(['error' => 'not_found']));
                return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
            }

            $row['connectionParameters'] = $row['connectionParameters'] !== null && $row['connectionParameters'] !== ''
                ? json_decode($row['connectionParameters'], true)
                : null;

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Nodes get error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/nodes/configs
     * Returns rows from supportedProtocols table.
     */
    public function configs(Request $req, Response $res): Response
    {
        try {
            $stmt = $this->db->pdo()->query('SELECT idsupportedProtocols, ProtocolName FROM supportedprotocols');
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Nodes configs error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
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
