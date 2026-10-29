FROM node:22-alpine AS build
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'worker_processes auto;\npid /tmp/nginx.pid;\nerror_log /dev/stderr warn;\nevents { worker_connections 1024; }\nhttp {\n  include /etc/nginx/mime.types;\n  default_type application/octet-stream;\n  access_log /dev/stdout;\n  client_body_temp_path /tmp/client_temp;\n  proxy_temp_path /tmp/proxy_temp;\n  fastcgi_temp_path /tmp/fastcgi_temp;\n  uwsgi_temp_path /tmp/uwsgi_temp;\n  scgi_temp_path /tmp/scgi_temp;\n  server {\n    listen 8080;\n    listen [::]:8080;\n    root /usr/share/nginx/html;\n    index index.html;\n    location / {\n      try_files $uri $uri/ /index.html;\n    }\n  }\n}\n' > /etc/nginx/nginx.conf
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget -qO /dev/null http://127.0.0.1:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
