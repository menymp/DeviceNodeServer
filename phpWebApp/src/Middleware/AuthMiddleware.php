<?php
namespace App\Middleware;

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\RequestHandlerInterface as Handler;
use Psr\Http\Message\ResponseInterface as Response;
use App\Services\TokenService;

class AuthMiddleware {
    private TokenService $tokenService;
    public function __construct(TokenService $tokenService) { $this->tokenService = $tokenService; }
    public function __invoke(Request $request, Handler $handler): Response {
    // Allow preflight requests to pass through without auth
        if (strtoupper($request->getMethod()) === 'OPTIONS') {
            // optional debug log
            error_log('DEBUG AuthMiddleware: bypassing OPTIONS preflight for ' . $request->getUri()->getPath());
            return $handler->handle($request);
        }

        error_log('DEBUG cookies: ' . json_encode($request->getHeaderLine('Authorization')));
        error_log('DEBUG $_COOKIE: ' . json_encode($_COOKIE));
        error_log('DEBUG cookies: ' . json_encode($request->getHeaderLine('Authorization')));
        error_log('DEBUG $_COOKIE: ' . json_encode($_COOKIE));
        $auth = $request->getHeaderLine('Authorization');
        if (!$auth || !preg_match('/Bearer\s+(.*)$/i', $auth, $m)) {
            $res = new \Slim\Psr7\Response();
            $res->getBody()->write(json_encode(['error'=>'Missing token']));
            return $res->withHeader('Content-Type','application/json')->withStatus(401);
        }
        $token = $m[1];
        error_log('TOKEN: ' . json_encode($token));
        $payload = $this->tokenService->validateAccessToken($token);
        if (!$payload) {
            $res = new \Slim\Psr7\Response();
            $res->getBody()->write(json_encode(['error'=>'Invalid token']));
            return $res->withHeader('Content-Type','application/json')->withStatus(401);
        }
        $request = $request->withAttribute('user', $payload);
        return $handler->handle($request);
    }
}
