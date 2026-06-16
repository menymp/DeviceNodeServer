<?php
namespace App\Middleware;

use Tuupola\Middleware\CorsMiddleware;
use App\Config;
use Psr\Log\LoggerInterface;

class CorsMiddlewareFactory {
    public static function create(Config $config, ?LoggerInterface $logger = null): CorsMiddleware {
        $originsRaw = (string)$config->get('CORS_ORIGIN', '');
        $origins = array_filter(array_map('trim', explode(',', $originsRaw)));
        $logger->error('CORS CALLED MENUUUUUUU: .');
        // if empty, use empty array (do not use '*' when credentials true)
        return new CorsMiddleware([
            "origin" => $origins,
            "methods" => ["GET","POST","PUT","DELETE","OPTIONS"],
            "headers.allow" => ["Content-Type","Authorization","Accept"],
            "credentials" => true,
            "cache" => 0,
            "logger" => $logger
        ]);
    }
}

