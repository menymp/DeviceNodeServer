FROM php:8.2-apache
RUN apt-get update && apt-get install -y \ git \ unzip \ && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install mysqli pdo pdo_mysql
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /var/www/html/
# Copy composer files first (for caching) 
COPY composer.json composer.lock ./
# Install PHP dependencies 
RUN composer install --no-dev --optimize-autoloader
COPY . .

RUN sed -i 's|DocumentRoot /var/www/html|DocumentRoot /var/www/html/public|' /etc/apache2/sites-available/000-default.conf \
 && sed -i 's|<Directory /var/www/html>|<Directory /var/www/html/public>|' /etc/apache2/apache2.conf
# Expose port (Apache default) 
EXPOSE 80
