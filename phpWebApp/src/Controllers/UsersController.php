<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class UsersController
{
    private Database $db;
    private LoggerInterface $logger;

    public function __construct(Database $db, LoggerInterface $logger)
    {
        $this->db = $db;
        $this->logger = $logger;
    }

    /**
     * GET /api/users/me
     * Returns basic info about the authenticated user.
     */
    public function me(Request $req, Response $res): Response
    {
        $user = $req->getAttribute('user');
        if (!$user || !isset($user['sub'])) {
            $payload = ['error' => 'unauthenticated'];
            $res->getBody()->write(json_encode($payload));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(401);
        }

        $stmt = $this->db->pdo()->prepare('SELECT id, username, created_at FROM users WHERE id = :id LIMIT 1');
        $stmt->execute(['id' => $user['sub']]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$row) {
            $res->getBody()->write(json_encode(['error' => 'not_found']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(404);
        }

        $res->getBody()->write(json_encode($row));
        return $res->withHeader('Content-Type', 'application/json');
    }

    /**
     * POST /api/users
     * Create a new user (admin or registration flow).
     * Body: { "username": "...", "password": "..." }
     */
    public function create(Request $req, Response $res): Response
    {
        $body = (array)$req->getParsedBody();
        $username = trim($body['username'] ?? '');
        $password = $body['password'] ?? '';

        if ($username === '' || $password === '') {
            $res->getBody()->write(json_encode(['error' => 'username_and_password_required']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        // Basic username validation
        if (!preg_match('/^[a-zA-Z0-9_\-\.]{3,64}$/', $username)) {
            $res->getBody()->write(json_encode(['error' => 'invalid_username']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(400);
        }

        $hash = password_hash($password, PASSWORD_DEFAULT);

        try {
            $stmt = $this->db->pdo()->prepare('INSERT INTO users (username, password_hash) VALUES (:u, :p)');
            $stmt->execute(['u' => $username, 'p' => $hash]);
            $id = (int)$this->db->pdo()->lastInsertId();
            $res->getBody()->write(json_encode(['id' => $id, 'username' => $username]));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(201);
        } catch (\PDOException $e) {
            $this->logger->warning('User create failed: ' . $e->getMessage());
            // Unique constraint violation
            $res->getBody()->write(json_encode(['error' => 'user_exists']));
            return $res->withHeader('Content-Type', 'application/json')->withStatus(409);
        }
    }
}
