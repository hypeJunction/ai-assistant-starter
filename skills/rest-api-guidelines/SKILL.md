---
name: rest-api-guidelines
description: REST API design guidelines including URL structure, HTTP methods, status codes, request/response formats, and client implementation. Auto-loaded when working with API code.
user-invocable: false
---

# API Design Guidelines

## Core Principles

1. **Consistency** - Same patterns everywhere
2. **Predictability** - Clients know what to expect
3. **Discoverability** - APIs are self-documenting
4. **Resilience** - Graceful degradation, proper error handling

## REST API Design

### URL Structure

```
# Collection resources (plural nouns)
GET    /api/users              # List users
POST   /api/users              # Create user
GET    /api/users/:id          # Get user
PUT    /api/users/:id          # Replace user
PATCH  /api/users/:id          # Update user
DELETE /api/users/:id          # Delete user

# Nested resources (relationships)
GET    /api/users/:id/orders   # User's orders
POST   /api/users/:id/orders   # Create order for user

# Actions (when CRUD doesn't fit)
POST   /api/users/:id/activate
POST   /api/orders/:id/cancel
```

### Naming Conventions

```typescript
// Use plural nouns for collections
/api/users          // Not /api/user
/api/products       // Not /api/product

// Use kebab-case for multi-word resources
/api/order-items    // Not /api/orderItems
/api/user-profiles  // Not /api/userProfiles

// Avoid verbs in URLs (use HTTP methods)
GET /api/users      // Not GET /api/getUsers
DELETE /api/users/1 // Not POST /api/deleteUser
```

### HTTP Methods

| Method | Purpose | Idempotent | Safe |
|--------|---------|------------|------|
| GET | Read resource | Yes | Yes |
| POST | Create resource | No | No |
| PUT | Replace resource | Yes | No |
| PATCH | Partial update | Yes | No |
| DELETE | Remove resource | Yes | No |

### Status Codes

```typescript
// Success
200 OK              // Successful GET, PUT, PATCH
201 Created         // Successful POST (include Location header)
204 No Content      // Successful DELETE

// Client Errors
400 Bad Request     // Invalid input, validation failed
401 Unauthorized    // Not authenticated
403 Forbidden       // Authenticated but not authorized
404 Not Found       // Resource doesn't exist
409 Conflict        // Resource state conflict
422 Unprocessable   // Semantic validation error

// Server Errors
500 Internal Error  // Unexpected server error
502 Bad Gateway     // Upstream service failed
503 Unavailable     // Service temporarily down
504 Gateway Timeout // Upstream service timeout
```

## Request/Response Format

### Request Structure

```typescript
// Query parameters for filtering/pagination
GET /api/users?status=active&page=1&limit=20&sort=-createdAt

// Request body for mutations
POST /api/users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin"
}
```

### Response Structure

```typescript
// Single resource
{
  "data": {
    "id": "user-123",
    "name": "John Doe",
    "email": "john@example.com",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}

// Collection with pagination
{
  "data": [
    { "id": "user-1", "name": "Alice" },
    { "id": "user-2", "name": "Bob" }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}

// Error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "email", "message": "Invalid email format" },
      { "field": "age", "message": "Must be at least 18" }
    ]
  }
}
```

### Type Definitions

```typescript
// Standard API response wrapper
interface ApiResponse<T> {
  data: T;
  meta?: {
    requestId: string;
    timestamp: string;
  };
}

// Paginated response
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Error response
interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Array<{
      field?: string;
      message: string;
    }>;
  };
}
```

## Known Gotchas

### Content-Type Matters

```typescript
// Always set Content-Type for POST/PUT/PATCH
fetch('/api/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

### Empty Responses

```typescript
// 204 No Content has no body - don't try to parse
if (response.status === 204) {
  return null;
}
return response.json();
```

### Trailing Slashes

Be consistent - pick one and stick to it:
```
/api/users      // Preferred
/api/users/     // Alternative (configure redirects)
```

### Date Formats

Always use ISO 8601 in UTC:
```typescript
{
  "createdAt": "2024-01-15T10:30:00Z"  // UTC
}
```

## Additional References

- [API Client Implementation](references/api-client-implementation.md) — HTTP client wrapper and retry logic
- [API Advanced Patterns](references/api-advanced-patterns.md) — Versioning, query parameters, rate limiting, caching, and common patterns
