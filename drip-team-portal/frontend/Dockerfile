FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration and startup script
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /start.sh

EXPOSE 80

CMD ["/start.sh"]