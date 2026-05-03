# PHP Web API (modernized)

This repository contains a modernized PHP REST API for the React frontend. It uses Slim 4, PDO, JWT (RS256), and is designed to run in Docker with a reverse proxy (Caddy) for TLS.

## Features
- Slim 4 routing and middleware
- JWT access tokens (RS256) and refresh token table (DB)
- PDO with prepared statements
- Per-domain controllers (Users, Devices, Cameras)
- CORS configured for a single React origin
- Dockerfile and Compose-ready service
- Logging to stdout (Monolog)

## Layout
phpWebApp/
├─ composer.json
├─ Dockerfile
├─ public/index.php
├─ src/
│  ├─ Config.php
│  ├─ Dependencies.php
│  ├─ Database.php
│  ├─ LoggerFactory.php
│  ├─ Middleware/
│  ├─ Controllers/
│  ├─ Services/
│  └─ Repositories/
├─ migrations/schema.sql
├─ Caddyfile
└─ README.md

## Quick start (development)

### Prerequisites
- Docker & Docker Compose
- `mkcert` (recommended for local TLS)
- `composer` (for local dev only)

### 1. Generate RSA keys for JWT (dev)
```bash
mkdir -p secrets
# generate 2048-bit RSA key pair
openssl genpkey -algorithm RSA -out secrets/jwt_private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in secrets/jwt_private_key.pem -out secrets/jwt_public_key.pem
Do not commit secrets/ to git.

2. Generate local TLS certs (dev)
mkcert -install
mkcert localhost 127.0.0.1 ::1
# move generated files into phpWebApp/certs (do not commit)
3. Create DB and run migrations
Start your MySQL container (compose) and run:

docker exec -i nodes-db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" < phpWebApp/migrations/schema.sql

<?php
require 'vendor/autoload.php';
$pdo = new PDO("mysql:host=nodes-db;dbname=app_db", "app_user", trim(file_get_contents('/run/secrets/db_user_password')));
$hash = password_hash('ChangeMe123!', PASSWORD_DEFAULT);
$pdo->prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)')->execute(['admin', $hash]);
echo "created\n";
