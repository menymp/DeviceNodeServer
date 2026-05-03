<?php
namespace App\Middleware;

use Tuupola\Middleware\CorsMiddleware;
use App\Config;

class CorsMiddlewareFactory {
    public static function create(Config $config): CorsMiddleware {
        $origin = $config->get('CORS_ORIGIN', '*');
        return new CorsMiddleware([
            "origin" => [$origin],
            "methods" => ["GET","POST","PUT","DELETE","OPTIONS"],
            "headers.allow" => ["Content-Type","Authorization","Accept"],
            "credentials" => true,
            "cache" => 0
        ]);
    }
}
