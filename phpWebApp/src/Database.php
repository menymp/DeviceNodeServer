<?php
namespace App;

use PDO;

class Database {
    private PDO $pdo;
    public function __construct(string $host, int $port, string $db, string $user, ?string $pass) {
        $dsn = "mysql:host={$host};port={$port};dbname={$db};charset=utf8mb4";
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false
        ];
        $this->pdo = new PDO($dsn, $user, $pass ?? '', $options);
    }
    public function pdo(): PDO { return $this->pdo; }
}
