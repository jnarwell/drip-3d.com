FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build arguments for environment variables
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_AUTH0_AUDIENCE
ARG VITE_API_URL

# Set environment variables for build
ENV VITE_AUTH0_DOMAIN=$VITE_AUTH0_DOMAIN
ENV VITE_AUTH0_CLIENT_ID=$VITE_AUTH0_CLIENT_ID
ENV VITE_AUTH0_AUDIENCE=$VITE_AUTH0_AUDIENCE
ENV VITE_API_URL=$VITE_API_URL

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