# API Advanced Patterns

Reference for versioning, query parameters, rate limiting, caching, and common API patterns.

## Versioning

### URL Versioning (Recommended)

```
/api/v1/users
/api/v2/users
```

### Header Versioning (Alternative)

```
GET /api/users
Accept: application/vnd.api.v2+json
```

### Deprecation Strategy

```typescript
// Response header for deprecated endpoints
X-API-Deprecated: true
X-API-Sunset: 2024-06-01
X-API-Successor: /api/v2/users

// Log deprecation warnings
app.use('/api/v1/*', (req, res, next) => {
  res.setHeader('X-API-Deprecated', 'true');
  res.setHeader('X-API-Sunset', '2024-06-01');
  logger.warn('Deprecated API accessed', {
    path: req.path,
    client: req.headers['user-agent']
  });
  next();
});
```

## Query Parameters

### Filtering

```
# Equality
GET /api/users?status=active

# Multiple values
GET /api/users?status=active,pending

# Comparison operators
GET /api/products?price[gte]=100&price[lte]=500

# Search
GET /api/users?search=john
```

### Sorting

```
# Single field (prefix with - for descending)
GET /api/users?sort=-createdAt

# Multiple fields
GET /api/users?sort=-createdAt,name
```

### Pagination

```
# Offset-based
GET /api/users?page=2&limit=20

# Cursor-based (for large datasets)
GET /api/users?cursor=eyJpZCI6MTIzfQ&limit=20
```

### Field Selection

```
# Include only specific fields
GET /api/users?fields=id,name,email

# Expand related resources
GET /api/orders?expand=customer,items
```

## Rate Limiting

### Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### 429 Response

```typescript
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retryAfter": 60
  }
}
```

## Caching

### Cache Headers

```typescript
// Static resources
Cache-Control: public, max-age=31536000, immutable

// Dynamic but cacheable
Cache-Control: private, max-age=300
ETag: "abc123"

// Never cache
Cache-Control: no-store
```

### Conditional Requests

```typescript
// Client sends
If-None-Match: "abc123"

// Server responds
304 Not Modified  // If unchanged
200 OK            // If changed, with new ETag
```

## Common Patterns

### Bulk Operations

```typescript
// Batch create
POST /api/users/batch
{
  "items": [
    { "name": "Alice", "email": "alice@example.com" },
    { "name": "Bob", "email": "bob@example.com" }
  ]
}

// Response with partial success
{
  "data": {
    "succeeded": [{ "id": "1", "name": "Alice" }],
    "failed": [{ "index": 1, "error": "Email already exists" }]
  }
}
```

### Long-Running Operations

```typescript
// Start operation
POST /api/reports/generate
Response: 202 Accepted
{
  "data": {
    "operationId": "op-123",
    "status": "pending",
    "statusUrl": "/api/operations/op-123"
  }
}

// Poll for status
GET /api/operations/op-123
{
  "data": {
    "operationId": "op-123",
    "status": "completed",
    "result": { "downloadUrl": "/api/reports/report-456" }
  }
}
```

### Webhooks

```typescript
// Webhook payload
{
  "id": "evt-123",
  "type": "order.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "orderId": "order-456",
    "total": 99.99
  }
}

// Webhook signature verification
const signature = req.headers['x-webhook-signature'];
const isValid = verifySignature(payload, signature, secret);
```
