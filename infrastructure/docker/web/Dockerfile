FROM node:22-alpine AS build

WORKDIR /src

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web/ ./
ENV VITE_API_BASE=/api/v1
RUN npm run build

FROM nginx:1.27-alpine

COPY infrastructure/docker/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=6 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
