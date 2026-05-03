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

$app->addBodyParsingMiddleware();
$app->addRoutingMiddleware();

// CORS
$app->add(CorsMiddlewareFactory::create($config));

// Error middleware (detailed in dev)
$app->addErrorMiddleware($config->isDebug(), true, true);

// Health check
$app->get('/health', function ($req, $res) {
    $res->getBody()->write(json_encode(['status' => 'ok']));
    return $res->withHeader('Content-Type', 'application/json');
});

// Resolve shared services from container
/** @var Psr\Container\ContainerInterface $container */
$tokenService = $container->get('tokenService');
$logger = $container->get('logger');
$db = $container->get('db');
$userService = $container->get('userService');

// Instantiate controllers with explicit dependencies (keeps wiring clear)
$authController = new \App\Controllers\AuthController(
    $userService,
    $tokenService,
    $logger,
    $db,
    $_ENV // pass env array for TTLs etc.
);

$usersController = new \App\Controllers\UsersController($db, $logger);
$devicesController = new \App\Controllers\DevicesController($db, $logger);
$camerasController = new \App\Controllers\CamerasServiceController($db, $logger);
$camerasDashboardController = new \App\Controllers\CamerasDashboardController($db, $logger);
$dashboardController = new \App\Controllers\DashboardController($db, $logger);
$nodeController = new \App\Controllers\NodeController($db, $logger);

// Public auth routes
$app->post('/auth/login', [$authController, 'login']);
$app->post('/auth/refresh', [$authController, 'refresh']);
$app->post('/auth/logout', [$authController, 'logout'])->add(new AuthMiddleware($tokenService));

// Protected API group (all routes here require a valid access token)
$authMiddleware = new AuthMiddleware($tokenService);

$app->group('/api', function (\Slim\Routing\RouteCollectorProxy $group) use (
    $usersController,
    $devicesController,
    $camerasController,
    $camerasDashboardController,
    $dashboardController,
    $nodeController
) {
    // Users
    $group->get('/users/me', [$usersController, 'me']);
    $group->post('/users', [$usersController, 'create']);

    // Devices
    $group->get('/devices', [$devicesController, 'list']);
    $group->post('/devices', [$devicesController, 'create']);
    $group->put('/devices/{id}', [$devicesController, 'update']);
    $group->delete('/devices/{id}', [$devicesController, 'delete']);

    // Cameras (service)
    $group->get('/cameras', [$camerasController, 'list']);
    $group->post('/cameras', [$camerasController, 'create']);
    $group->put('/cameras/{id}', [$camerasController, 'update']);
    $group->delete('/cameras/{id}', [$camerasController, 'delete']);

    // Cameras dashboards
    $group->get('/video-dashboards', [$camerasDashboardController, 'list']);
    $group->post('/video-dashboards', [$camerasDashboardController, 'create']);
    $group->put('/video-dashboards/{id}', [$camerasDashboardController, 'update']);
    $group->delete('/video-dashboards/{id}', [$camerasDashboardController, 'delete']);

    // Dashboard controls
    $group->get('/controls', [$dashboardController, 'list']);
    $group->get('/controls/{id}', [$dashboardController, 'get']);
    $group->get('/control-types', [$dashboardController, 'types']);
    $group->post('/controls', [$dashboardController, 'save']);
    $group->delete('/controls/{id}', [$dashboardController, 'delete']);

    // Nodes
    $group->get('/nodes', [$nodeController, 'list']);
    $group->post('/nodes', [$nodeController, 'save']);
    $group->put('/nodes/{id}', [$nodeController, 'save']);
    $group->delete('/nodes/{id}', [$nodeController, 'delete']);
    $group->get('/nodes/configs', [$nodeController, 'configs']);
})->add($authMiddleware);

// Run the app
$app->run();

