#!/bin/sh

# Use the PORT environment variable if provided, otherwise default to 80
PORT=${PORT:-80}

# Replace the port in nginx configuration
sed -i "s/listen 80/listen $PORT/g" /etc/nginx/nginx.conf

# Start nginx
nginx -g "daemon off;"