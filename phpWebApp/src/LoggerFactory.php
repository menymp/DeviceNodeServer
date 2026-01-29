<?php
namespace App;

use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Monolog\Formatter\LineFormatter;

class LoggerFactory
{
    public static function create(): Logger
    {
        $logger = new Logger('app');

        // Log to stdout (Docker best practice)
        $handler = new StreamHandler('php://stdout', Logger::DEBUG);

        // Optional: format logs
        $formatter = new LineFormatter("[%datetime%] %level_name%: %message%\n", "Y-m-d H:i:s");
        $handler->setFormatter($formatter);

        $logger->pushHandler($handler);

        return $logger;
    }
}
