---
name: docker-node-guidelines
description: Docker guidelines for Node.js including Dockerfile best practices, multi-stage builds, Docker Compose, security, and health checks. Auto-loaded when working with Docker configurations.
user-invocable: false
---

# Docker Guidelines

## Core Principles

1. **Minimal images** - Include only what's needed
2. **Reproducible builds** - Pin versions, use multi-stage
3. **Security** - Don't run as root, scan for vulnerabilities
4. **Layer optimization** - Order commands for caching
5. **Health checks** - Verify container health

## Dockerfile Best Practices

### Multi-Stage Builds

```dockerfile
# Stage 1: Build
FROM {{BASE_IMAGE}} AS builder

WORKDIR /app

# Copy package files first (better caching)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Production
FROM {{BASE_IMAGE}} AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy only production dependencies
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built artifacts
COPY --from=builder /app/dist ./dist

# Use non-root user
USER nodejs

# Expose port
EXPOSE {{APP_PORT}}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:{{APP_PORT}}/health || exit 1

# Start application
CMD ["node", "{{BUILD_OUTPUT}}/{{ENTRY_POINT}}"]
```

### Layer Optimization

```dockerfile
# Bad - busts cache on any file change
COPY . .
RUN npm install

# Good - dependencies cached separately
COPY package*.json ./
RUN npm ci
COPY . .
```

### Minimize Image Size

```dockerfile
# Use alpine images
FROM {{BASE_IMAGE}}

# Clean up in same layer
RUN apk add --no-cache python3 make g++ && \
    npm ci && \
    apk del python3 make g++

# Use .dockerignore
# .dockerignore:
# node_modules
# .git
# *.md
# .env*
# coverage
# dist
```

## Security

### Non-Root User

```dockerfile
# Create and use non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set ownership
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser
```

### No Secrets in Images

```dockerfile
# Bad - secret in image history
ARG API_KEY
ENV API_KEY=$API_KEY

# Good - use runtime secrets
# Pass at runtime: docker run -e API_KEY=xxx myapp

# Or use Docker secrets
docker secret create api_key ./secret.txt
docker service create --secret api_key myapp
```

## Health Checks

### Application Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:{{APP_PORT}}/health || exit 1
```

## Known Gotchas

### Build Context

```dockerfile
# .dockerignore is crucial for performance
# Exclude:
node_modules
.git
*.md
.env*
coverage
dist
.DS_Store
```

### Cache Invalidation

```dockerfile
# ARG invalidates cache for subsequent layers
ARG CACHEBUST=1
RUN npm ci  # Runs every time if CACHEBUST changes

# Better: Use BuildKit cache mounts
RUN --mount=type=cache,target=/root/.npm npm ci
```

### Signal Handling

```dockerfile
# PID 1 problem - use dumb-init or tini
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "{{BUILD_OUTPUT}}/{{ENTRY_POINT}}"]

# Or use exec form (doesn't use shell)
CMD ["node", "{{BUILD_OUTPUT}}/{{ENTRY_POINT}}"]  # Good - node is PID 1
CMD node {{BUILD_OUTPUT}}/{{ENTRY_POINT}}         # Bad - shell is PID 1
```

### Environment vs ARG

```dockerfile
# ARG - build-time only
ARG NODE_VERSION=20

# ENV - runtime available
ENV NODE_ENV=production

# ARG to ENV pattern
ARG VERSION
ENV APP_VERSION=$VERSION
```

### Layer Caching with COPY

```dockerfile
# Specific files first for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Then rest of source
COPY . .
```

## Additional References

- [Docker Compose Patterns](references/docker-compose-patterns.md) — Development, production, and override setups; environment variables; health checks in Compose
- [Networking, Volumes, Logging](references/docker-networking-volumes-logging.md) — Service discovery, volumes, logging configuration, and common patterns
- [Security Scanning](references/docker-security-scanning.md) — Read-only filesystem and vulnerability scanning
