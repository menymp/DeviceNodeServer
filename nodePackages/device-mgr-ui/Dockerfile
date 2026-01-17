# Stage 1: Build the React app
FROM node:20-alpine AS build
WORKDIR /app

# Copy dependency files first for caching
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

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

# Copy custom Nginx config if you want (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
