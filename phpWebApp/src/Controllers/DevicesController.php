<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

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
     * Also accepts POST with JSON body for clients that send body (compat with legacy client).
     *
     * Params (query or JSON body):
     *  - pageCount (int)  -> page index (0-based)
     *  - pageSize  (int)  -> page size
     *  - deviceName (string) -> filter devices.name LIKE %deviceName%
     *  - nodeName (string) -> filter nodestable.nodeName LIKE %nodeName%
     *  - idDevices (int) -> optional exact id filter (returns single row in array)
     *
     * Returns array of joined device rows:
     *  idDevices, name, mode, type, channelPath, nodeName, idMode, idType, idParentNode
     */
    public function list(Request $req, Response $res): Response
    {
        // Accept query params or JSON body for compatibility
        $params = $req->getQueryParams();
        if (empty($params)) {
            $body = (array)$req->getParsedBody();
            $params = $body ?: [];
        }

        $page = max(0, (int)($params['pageCount'] ?? $params['page'] ?? 0));
        $size = max(1, min(200, (int)($params['pageSize'] ?? $params['size'] ?? 50)));
        $deviceName = isset($params['deviceName']) ? $params['deviceName'] : null;
        $nodeName = isset($params['nodeName']) ? $params['nodeName'] : null;
        $idDevices = isset($params['idDevices']) ? (int)$params['idDevices'] : null;

        $sql = "SELECT 
                    devices.idDevices,
                    devices.name,
                    devicesmodes.mode,
                    devicestype.type,
                    devices.channelPath,
                    nodestable.nodeName,
                    devices.idMode,
                    devices.idType,
                    devices.idParentNode
                FROM devices
                    INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes
                    INNER JOIN devicestype ON devices.idType = devicestype.idDevicesType
                    INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable
                WHERE 1=1";

        $bindings = [];

        if ($idDevices) {
            $sql .= " AND devices.idDevices = :idDevices";
            $bindings['idDevices'] = $idDevices;
        } else {
            if ($deviceName !== null) {
                $sql .= " AND devices.name LIKE :deviceName";
                $bindings['deviceName'] = '%' . $deviceName . '%';
            }
            if ($nodeName !== null) {
                $sql .= " AND nodestable.nodeName LIKE :nodeName";
                $bindings['nodeName'] = '%' . $nodeName . '%';
            }
            $sql .= " ORDER BY devices.name DESC LIMIT :limit OFFSET :offset";
        }

        try {
            $stmt = $this->db->pdo()->prepare($sql);

            foreach ($bindings as $k => $v) {
                $stmt->bindValue(':' . $k, $v, is_int($v) ? PDO::PARAM_INT : PDO::PARAM_STR);
            }

            if (!$idDevices) {
                $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
                $stmt->bindValue(':offset', (int)($page * $size), PDO::PARAM_INT);
            }

            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Devices list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/device
     * Returns single device with joined fields.
     *
     * Supports:
     *  - /api/device?id=123
     *  - /api/device?tag=nickname   (requires authenticated user; resolves tag -> device id)
     *  - /api/device/{identifier}    (identifier can be numeric id or tag string)
     */
    public function get(Request $req, Response $res): Response
    {
        // Try to resolve device id from query params or parsed body
        $params = $req->getQueryParams();
        if (empty($params)) {
            $body = (array)$req->getParsedBody();
            $params = $body ?: [];
        }

        // If a path param was used, it will be handled by getByIdentifier route.
        // Here we support query-based id or tag.
        $id = $this->resolveDeviceIdFromRequest($req, $params, []);

        if ($id === null || $id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_id']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        return $this->fetchAndReturnDevice($id, $res);
    }

    /**
     * GET /api/device/{identifier}
     * Path identifier can be numeric id or a tag string.
     */
    public function getByIdentifier(Request $req, Response $res, array $args): Response
    {
        $id = $this->resolveDeviceIdFromRequest($req, [], $args);

        if ($id === null || $id <= 0) {
            $res->getBody()->write(json_encode(['error' => 'invalid_id_or_tag']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        return $this->fetchAndReturnDevice($id, $res);
    }

    /**
     * Helper: resolve device id from query/body/path args.
     *
     * Priority:
     * 1) explicit numeric id (query param 'id' or body 'id')
     * 2) path identifier (args['identifier']) — numeric treated as id, otherwise treated as tag
     * 3) query param 'tag' (user-scoped)
     *
     * If tag is used, it is resolved against device_tags for the authenticated user.
     */
    private function resolveDeviceIdFromRequest(Request $req, array $params = [], array $args = []): ?int
    {
        // 1) explicit numeric id in params
        $id = isset($params['id']) ? (int)$params['id'] : null;
        if ($id && $id > 0) return $id;

        // 2) path identifier
        if (!empty($args['identifier'])) {
            $identifier = (string)$args['identifier'];
            if (ctype_digit($identifier)) {
                return (int)$identifier;
            }
            // treat as tag string
            $tag = trim($identifier);
            if ($tag !== '') {
                return $this->resolveDeviceIdByTag($req, $tag);
            }
        }

        // 3) query/body tag param
        $tag = isset($params['tag']) ? trim((string)$params['tag']) : null;
        if ($tag !== null && $tag !== '') {
            return $this->resolveDeviceIdByTag($req, $tag);
        }

        return null;
    }

    /**
     * Resolve a device id by tag for the authenticated user.
     * Returns first matching device id or null.
     */
    private function resolveDeviceIdByTag(Request $req, string $tag): ?int
    {
        // Tag lookups are user-scoped. Ensure user is authenticated.
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) {
            // Not authenticated — cannot resolve user-scoped tag
            return null;
        }

        try {
            $stmt = $this->db->pdo()->prepare('SELECT idDevices FROM device_tags WHERE tag = :tag AND user_id = :uid ORDER BY created_at DESC LIMIT 1');
            $stmt->execute(['tag' => $tag, 'uid' => $uid]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if ($row && isset($row['idDevices'])) {
                return (int)$row['idDevices'];
            }
            return null;
        } catch (Exception $e) {
            $this->logger->warning('Tag lookup failed: ' . $e->getMessage());
            return null;
        }
    }

    /**
     * Fetch device row by id and return JSON response (joined fields).
     */
    private function fetchAndReturnDevice(int $id, Response $res): Response
    {
        $sql = "SELECT 
                    devices.idDevices,
                    devices.name,
                    devicesmodes.mode,
                    devicestype.type,
                    devices.channelPath,
                    nodestable.nodeName,
                    devices.idMode,
                    devices.idType,
                    devices.idParentNode
                FROM devices
                    INNER JOIN devicesmodes ON devices.idMode = devicesmodes.idDevicesModes
                    INNER JOIN devicestype ON devices.idType = devicestype.idDevicesType
                    INNER JOIN nodestable ON devices.idParentNode = nodestable.idNodesTable
                WHERE devices.idDevices = :id LIMIT 1";

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                $res->getBody()->write(json_encode(['error' => 'not_found']));
                return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
            }
            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Devices get error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }


    // ----------------------
    // Device tags (per-user nicknames/labels)
    // ----------------------

    /**
     * GET /api/devices/{id}/tags
     * Returns tags for the authenticated user and device
     */
    public function listTags(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) return $this->jsonError($res, 'invalid_device_id', 400);

        // ensure device exists
        $check = $this->db->pdo()->prepare('SELECT idDevices FROM devices WHERE idDevices = :id LIMIT 1');
        $check->execute(['id' => $id]);
        if (!$check->fetch(PDO::FETCH_ASSOC)) return $this->jsonError($res, 'device_not_found', 404);

        try {
            $stmt = $this->db->pdo()->prepare('SELECT id, idDevices, user_id, tag, created_at FROM device_tags WHERE idDevices = :id AND user_id = :uid ORDER BY created_at DESC');
            $stmt->execute(['id' => $id, 'uid' => $uid]);
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Device tags list error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * POST /api/devices/{id}/tags
     * Body: { tag: "nickname" }
     * Creates a tag for the authenticated user and device
     */
    public function createTag(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) return $this->jsonError($res, 'invalid_device_id', 400);

        $body = (array)$req->getParsedBody();
        $tag = trim((string)($body['tag'] ?? ''));

        if ($tag === '') return $this->jsonError($res, 'tag_required', 400);

        // ensure device exists
        $check = $this->db->pdo()->prepare('SELECT idDevices FROM devices WHERE idDevices = :id LIMIT 1');
        $check->execute(['id' => $id]);
        if (!$check->fetch(PDO::FETCH_ASSOC)) return $this->jsonError($res, 'device_not_found', 404);

        try {
            $stmt = $this->db->pdo()->prepare('INSERT INTO device_tags (idDevices, user_id, tag) VALUES (:idDevices, :uid, :tag)');
            $stmt->execute(['idDevices' => $id, 'uid' => $uid, 'tag' => $tag]);
            $tagId = (int)$this->db->pdo()->lastInsertId();

            $res->getBody()->write(json_encode(['id' => $tagId, 'tag' => $tag]));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
        } catch (Exception $e) {
            // handle unique constraint violation gracefully
            if ($e->getCode() === '23000') {
                return $this->jsonError($res, 'duplicate_tag', 409);
            }
            $this->logger->error('Device tag create error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * PUT /api/devices/{id}/tags/{tagId}
     * Body: { tag: "new nickname" }
     * Updates a tag owned by the authenticated user
     */
    public function updateTag(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        $tagId = (int)($args['tagId'] ?? 0);
        if ($id <= 0 || $tagId <= 0) return $this->jsonError($res, 'invalid_ids', 400);

        $body = (array)$req->getParsedBody();
        $tag = trim((string)($body['tag'] ?? ''));
        if ($tag === '') return $this->jsonError($res, 'tag_required', 400);

        try {
            // ensure tag exists and belongs to user and device
            $check = $this->db->pdo()->prepare('SELECT id, idDevices, user_id FROM device_tags WHERE id = :tagId LIMIT 1');
            $check->execute(['tagId' => $tagId]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'tag_not_found', 404);
            if ((int)$row['idDevices'] !== $id || (int)$row['user_id'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('UPDATE device_tags SET tag = :tag WHERE id = :tagId');
            $stmt->execute(['tag' => $tag, 'tagId' => $tagId]);

            $res->getBody()->write(json_encode(['id' => $tagId, 'tag' => $tag, 'updated' => true]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            if ($e->getCode() === '23000') {
                return $this->jsonError($res, 'duplicate_tag', 409);
            }
            $this->logger->error('Device tag update error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * DELETE /api/devices/{id}/tags/{tagId}
     * Deletes a tag owned by the authenticated user
     */
    public function deleteTag(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        $uid = $user['sub'] ?? null;
        if (!$uid) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        $tagId = (int)($args['tagId'] ?? 0);
        if ($id <= 0 || $tagId <= 0) return $this->jsonError($res, 'invalid_ids', 400);

        try {
            $check = $this->db->pdo()->prepare('SELECT id, idDevices, user_id FROM device_tags WHERE id = :tagId LIMIT 1');
            $check->execute(['tagId' => $tagId]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'tag_not_found', 404);
            if ((int)$row['idDevices'] !== $id || (int)$row['user_id'] !== (int)$uid) return $this->forbidden($res);

            $stmt = $this->db->pdo()->prepare('DELETE FROM device_tags WHERE id = :tagId');
            $stmt->execute(['tagId' => $tagId]);

            $res->getBody()->write(json_encode(['deleted' => $tagId]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Device tag delete error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
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
