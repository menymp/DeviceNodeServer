<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;
use Exception;

class SchedulerController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/scheduler/rules
     * Query params: page (0-based), size
     * Returns list of scheduler rules (enabled and disabled) with pagination.
     */
    public function list(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        $params = $req->getQueryParams();
        $page = max(0, (int)($params['page'] ?? 0));
        $size = max(1, min(500, (int)($params['size'] ?? 50)));
        $offset = $page * $size;

        $sql = 'SELECT id, name, enabled, rule_json, safe_state, created_at, updated_at
                FROM scheduler_rules
                ORDER BY id DESC
                LIMIT :limit OFFSET :offset';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->bindValue(':limit', (int)$size, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);
            $stmt->execute();
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

            foreach ($rows as &$r) {
                $r['rule_json'] = $r['rule_json'] !== null && $r['rule_json'] !== ''
                    ? json_decode($r['rule_json'], true)
                    : null;
                $r['safe_state'] = $r['safe_state'] !== null && $r['safe_state'] !== ''
                    ? json_decode($r['safe_state'], true)
                    : null;
            }

            $res->getBody()->write(json_encode($rows));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Scheduler list error: ' . $e->getMessage());
            $res->getBody()->write(json_encode(['error' => 'server_error']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(500);
        }
    }

    /**
     * GET /api/scheduler/rules/{id}
     * Returns single rule by id.
     */
    public function get(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            return $this->json($res, ['error' => 'invalid_id'], 400);
        }

        $sql = 'SELECT id, name, enabled, rule_json, safe_state, created_at, updated_at
                FROM scheduler_rules
                WHERE id = :id
                LIMIT 1';

        try {
            $stmt = $this->db->pdo()->prepare($sql);
            $stmt->execute(['id' => $id]);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                return $this->json($res, ['error' => 'not_found'], 404);
            }

            $row['rule_json'] = $row['rule_json'] !== null && $row['rule_json'] !== ''
                ? json_decode($row['rule_json'], true)
                : null;
            $row['safe_state'] = $row['safe_state'] !== null && $row['safe_state'] !== ''
                ? json_decode($row['safe_state'], true)
                : null;

            $res->getBody()->write(json_encode($row));
            return $res->withHeader('Content-Type', 'application/json');
        } catch (Exception $e) {
            $this->logger->error('Scheduler get error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * POST /api/scheduler/rules
     * Body: { name, enabled (optional), rule_json (object), safe_state (object optional) }
     * Creates a new scheduler rule.
     */
    public function create(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        $body = (array)$req->getParsedBody();
        $name = trim((string)($body['name'] ?? ''));
        $enabled = isset($body['enabled']) ? (int)(bool)$body['enabled'] : 1;
        $rule_json = $body['rule_json'] ?? null;
        $safe_state = $body['safe_state'] ?? null;

        if ($name === '' || !is_array($rule_json)) {
            return $this->json($res, ['error' => 'invalid_input'], 400);
        }

        try {
            $stmt = $this->db->pdo()->prepare('INSERT INTO scheduler_rules (name, enabled, rule_json, safe_state) VALUES (:name, :enabled, :rule_json, :safe_state)');
            $stmt->execute([
                'name' => $name,
                'enabled' => $enabled,
                'rule_json' => json_encode($rule_json),
                'safe_state' => $safe_state !== null ? json_encode($safe_state) : null
            ]);
            $id = (int)$this->db->pdo()->lastInsertId();
            return $this->json($res, ['id' => $id, 'name' => $name], 201);
        } catch (Exception $e) {
            $this->logger->error('Scheduler create error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * PUT /api/scheduler/rules/{id}
     * Body: { name, enabled, rule_json, safe_state }
     * Updates an existing rule. updated_at will be updated automatically by DB.
     */
    public function update(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            return $this->json($res, ['error' => 'invalid_id'], 400);
        }

        $body = (array)$req->getParsedBody();
        $name = trim((string)($body['name'] ?? ''));
        $enabled = isset($body['enabled']) ? (int)(bool)$body['enabled'] : 1;
        $rule_json = $body['rule_json'] ?? null;
        $safe_state = $body['safe_state'] ?? null;

        if ($name === '' || !is_array($rule_json)) {
            return $this->json($res, ['error' => 'invalid_input'], 400);
        }

        try {
            // Ensure rule exists
            $check = $this->db->pdo()->prepare('SELECT id FROM scheduler_rules WHERE id = :id LIMIT 1');
            $check->execute(['id' => $id]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                return $this->json($res, ['error' => 'not_found'], 404);
            }

            $stmt = $this->db->pdo()->prepare('UPDATE scheduler_rules SET name = :name, enabled = :enabled, rule_json = :rule_json, safe_state = :safe_state WHERE id = :id');
            $stmt->execute([
                'name' => $name,
                'enabled' => $enabled,
                'rule_json' => json_encode($rule_json),
                'safe_state' => $safe_state !== null ? json_encode($safe_state) : null,
                'id' => $id
            ]);

            return $this->json($res, ['id' => $id, 'ok' => true]);
        } catch (Exception $e) {
            $this->logger->error('Scheduler update error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * DELETE /api/scheduler/rules/{id}
     * Deletes a rule.
     */
    public function delete(Request $req, Response $res, array $args): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        $id = (int)($args['id'] ?? 0);
        if ($id <= 0) {
            return $this->json($res, ['error' => 'invalid_id'], 400);
        }

        try {
            $check = $this->db->pdo()->prepare('SELECT id FROM scheduler_rules WHERE id = :id LIMIT 1');
            $check->execute(['id' => $id]);
            $row = $check->fetch(PDO::FETCH_ASSOC);
            if (!$row) {
                return $this->json($res, ['error' => 'not_found'], 404);
            }

            $stmt = $this->db->pdo()->prepare('DELETE FROM scheduler_rules WHERE id = :id');
            $stmt->execute(['id' => $id]);

            return $this->json($res, ['deleted' => $id]);
        } catch (Exception $e) {
            $this->logger->error('Scheduler delete error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * POST /api/scheduler/notify-reload
     * Simple endpoint to notify the scheduler to reload rules immediately.
     * Implementation: insert a row into scheduler_reload (simple marker) so the scheduler can watch it,
     * or update a timestamp in scheduler_meta. If the DB table doesn't exist, this will attempt to create it.
     */
    public function notifyReload(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        if (!$user) return $this->unauth($res);

        try {
            // Ensure table exists (idempotent)
            $this->db->pdo()->exec("
                CREATE TABLE IF NOT EXISTS scheduler_reload (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            ");
            $stmt = $this->db->pdo()->prepare('INSERT INTO scheduler_reload () VALUES ()');
            $stmt->execute();
            return $this->json($res, ['ok' => true]);
        } catch (Exception $e) {
            $this->logger->error('Scheduler notifyReload error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
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

    private function json(Response $res, $data, int $status = 200): Response
    {
        $res->getBody()->write(json_encode($data));
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}
