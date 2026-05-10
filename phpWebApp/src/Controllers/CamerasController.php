<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

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
     * Query params: pageCount (0-based), pageSize
     *
     * Returns array of camera rows:
     *  idVideoSource, name, username, sourceParameters (decoded JSON or null)
     *
     * Accepts query params or JSON body for compatibility with different clients.
     */
    public function list(Request $req, Response $res): Response
    {
        // Accept query params or JSON body
        $params = $req->getQueryParams();
        if (empty($params)) {
            $body = (array)$req->getParsedBody();
            $params = $body ?: [];
        }

        $page = max(0, (int)($params['pageCount'] ?? $params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['pageSize'] ?? $params['size'] ?? 50)));
        $offset = $page * $size;

        $sql = "SELECT 
                    VideoSources.idVideoSource,
                    VideoSources.name,
                    users.username,
                    VideoSources.sourceParameters
                FROM videosources AS VideoSources
                    INNER JOIN users ON VideoSources.idCreator = users.idUser
                ORDER BY VideoSources.name DESC
                LIMIT :limit OFFSET :offset";

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);
            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            foreach ($rows as &$r) {
                $r['sourceParameters'] = $r['sourceParameters'] !== null && $r['sourceParameters'] !== ''
                    ? json_decode($r['sourceParameters'], true)
                    : null;
            }

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Cameras list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/camera/{id}
     * Returns single camera row.
     */
    public function get(Request $req, Response $res, array $args): Response
    {
        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_id']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $sql = "SELECT 
                    VideoSources.idVideoSource,
                    VideoSources.name,
                    users.username,
                    VideoSources.sourceParameters
                FROM videosources AS VideoSources
                    INNER JOIN users ON VideoSources.idCreator = users.idUser
                WHERE VideoSources.idVideoSource = :id
                LIMIT 1";

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                $res->getBody()->write(json_encode(['error' => 'not_found']));
                return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
            }

            $row['sourceParameters'] = $row['sourceParameters'] !== null && $row['sourceParameters'] !== ''
                ? json_decode($row['sourceParameters'], true)
                : null;

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Cameras get error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    // ----------------------
    // Helpers
    // ----------------------
    private function jsonError(Response $res, string $msg, int $status = 400): Response
    {
        $res->getBody()->write(json_encode(['error' => $msg]));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}