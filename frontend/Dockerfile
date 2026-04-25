FROM node:20-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app/frontend
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend ./
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app/frontend
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_API_URL=http://localhost:8000 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S nextjs && adduser -S nextjs -G nextjs

COPY --from=builder --chown=nextjs:nextjs /app/frontend/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/frontend/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000/api/health').then((res) => process.exit(res.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
