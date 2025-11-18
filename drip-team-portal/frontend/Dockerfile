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

# Copy nginx configuration
COPY nginx-railway.conf /etc/nginx/nginx.conf

# Expose port 8080 (Railway's default)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]