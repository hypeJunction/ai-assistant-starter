# Docker Compose Patterns

Reference for Docker Compose development, production, and override configurations, environment variables, and health checks in Compose.

## Docker Compose

### Development Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      target: development  # Use dev stage
    ports:
      - "{{APP_PORT}}:{{APP_PORT}}"
    volumes:
      - .:/app
      - /app/node_modules  # Preserve container's node_modules
    environment:
      - NODE_ENV=development
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: myapp:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "{{APP_PORT}}:{{APP_PORT}}"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:{{APP_PORT}}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Override Files

```yaml
# docker-compose.override.yml (auto-loaded in dev)
version: '3.8'

services:
  app:
    build:
      target: development
    volumes:
      - .:/app
    command: npm run dev
```

## Health Checks

### Compose Health Check

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{APP_PORT}}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Dependency Health

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

## Environment Variables

### Development

```yaml
services:
  app:
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    env_file:
      - .env.development
```

### Production

```yaml
services:
  app:
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    external: true
  api_key:
    external: true
```
