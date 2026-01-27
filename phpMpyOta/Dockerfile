FROM php:8.2-apache
RUN apt-get update && apt-get install -y \ git \ unzip \ && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install mysqli pdo pdo_mysql
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /var/www/html/pyota
# Copy composer files first (for caching) 
COPY composer.json composer.lock ./
# Install PHP dependencies 
RUN composer install --no-dev --optimize-autoloader
COPY . .
# Expose port (Apache default) 
EXPOSE 80