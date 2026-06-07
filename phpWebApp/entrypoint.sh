#!/bin/sh
set -e

if [ -f /run/secrets/jwt_private_key ]; then
  mkdir -p /var/www/html/secrets
  cp /run/secrets/jwt_private_key /var/www/html/secrets/jwt_private_key
  chown www-data:www-data /var/www/html/secrets/jwt_private_key
  chmod 440 /var/www/html/secrets/jwt_private_key
fi

if [ -f /run/secrets/jwt_public_key ]; then
  cp /run/secrets/jwt_public_key /var/www/html/secrets/jwt_public_key
  chown www-data:www-data /var/www/html/secrets/jwt_public_key
  chmod 440 /var/www/html/secrets/jwt_public_key
fi

exec "$@"