<?php
namespace App\Services;

use App\Repositories\UserRepository;
use Psr\Log\LoggerInterface;

class UserService {
    private UserRepository $repo;
    private LoggerInterface $logger;
    public function __construct(UserRepository $repo, LoggerInterface $logger) { $this->repo = $repo; $this->logger = $logger; }

    public function authenticate(string $username, string $password): ?array {
        $user = $this->repo->findByUsername($username);
        if (!$user) return null;
        if (password_verify($password, $user['password_hash'])) {
            return $user;
        }
        return null;
    }
}
