# Multi-stage Dockerfile for React/Vite Frontend
# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies manifest
COPY package*.json ./
RUN npm ci

# Copy application source code
COPY . .

# Pass optional API URL at build time (defaults to empty for same-origin relative URLs in Nginx reverse proxy)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve with lightweight Nginx web server
FROM nginx:1.25-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
