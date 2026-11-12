# Multi-stage build for the Next.js frontend (standalone output, non-root runtime).
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Same-origin API behind the reverse proxy (see deploy/Caddyfile). Baked in at build time.
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S fitscan && adduser -S fitscan -G fitscan
COPY --from=build /app/public ./public
COPY --from=build --chown=fitscan:fitscan /app/.next/standalone ./
COPY --from=build --chown=fitscan:fitscan /app/.next/static ./.next/static
USER fitscan
EXPOSE 3000
CMD ["node", "server.js"]
