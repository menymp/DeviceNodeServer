# Dockerfile for react-device-manager-ui

# Stage 1: Build the React app
FROM node:20-alpine AS build
WORKDIR /app

# Build-time args for runtime config (prefix REACT_APP_ for CRA)
ARG REACT_APP_BASE_ORIGIN
ARG REACT_APP_COMMAND_WEBSOCKET_URL
ARG REACT_APP_DEVICE_SERVICE_URL
ARG REACT_APP_VIDEO_SEED_URL
ARG NODE_ENV=production

# Make args available as env for the build step
ENV REACT_APP_BASE_ORIGIN=${REACT_APP_BASE_ORIGIN}
ENV REACT_APP_COMMAND_WEBSOCKET_URL=${REACT_APP_COMMAND_WEBSOCKET_URL}
ENV REACT_APP_DEVICE_SERVICE_URL=${REACT_APP_DEVICE_SERVICE_URL}
ENV REACT_APP_VIDEO_SEED_URL=${REACT_APP_VIDEO_SEED_URL}
ENV NODE_ENV=${NODE_ENV}

# Copy dependency files first for caching
COPY package.json yarn.lock ./

# Install all dependencies (devDependencies required for build)
RUN yarn install --frozen-lockfile --non-interactive

# Copy the rest of the source code
COPY . .

# Build the production-ready static files
RUN yarn build

# Stage 2: Serve with Nginx
FROM nginx:1.25-alpine
WORKDIR /usr/share/nginx/html

# Remove default Nginx static assets
RUN rm -rf ./*

# Copy build output from previous stage
COPY --from=build /app/build .

# Copy custom Nginx config (important for React Router)
# This expects nginx.conf to be present in the build context (project root)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

