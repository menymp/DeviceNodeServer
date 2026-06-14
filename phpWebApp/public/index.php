<?php
declare(strict_types=1);

use Slim\Factory\AppFactory;
use App\Dependencies;
use App\Config;
use App\Middleware\CorsMiddlewareFactory;
use App\Middleware\AuthMiddleware;
use Dotenv\Dotenv;

require __DIR__ . '/../vendor/autoload.php';

$dotenv = Dotenv::createImmutable(__DIR__ . '/../');
$dotenv->safeLoad();

// Build config and DI container
$config = new Config($_ENV);
$container = Dependencies::build($config);

// Attach container to Slim
AppFactory::setContainer($container);
$app = AppFactory::create();


// Temporary test handler — insert before $app->add(...) in public/index.php

$app->options('/auth/login', function ($request, $response) use ($config) {
    $origin = $request->getHeaderLine('Origin') ?: ($config->get('CORS_ORIGIN') ?? '');
    if ($origin) {
        $response = $response
            ->withHeader('Access-Control-Allow-Origin', $origin)
            ->withHeader('Access-Control-Allow-Credentials', 'true')
            ->withHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            ->withHeader('Access-Control-Allow-Headers', $request->getHeaderLine('Access-Control-Request-Headers') ?: 'Content-Type, Authorization')
            ->withHeader('Vary', 'Origin');
    }
    return $response->withStatus(204);
});

$app->post('/auth/login', function ($request, $response) {
    $body = $request->getParsedBody() ?: json_decode((string)$request->getBody(), true) ?: [];
    $response->getBody()->write(json_encode([
        'ok' => true,
        'received' => $body,
        'time' => date('c')
    ]));
    return $response->withHeader('Content-Type', 'application/json')->withStatus(200);
});
