#!/bin/sh

# Use the PORT environment variable if provided, otherwise default to 80
PORT=${PORT:-80}

echo "Starting nginx on port $PORT"
echo "Available environment variables:"
env | grep -E "(PORT|RAILWAY)" || echo "No Railway environment variables found"

# Replace the port in nginx configuration
sed -i "s/listen 80/listen $PORT/g" /etc/nginx/nginx.conf

# Test nginx configuration
nginx -t

# Start nginx
exec nginx -g "daemon off;"