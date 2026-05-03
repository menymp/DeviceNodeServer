<?php
namespace App;

use Psr\Container\ContainerInterface;
use DI\ContainerBuilder;
use Monolog\Logger;

class Dependencies {
    public static function build(Config $config): ContainerInterface {
        $builder = new ContainerBuilder();
        $builder->addDefinitions([
            'config' => $config,
            'logger' => function() { return LoggerFactory::create(); },
            'db' => function() use ($config) {
                $pass = null;
                $pwFile = $config->get('DB_PASSWORD_FILE');
                if ($pwFile && file_exists($pwFile)) $pass = trim(file_get_contents($pwFile));
                return new Database($config->get('DB_HOST','127.0.0.1'), (int)$config->get('DB_PORT',3306), $config->get('DB_NAME'), $config->get('DB_USER'), $pass);
            },
            'tokenService' => function($c) { return new Services\TokenService($c->get('config'), $c->get('logger')); },
            'userRepository' => function($c) { return new Repositories\UserRepository($c->get('db'), $c->get('logger')); },
            'userService' => function($c) { return new Services\UserService($c->get('userRepository'), $c->get('logger')); }
        ]);
        return $builder->build();
    }
}
