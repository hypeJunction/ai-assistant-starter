# Docker Networking, Volumes, Logging, and Common Patterns

Reference for Docker networking (service discovery, internal vs external), volumes, logging configuration, and common container patterns.

## Networking

### Service Discovery

```yaml
services:
  app:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend

  nginx:
    networks:
      - frontend

networks:
  frontend:
  backend:
```

### Internal vs External

```yaml
services:
  app:
    ports:
      - "{{APP_PORT}}:{{APP_PORT}}"  # External access

  db:
    expose:
      - "5432"  # Internal only
```

## Volumes

### Named Volumes

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    driver: local
```

### Bind Mounts (Development)

```yaml
services:
  app:
    volumes:
      - .:/app:delegated  # Performance hint for macOS
      - /app/node_modules  # Preserve container's modules
```

## Logging

### Logging Configuration

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "app,environment"
        env: "NODE_ENV"
```

### Centralized Logging

```yaml
services:
  app:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "{{LOGGING_HOST}}:{{LOGGING_PORT}}"
        tag: "app.{{.Name}}"
```

## Common Patterns

### Init Container Pattern

```yaml
services:
  migrate:
    image: myapp:latest
    command: npm run migrate
    depends_on:
      db:
        condition: service_healthy

  app:
    image: myapp:latest
    depends_on:
      migrate:
        condition: service_completed_successfully
```

### Sidecar Pattern

```yaml
services:
  app:
    image: myapp:latest

  log-collector:
    image: fluent-bit:latest
    volumes:
      - app_logs:/var/log/app:ro
```
