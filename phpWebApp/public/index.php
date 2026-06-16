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

$logger = $container->get('logger');

// Attach container to Slim
AppFactory::setContainer($container);
$app = AppFactory::create();

// CORS
$logger->error('LOADED ORIGINS MENYYYYYYYYYYYYY: .' . $config->get('CORS_ORIGIN') . '.');
$app->add(CorsMiddlewareFactory::create($config));

// register global OPTIONS route before middleware and routing
// public/index.php — global OPTIONS handler (exact)
$app->options('/{routes:.+}', function ($request, $response) use ($container, $config, $logger) {
    // immediate, unmistakable log
    $logger->error('LOADED ORIGINS MENYYYYYYYYYYYYY: .' . $config->get('CORS_ORIGIN') . '.');

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

// CORS
//$app->add(CorsMiddlewareFactory::create($config));

$app->addBodyParsingMiddleware();

$app->addRoutingMiddleware();

// Error middleware (detailed in dev)
$app->addErrorMiddleware($config->isDebug(), true, true);

// Health check
$app->get('/health', function ($req, $res, $logger) {
    $logger->error('LOADED ORIGINS MENYYYYYYYYYYYYY: .' . $req . '.');
    $res->getBody()->write(json_encode(['status' => 'ok']));
    return $res->withHeader('Content-Type', 'application/json');
});

// Resolve shared services from container
/** @var Psr\Container\ContainerInterface $container */
$tokenService = $container->get('tokenService');
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
$camerasController = new \App\Controllers\CamerasController($db, $logger);
$camerasDashboardController = new \App\Controllers\CamerasDashboardController($db, $logger);
$dashboardController = new \App\Controllers\DashboardController($db, $logger);
$nodeController = new \App\Controllers\NodeController($db, $logger);
$schedulerController = new \App\Controllers\SchedulerController($db, $logger);
$userRfidsController = new \App\Controllers\UserRfidsController($db, $logger);

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
    $nodeController,
    $schedulerController,
    $userRfidsController
) {
    // Users
    $group->get('/users/me', [$usersController, 'me']);
    $group->post('/users', [$usersController, 'create']);

    // Devices
    $group->get('/devices', [$devicesController, 'list']);
    // keep existing query-based route for backward compatibility
    $group->get('/device', [$devicesController, 'get']);

    // new route: identifier can be numeric id or a tag string (user-scoped)
    $group->get('/device/{identifier}', [$devicesController, 'getByIdentifier']);

    // Device tags CRUD (per-device, user-scoped)
    $group->get('/devices/{id:[0-9]+}/tags', [$devicesController, 'listTags']);
    $group->post('/devices/{id:[0-9]+}/tags', [$devicesController, 'createTag']);
    $group->put('/devices/{id:[0-9]+}/tags/{tagId:[0-9]+}', [$devicesController, 'updateTag']);
    $group->delete('/devices/{id:[0-9]+}/tags/{tagId:[0-9]+}', [$devicesController, 'deleteTag']);

    // Cameras (service)
    $group->get('/cameras', [$camerasController, 'list']);
    $group->get('/camera/{id:[0-9]+}', [$camerasController, 'get']);

    // Video dashboards routes
    $group->get('/video-dashboards', [$camerasDashboardController, 'list']);
    $group->get('/video-dashboard/{id:[0-9]+}', [$camerasDashboardController, 'get']);
    $group->post('/video-dashboards', [$camerasDashboardController, 'create']);
    $group->put('/video-dashboard/{id:[0-9]+}', [$camerasDashboardController, 'update']);
    $group->delete('/video-dashboard/{id:[0-9]+}', [$camerasDashboardController, 'delete']);


    // Dashboard controls routes
    $group->get('/controls', [$dashboardController, 'list']);
    $group->get('/control/{id:[0-9]+}', [$dashboardController, 'get']);
    $group->get('/control-types', [$dashboardController, 'types']);
    $group->post('/controls', [$dashboardController, 'save']);
    $group->delete('/control/{id:[0-9]+}', [$dashboardController, 'delete']);

    // Nodes read-only routes
    $group->get('/nodes', [$nodeController, 'list']);
    $group->get('/node/{id}', [$nodeController, 'get']);
    $group->get('/nodes/configs', [$nodeController, 'configs']);

    // List rules (paginated)
    $group->get('/scheduler/rules', [$schedulerController, 'list']);
    $group->get('/scheduler/rules/{id:[0-9]+}', [$schedulerController, 'get']);
    $group->post('/scheduler/rules', [$schedulerController, 'create']);
    $group->put('/scheduler/rules/{id:[0-9]+}', [$schedulerController, 'update']);
    $group->delete('/scheduler/rules/{id:[0-9]+}', [$schedulerController, 'delete']);
    $group->post('/scheduler/notify-reload', [$schedulerController, 'notifyReload']);

    // User RFIDs (owner-scoped)
    $group->get('/users/{id:[0-9]+}/rfids', [ $userRfidsController, 'list' ]);
    $group->post('/users/{id:[0-9]+}/rfids', [ $userRfidsController, 'create' ]);
    $group->put('/users/{id:[0-9]+}/rfids/{rfidId:[0-9]+}', [ $userRfidsController, 'update' ]);
    $group->delete('/users/{id:[0-9]+}/rfids/{rfidId:[0-9]+}', [ $userRfidsController, 'delete' ]);

    // RFID resolve (requires auth)
    $group->post('/rfid/resolve', [ $userRfidsController, 'resolve' ]);

})->add($authMiddleware);

// Run the app
$app->run();

