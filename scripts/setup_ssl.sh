#!/bin/bash
# Script to initialize SSL certificates with Let's Encrypt
# Usage: ./setup_ssl.sh yourdomain.com your@email.com

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 yourdomain.com your@email.com"
    exit 1
fi

# Create required directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Replace domain in nginx/ssl.conf.example
sed "s/example.com/$DOMAIN/g" ./nginx/ssl.conf.example > ./nginx/ssl.conf

# Configure docker-compose override for SSL
cat > ./docker-compose.override.yml << EOL
version: '3.8'

services:
  web:
    environment:
      - VIRTUAL_HOST=$DOMAIN
      - LETSENCRYPT_HOST=$DOMAIN
      - LETSENCRYPT_EMAIL=$EMAIL
        
  nginx:
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    ports:
      - "80:80"
      - "443:443"
        
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \$\${!}; done;'"
    depends_on:
      - nginx
EOL

echo "SSL config created for $DOMAIN"
echo "Next steps:"
echo "1. Start the services: docker-compose up -d nginx"
echo "2. Run Certbot: docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email $EMAIL --agree-tos --no-eff-email -d $DOMAIN"
echo "3. After certificates are generated, restart everything: docker-compose down && docker-compose up -d"