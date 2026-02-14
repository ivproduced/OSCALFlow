FROM node:20-alpine AS builder

ARG AGENCY_NAME="Federal Agency"
ARG AGENCY_PRIMARY_COLOR="#002868"

WORKDIR /app

# Clone LibreChat (using specific stable version)
RUN apk add --no-cache git && \
    git clone --depth 1 --branch v0.7.0 https://github.com/danny-avila/LibreChat.git . && \
    rm -rf .git

# Install dependencies
COPY package.json* ./
RUN npm ci --legacy-peer-deps

# Copy customization files
COPY ./config/librechat.yaml ./librechat.yaml
COPY ./config/custom.css ./client/public/custom.css
COPY ./assets/* ./client/public/assets/

# Build customizations into environment
RUN echo "VITE_APP_TITLE=\"${AGENCY_NAME} AI Assistant\"" >> .env && \
    echo "VITE_PRIMARY_COLOR=\"${AGENCY_PRIMARY_COLOR}\"" >> .env

# Build frontend
RUN npm run frontend

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install production dependencies only
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev --legacy-peer-deps && \
    npm cache clean --force

# Copy built application
COPY --from=builder /app .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app

USER nodejs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["npm", "run", "backend"]
