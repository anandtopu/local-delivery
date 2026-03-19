##############################################################################
# Stage 1: development — hot reload
##############################################################################
FROM node:20-alpine AS development

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

##############################################################################
# Stage 2: builder — production build
##############################################################################
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

##############################################################################
# Stage 3: production — nginx to serve static files
##############################################################################
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config to support React Router (history API fallback)
RUN printf 'server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / {\n\
    try_files $uri $uri/ /index.html;\n\
  }\n\
  location /api/ {\n\
    proxy_pass http://backend:8000;\n\
    proxy_set_header Host $host;\n\
    proxy_set_header X-Real-IP $remote_addr;\n\
  }\n\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
