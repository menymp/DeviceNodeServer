<?php
namespace App;

class Config {
    private array $env;
    public function __construct(array $env) { $this->env = $env; }
    public function get(string $k, $d = null) { return $this->env[$k] ?? $d; }
    public function isDebug(): bool { return ($this->get('APP_DEBUG','false') === 'true'); }
}
