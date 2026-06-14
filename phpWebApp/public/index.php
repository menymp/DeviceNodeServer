<?php
declare(strict_types=1);

// header("Access-Control-Allow-Origin: *");
// header('Access-Control-Allow-Headers: Content-Type');

use Slim\Factory\AppFactory;
use App\Dependencies;
use App\Config;
// use App\Middleware\CorsMiddlewareFactory;
// use App\Middleware\AuthMiddleware;
use Dotenv\Dotenv;

require __DIR__ . '/../vendor/autoload.php';

$dotenv = Dotenv::createImmutable(__DIR__ . '/../');
$dotenv->safeLoad();

// Build config and DI container
$config = new Config($_ENV);
$container = Dependencies::build($config);

header("Access-Control-Allow-Origin: http://localhost:3000");
header("Access-Control-Allow-Credentials: true");

// Attach container to Slim
AppFactory::setContainer($container);
$app = AppFactory::create();

// TEMP debug handler for /auth/login
$app->options('/auth/login', function ($request, $response) use ($config) {
    // write a file so we can confirm execution
    // @file_put_contents('/tmp/test_options_hit', date('c') . " " . $request->getMethod() . " " . $request->getUri()->getPath() . PHP_EOL, FILE_APPEND);

    $origin = $request->getHeaderLine('Origin') ?: 'http://localhost:3000';
    $response = $response
        ->withHeader('Access-Control-Allow-Origin', $origin)
        ->withHeader('Access-Control-Allow-Credentials', 'true')
        ->withHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        ->withHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        ->withHeader('Vary', 'Origin')
        ->withHeader('Content-Type', 'application/json');

    $response->getBody()->write(json_encode(['ok' => true, 'method' => 'OPTIONS', 'origin' => $origin]));
    return $response->withStatus(200);
});

