<?php
namespace App\Repositories;

use App\Database;
use Psr\Log\LoggerInterface;
use PDO;

class UserRepository {
    private Database $db;
    private LoggerInterface $logger;
    public function __construct(Database $db, LoggerInterface $logger) { $this->db = $db; $this->logger = $logger; }

    public function findByUsername(string $username): ?array {
        $stmt = $this->db->pdo()->prepare('SELECT idUser, username, password_hash FROM users WHERE username = :u LIMIT 1');
        $stmt->execute(['u' => $username]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ?: null;
    }

    public function createUser(string $username, string $passwordHash): int {
        $stmt = $this->db->pdo()->prepare('INSERT INTO users (username, password_hash) VALUES (:u, :p)');
        $stmt->execute(['u'=>$username,'p'=>$passwordHash]);
        return (int)$this->db->pdo()->lastInsertId();
    }
}
