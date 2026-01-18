<?php

return array(
    'host' => getenv('DB_HOST'),
	'database' => getenv('DB_NAME'),
    'user' => getenv('DB_USER'),
	'pass' => getenv('DB_PASSWORD_FILE'),
);