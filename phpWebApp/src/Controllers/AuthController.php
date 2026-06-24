<?php
namespace App\Controllers;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Log\LoggerInterface;
use App\Services\TokenService;
use App\Services\UserService;
use App\Database;
use DateTimeImmutable;
use Exception;

class AuthController {
    private UserService $userService;
    private TokenService $tokenService;
    private LoggerInterface $logger;
    private Database $db;
    private array $config;

    public function __construct(UserService $u, TokenService $t, LoggerInterface $l, Database $db, array $config = []) {
        $this->userService = $u;
        $this->tokenService = $t;
        $this->logger = $l;
        $this->db = $db;
        $this->config = $config;
    }

    /**
     * POST /auth/login
     * Body: { username, password }
     * Returns access_token and sets httpOnly refresh cookie.
     */
    public function login(Request $req, Response $res): Response {
        $body = (array)$req->getParsedBody();
        $username = $body['username'] ?? '';
        $password = $body['password'] ?? '';

        if (!$username || !$password) {
            return $this->json($res, ['error' => 'missing_credentials'], 400);
        }

        $user = $this->userService->authenticate($username, $password);
        if (!$user) {
            return $this->json($res, ['error' => 'invalid_credentials'], 401);
        }

        // Create access token with admin claim
        $access = $this->tokenService->createAccessToken([
            'sub' => $user['idUser'],
            'username' => $user['username'],
            'is_admin' => (bool)($user['is_admin'] ?? false)
        ]);

        // Create refresh token (rotatable, stored in DB)
        $refreshToken = $this->createAndStoreRefreshToken((int)$user['idUser']);

        // Set refresh token as httpOnly secure cookie (modify $res)
        $res = $this->setRefreshCookie($res, $refreshToken);

        return $this->json($res, [
            'access_token' => $access,
            'refresh_token' => $refreshToken, // not the best practice to return it in body, but for testing
            'token_type' => 'Bearer',
            'expires_in' => (int)($this->config['ACCESS_TOKEN_TTL'] ?? $_ENV['ACCESS_TOKEN_TTL'] ?? 300)
        ]);
    }

    /**
     * POST /auth/refresh
     * Reads refresh token from httpOnly cookie, validates DB, rotates token and returns new access token.
     */
    public function refresh(Request $req, Response $res): Response {
        // Read cookie
        // $cookies = $req->getCookieParams(); NOT THE BEST PRACTICE, BUT IS TESTING FOR NOW
        $body = (array)$req->getParsedBody();

        $refresh = $body['refresh_token'] ?? null;
        //$this->logger->error('MENY REFRESH TOKEN: ' . $body);
        if (!$refresh) {
            return $this->json($res, ['error' => 'no_refresh_token'], 401);
        }

        try {
            // Lookup refresh token in DB
            $stmt = $this->db->pdo()->prepare('SELECT id, user_id, expires_at, revoked FROM refresh_tokens WHERE token = :t LIMIT 1');
            $stmt->execute(['t' => $refresh]);
            $row = $stmt->fetch(\PDO::FETCH_ASSOC);

            if (!$row) {
                return $this->json($res, ['error' => 'invalid_refresh_token'], 401);
            }

            if ((int)$row['revoked'] === 1) {
                return $this->json($res, ['error' => 'revoked_refresh_token'], 401);
            }

            $expiresAt = new DateTimeImmutable($row['expires_at']);
            $now = new DateTimeImmutable();
            if ($expiresAt <= $now) {
                return $this->json($res, ['error' => 'expired_refresh_token'], 401);
            }

            $userId = (int)$row['user_id'];
            $userStmt = $this->db->pdo()->prepare('SELECT is_admin FROM users WHERE idUser = :id LIMIT 1');
            $userStmt->execute(['id' => $userId]);
            $userRow = $userStmt->fetch(PDO::FETCH_ASSOC);
            $isAdmin = (bool)($userRow['is_admin'] ?? false);

            // Rotate refresh token: mark old revoked and insert new
            $this->db->pdo()->beginTransaction();
            $upd = $this->db->pdo()->prepare('UPDATE refresh_tokens SET revoked = 1 WHERE id = :id');
            $upd->execute(['id' => $row['id']]);

            $newRefresh = $this->generateRandomToken();
            $refreshTtl = (int)($this->config['REFRESH_TOKEN_TTL'] ?? $_ENV['REFRESH_TOKEN_TTL'] ?? 1209600); // seconds
            $expires = $now->modify("+{$refreshTtl} seconds")->format('Y-m-d H:i:s');

            $ins = $this->db->pdo()->prepare('INSERT INTO refresh_tokens (user_id, token, expires_at, revoked) VALUES (:uid, :t, :exp, 0)');
            $ins->execute(['uid' => $userId, 't' => $newRefresh, 'exp' => $expires]);
            $this->db->pdo()->commit();

            // Issue new access token with admin claim
            $access = $this->tokenService->createAccessToken([
                'sub' => $userId,
                'is_admin' => $isAdmin
            ]);

            // Set new refresh cookie (modify $res)
            $res = $this->setRefreshCookie($res, $newRefresh, $refreshTtl);

            return $this->json($res, [
                'access_token' => $access,
                'token_type' => 'Bearer',
                'expires_in' => (int)($this->config['ACCESS_TOKEN_TTL'] ?? $_ENV['ACCESS_TOKEN_TTL'] ?? 300)
            ]);
        } catch (Exception $e) {
            try { $this->db->pdo()->rollBack(); } catch (\Throwable $_) {}
            $this->logger->error('Refresh token error: ' . $e->getMessage());
            return $this->json($res, ['error' => 'server_error'], 500);
        }
    }

    /**
     * POST /auth/logout
     * Revokes refresh token cookie and removes it from DB (or marks revoked).
     */
    public function logout(Request $req, Response $res): Response {
        $cookies = $req->getCookieParams();
        $refresh = $cookies['refresh_token'] ?? null;
        if ($refresh) {
            try {
                $stmt = $this->db->pdo()->prepare('UPDATE refresh_tokens SET revoked = 1 WHERE token = :t');
                $stmt->execute(['t' => $refresh]);
            } catch (Exception $e) {
                $this->logger->warning('Logout revoke failed: ' . $e->getMessage());
            }
        }

        // Clear cookie (modify $res)
        $res = $this->clearRefreshCookie($res);

        return $this->json($res, ['result' => 'ok']);
    }

    // ----------------------
    // Helpers
    // ----------------------
    private function createAndStoreRefreshToken(int $userId): string {
        $token = $this->generateRandomToken();
        $now = new DateTimeImmutable();
        $ttl = (int)($this->config['REFRESH_TOKEN_TTL'] ?? $_ENV['REFRESH_TOKEN_TTL'] ?? 1209600);
        $expires = $now->modify("+{$ttl} seconds")->format('Y-m-d H:i:s');

        $stmt = $this->db->pdo()->prepare('INSERT INTO refresh_tokens (user_id, token, expires_at, revoked) VALUES (:uid, :t, :exp, 0)');
        $stmt->execute(['uid' => $userId, 't' => $token, 'exp' => $expires]);

        return $token;
    }

    private function generateRandomToken(int $len = 48): string {
        return rtrim(strtr(base64_encode(random_bytes($len)), '+/', '-_'), '=');
    }

    /**
     * Set refresh cookie on the PSR-7 response and return the modified response.
     * Uses SameSite=None and Secure in non-development environments.
     */
    private function setRefreshCookie(Response $res, string $token, ?int $ttl = null): Response {
        $ttl = $ttl ?? (int)($this->config['REFRESH_TOKEN_TTL'] ?? $_ENV['REFRESH_TOKEN_TTL'] ?? 1209600);
        $env = $this->config['APP_ENV'] ?? $_ENV['APP_ENV'] ?? 'production';
        $secure = $env !== 'development';

        // Use rawurlencode to ensure safe cookie value
        $value = rawurlencode($token);

        $parts = [
            "refresh_token={$value}",
            "Path=/",
            "Max-Age={$ttl}",
            "HttpOnly",
            "SameSite=None"
        ];
        if ($secure) {
            $parts[] = "Secure";
        }

        $cookie = implode('; ', $parts);

        // Use withAddedHeader so we don't clobber other Set-Cookie headers
        return $res->withAddedHeader('Set-Cookie', $cookie);
    }

    /**
     * Clear the refresh cookie by setting an expired cookie on the PSR-7 response.
     */
    private function clearRefreshCookie(Response $res): Response {
        $env = $this->config['APP_ENV'] ?? $_ENV['APP_ENV'] ?? 'production';
        $secure = $env !== 'development';

        $parts = [
            "refresh_token=deleted",
            "Path=/",
            "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
            "HttpOnly",
            "SameSite=None"
        ];
        if ($secure) {
            $parts[] = "Secure";
        }

        $cookie = implode('; ', $parts);

        return $res->withAddedHeader('Set-Cookie', $cookie);
    }

    /**
     * Write JSON to response body and set Content-Type header.
     */
    private function json(Response $res, $data, $status = 200): Response {
        $payload = json_encode($data);
        $res->getBody()->write($payload);
        return $res->withHeader('Content-Type', 'application/json')->withStatus($status);
    }
}


