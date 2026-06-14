<?php
// src/Middleware/CorsMiddlewareFactory.php
namespace App\Middleware;

use Tuupola\Middleware\CorsMiddleware;
use App\Config;

class CorsMiddlewareFactory {
    public static function create(Config $config): CorsMiddleware {
        // Accept comma-separated origins in env, e.g. "http://localhost:3000,https://localhost:3000"
        $originsRaw = (string)$config->get('CORS_ORIGIN', '');
        $origins = array_filter(array_map('trim', explode(',', $originsRaw)));

        // If no origins configured, default to empty array (no wildcard when credentials=true)
        // If you want to allow all origins (not recommended with credentials), set ['*'] explicitly.
        if (empty($origins)) {
            $origins = [];
        }

        return new CorsMiddleware([
            "origin" => $origins,                       // array of allowed origin strings
            "methods" => ["GET","POST","PUT","DELETE","OPTIONS"],
            "headers.allow" => ["Content-Type","Authorization","Accept"],
            "credentials" => true,
            "cache" => 0
        ]);
    }
}

