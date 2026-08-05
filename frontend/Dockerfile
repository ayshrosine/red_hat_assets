# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Build arguments for environment variables
ARG REACT_APP_GOOGLE_CLIENT_ID
ARG REACT_APP_BACKEND_URL

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies using Yarn
RUN yarn install --frozen-lockfile

# Copy application code
COPY . .

# Set environment variables for build
ENV REACT_APP_GOOGLE_CLIENT_ID=${REACT_APP_GOOGLE_CLIENT_ID}
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Build the React application
RUN yarn build

# Production stage
FROM nginx:1.27-alpine

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Nginx must not bind to port 80 as root-restricted
# OpenShift needs unprivileged port
RUN sed -i 's/listen\s*80;/listen 8080;/' /etc/nginx/conf.d/default.conf \
    && chgrp -R 0 /var/cache/nginx /var/run /usr/share/nginx/html \
    && chmod -R g=u /var/cache/nginx /var/run /usr/share/nginx/html

# Expose port 8080
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
