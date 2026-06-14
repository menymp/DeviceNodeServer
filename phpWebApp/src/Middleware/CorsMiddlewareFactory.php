<?php
namespace App\Middleware;

use Tuupola\Middleware\CorsMiddleware;
use App\Config;

class CorsMiddlewareFactory {
    public static function create(Config $config): CorsMiddleware {
        // Accept comma-separated origins in env, e.g. "http://localhost:3000,https://localhost:3000"
        $originsRaw = $config->get('CORS_ORIGIN', '');
        $origins = array_filter(array_map('trim', explode(',', $originsRaw)));

        // If none provided, default to empty array (no wildcard when credentials=true)
        if (empty($origins)) {
            $origins = [];
        }

        return new CorsMiddleware([
            // Tuupola accepts callable for origin; we use a callable to echo only allowed origins
            "origin" => function ($requestOrigin) use ($origins) {
                if (empty($origins)) return false;
                // allow if requestOrigin exactly matches one of the configured origins
                return in_array($requestOrigin, $origins, true) ? $requestOrigin : false;
            },
            "methods" => ["GET","POST","PUT","DELETE","OPTIONS"],
            "headers.allow" => ["Content-Type","Authorization","Accept"],
            "credentials" => true,
            "cache" => 0
        ]);
    }
}
