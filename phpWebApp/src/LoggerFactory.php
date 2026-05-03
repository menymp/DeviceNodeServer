<?php
namespace App;

use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Monolog\Formatter\LineFormatter;

class LoggerFactory {
    public static function create(): Logger {
        $logger = new Logger('app');
        $handler = new StreamHandler('php://stdout', Logger::DEBUG);
        $handler->setFormatter(new LineFormatter("[%datetime%] %level_name%: %message%\n", "Y-m-d H:i:s"));
        $logger->pushHandler($handler);
        return $logger;
    }
}

