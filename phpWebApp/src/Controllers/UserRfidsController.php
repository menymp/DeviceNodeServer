<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

class UserRfidsController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/users/{id}/rfids
     * List RFIDs for a user (owner only).
     */
    public function list(Request $req, Response $res, array $args): Response
    {
        $auth = $req->getAttribute('user');
        $authUid = $auth['sub'] ?? null;
        $isAdmin = (bool)($auth['is_admin'] ?? false);
        if (!$authUid) return $this->unauth($res);

        $userId = (int)($args['id'] ?? 0);
        if ($userId <= 0) return $this->jsonError($res, 'invalid_user_id', 400);

        if (!$isAdmin && (int)$authUid !== $userId) return $this->forbidden($res);

        try {
            $stmt = $this->db->pdo()->prepare('SELECT id, user_id, rfid_id, label, enabled, created_at FROM user_rfids WHERE user_id = :uid ORDER BY created_at DESC');
            $stmt->execute(['uid' => $userId]);
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('User RFIDs list error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * POST /api/users/{id}/rfids
     * Body: { rfid_id: string, label?: string, enabled?: boolean }
     * Create a new RFID for the user (owner only).
     */
    public function create(Request $req, Response $res, array $args): Response
    {
        $auth = $req->getAttribute('user');
        $authUid = $auth['sub'] ?? null;
        $isAdmin = (bool)($auth['is_admin'] ?? false);
        if (!$authUid) return $this->unauth($res);

        $userId = (int)($args['id'] ?? 0);
        if ($userId <= 0) return $this->jsonError($res, 'invalid_user_id', 400);
        if (!$isAdmin && (int)$authUid !== $userId) return $this->forbidden($res);

        $body = (array)$req->getParsedBody();
        $rfid = isset($body['rfid_id']) ? trim((string)$body['rfid_id']) : '';
        $label = isset($body['label']) ? trim((string)$body['label']) : null;
        $enabled = isset($body['enabled']) ? (int)(bool)$body['enabled'] : 1;

        if ($rfid === '') return $this->jsonError($res, 'rfid_required', 400);

        try {
            $stmt = $this->db->pdo()->prepare('INSERT INTO user_rfids (user_id, rfid_id, label, enabled) VALUES (:uid, :rfid, :label, :enabled)');
            $stmt->execute([
                'uid' => $userId,
                'rfid' => $rfid,
                'label' => $label,
                'enabled' => $enabled
            ]);
            $id = (int)$this->db->pdo()->lastInsertId();
            $res->getBody()->write(json_encode(['id' => $id, 'rfid_id' => $rfid]));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
        } catch (Exception $e) {
            // unique constraint violation
            if ($e->getCode() === '23000') {
                return $this->jsonError($res, 'duplicate_rfid', 409);
            }
            $this->logger->error('User RFIDs create error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * PUT /api/users/{id}/rfids/{rfidId}
     * Body: { label?: string, enabled?: boolean }
     * Update label or enabled flag (owner only).
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $auth = $req->getAttribute('user');
        $authUid = $auth['sub'] ?? null;
        $isAdmin = (bool)($auth['is_admin'] ?? false);
        if (!$authUid) return $this->unauth($res);

        $userId = (int)($args['id'] ?? 0);
        $rfidRowId = (int)($args['rfidId'] ?? 0);
        if ($userId <= 0 || $rfidRowId <= 0) return $this->jsonError($res, 'invalid_ids', 400);
        if (!$isAdmin && (int)$authUid !== $userId) return $this->forbidden($res);

        $body = (array)$req->getParsedBody();
        $label = array_key_exists('label', $body) ? trim((string)$body['label']) : null;
        $enabled = array_key_exists('enabled', $body) ? (int)(bool)$body['enabled'] : null;

        try {
            // ensure ownership
            $check = $this->db->pdo()->prepare('SELECT id FROM user_rfids WHERE id = :id AND user_id = :uid LIMIT 1');
            $check->execute(['id' => $rfidRowId, 'uid' => $userId]);
            if (!$check->fetch(PDO::FETCH_ASSOC)) return $this->jsonError($res, 'not_found', 404);

            $fields = [];
            $params = ['id' => $rfidRowId];
            if ($label !== null) { $fields[] = 'label = :label'; $params['label'] = $label; }
            if ($enabled !== null) { $fields[] = 'enabled = :enabled'; $params['enabled'] = $enabled; }

            if (empty($fields)) return $this->jsonError($res, 'nothing_to_update', 400);

            $sql = 'UPDATE user_rfids SET ' . implode(', ', $fields) . ' WHERE id = :id';
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute($params);

            $res->getBody()->write(json_encode(['id' => $rfidRowId, 'updated' => true]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('User RFIDs update error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * DELETE /api/users/{id}/rfids/{rfidId}
     * Owner-only deletion.
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $auth = $req->getAttribute('user');
        $authUid = $auth['sub'] ?? null;
        $isAdmin = (bool)($auth['is_admin'] ?? false);
        if (!$authUid) return $this->unauth($res);

        $userId = (int)($args['id'] ?? 0);
        $rfidRowId = (int)($args['rfidId'] ?? 0);
        if ($userId <= 0 || $rfidRowId <= 0) return $this->jsonError($res, 'invalid_ids', 400);
        if (!$isAdmin && (int)$authUid !== $userId) return $this->forbidden($res);

        try {
            $check = $this->db->pdo()->prepare('SELECT id FROM user_rfids WHERE id = :id AND user_id = :uid LIMIT 1');
            $check->execute(['id' => $rfidRowId, 'uid' => $userId]);
            if (!$check->fetch(PDO::FETCH_ASSOC)) return $this->jsonError($res, 'not_found', 404);

            $stmt = $this->db->pdo()->prepare('DELETE FROM user_rfids WHERE id = :id');
            $stmt->execute(['id' => $rfidRowId]);

            $res->getBody()->write(json_encode(['deleted' => $rfidRowId]));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('User RFIDs delete error: ' . $e->getMessage());
            return $this->jsonError($res, 'server_error', 500);
        }
    }

    /**
     * POST /api/rfid/resolve
     * Body: { rfid_id: string }
     * Returns user info for a given rfid_id (used by readers). Requires auth.
     */
    public function resolve(Request $req, Response $res): Response
    {
        $auth = $req->getAttribute('user');
        $authUid = $auth['sub'] ?? null;
        if (!$authUid) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $rfid = isset($body['rfid_id']) ? trim((string)$body['rfid_id']) : '';
        if ($rfid === '') return $this->jsonError($res, 'rfid_required', 400);

        try {
            $stmt = $this->db->pdo()->prepare('
                SELECT u.idUser AS idUser, u.username
                FROM users u
                INNER JOIN user_rfids r ON r.user_id = u.idUser
                WHERE r.rfid_id = :rfid AND r.enabled = 1
                LIMIT 1
            ');
            $stmt->execute(['rfid' => $rfid]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) return $this->jsonError($res, 'not_found', 404);

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('RFID resolve error: ' . $e->getMessage());
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
