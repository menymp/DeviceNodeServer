FROM php:8.2-apache

RUN apt-get update && apt-get install -y --no-install-recommends \
    git unzip libzip-dev libonig-dev \
  && docker-php-ext-install pdo_mysql mysqli zip \
  && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Copy application code first
COPY . .

# Install dependencies after code is present
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-progress

# Ensure correct ownership and DocumentRoot
RUN chown -R www-data:www-data /var/www/html \
 && sed -i 's|DocumentRoot /var/www/html|DocumentRoot /var/www/html/public|' /etc/apache2/sites-available/000-default.conf \
 && sed -i 's|<Directory /var/www/html>|<Directory /var/www/html/public>|' /etc/apache2/apache2.conf

RUN cat > /etc/apache2/conf-available/app-public.conf <<'APPCONF'
<Directory /var/www/html/public>
    AllowOverride All
    Require all granted
    AcceptPathInfo On
</Directory>
APPCONF

RUN a2enmod rewrite \
 && a2enconf app-public \
 && echo "ServerName localhost" > /etc/apache2/conf-available/servername.conf \
 && a2enconf servername

EXPOSE 80
CMD ["apache2-foreground"]