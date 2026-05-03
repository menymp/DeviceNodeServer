<?php
namespace App\Services;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use App\Config;
use Psr\Log\LoggerInterface;
use DateTimeImmutable;

class TokenService {
    private Config $config;
    private LoggerInterface $logger;
    private string $privateKey;
    private string $publicKey;
    public function __construct(Config $config, LoggerInterface $logger) {
        $this->config = $config; $this->logger = $logger;
        $privPath = $config->get('JWT_PRIVATE_KEY_PATH');
        $pubPath = $config->get('JWT_PUBLIC_KEY_PATH');
        $this->privateKey = $privPath && file_exists($privPath) ? file_get_contents($privPath) : '';
        $this->publicKey = $pubPath && file_exists($pubPath) ? file_get_contents($pubPath) : '';
    }

    public function createAccessToken(array $claims): string {
        $now = new DateTimeImmutable();
        $ttl = (int)$this->config->get('ACCESS_TOKEN_TTL', 300);
        $payload = array_merge($claims, [
            'iat' => $now->getTimestamp(),
            'exp' => $now->modify("+{$ttl} seconds")->getTimestamp(),
            'iss' => $this->config->get('JWT_ISSUER'),
            'aud' => $this->config->get('JWT_AUDIENCE')
        ]);
        return JWT::encode($payload, $this->privateKey, 'RS256');
    }

    public function validateAccessToken(string $token): ?array {
        try {
            $decoded = JWT::decode($token, new Key($this->publicKey, 'RS256'));
            return (array)$decoded;
        } catch (\Throwable $e) {
            $this->logger->warning("Token validation failed: " . $e->getMessage());
            return null;
        }
    }
}
