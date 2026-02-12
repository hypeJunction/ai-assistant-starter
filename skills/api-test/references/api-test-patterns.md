Detailed API testing patterns including request/response testing, authentication, input validation, error handling, pagination, rate limiting, and file uploads.

## Request/Response Test Patterns

### GET Requests

```typescript
describe('GET /api/resources', () => {
  it('should return 200 with list of resources', async () => {
    const res = await request(app)
      .get('/api/resources')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('data');
    expect(Array.isArray(res.body.data)).toBe(true);
  });

  it('should return 200 with single resource by id', async () => {
    const res = await request(app)
      .get('/api/resources/123')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      id: '123',
      name: expect.any(String),
      createdAt: expect.any(String),
    });
  });

  it('should return 404 when resource not found', async () => {
    const res = await request(app)
      .get('/api/resources/nonexistent')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(404);
  });
});
```

### POST Requests

```typescript
describe('POST /api/resources', () => {
  it('should return 201 with created resource', async () => {
    const payload = { name: 'New Resource', type: 'example' };

    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send(payload);

    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({
      id: expect.any(String),
      name: 'New Resource',
      type: 'example',
    });
  });
});
```

### PUT / PATCH Requests

```typescript
describe('PUT /api/resources/:id', () => {
  it('should return 200 with full replacement', async () => {
    const payload = { name: 'Updated', type: 'modified' };

    const res = await request(app)
      .put('/api/resources/123')
      .set('Authorization', `Bearer ${token}`)
      .send(payload);

    expect(res.status).toBe(200);
    expect(res.body.name).toBe('Updated');
  });
});

describe('PATCH /api/resources/:id', () => {
  it('should return 200 with partial update', async () => {
    const res = await request(app)
      .patch('/api/resources/123')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Patched' });

    expect(res.status).toBe(200);
    expect(res.body.name).toBe('Patched');
  });
});
```

### DELETE Requests

```typescript
describe('DELETE /api/resources/:id', () => {
  it('should return 204 on successful deletion', async () => {
    const res = await request(app)
      .delete('/api/resources/123')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(204);
  });

  it('should return 404 when deleting nonexistent resource', async () => {
    const res = await request(app)
      .delete('/api/resources/nonexistent')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(404);
  });
});
```

## Authentication Testing Patterns

```typescript
describe('Authentication', () => {
  it('should return 401 when no token is provided', async () => {
    const res = await request(app).get('/api/protected');

    expect(res.status).toBe(401);
    expect(res.body).toMatchObject({
      error: { message: expect.stringContaining('auth') },
    });
  });

  it('should return 401 when token is expired', async () => {
    const expiredToken = generateToken({ userId: '1', exp: Math.floor(Date.now() / 1000) - 3600 });

    const res = await request(app)
      .get('/api/protected')
      .set('Authorization', `Bearer ${expiredToken}`);

    expect(res.status).toBe(401);
  });

  it('should return 401 when token is malformed', async () => {
    const res = await request(app)
      .get('/api/protected')
      .set('Authorization', 'Bearer not-a-valid-jwt');

    expect(res.status).toBe(401);
  });

  it('should return 403 when user lacks required role', async () => {
    const viewerToken = generateToken({ userId: '1', role: 'viewer' });

    const res = await request(app)
      .delete('/api/admin/resources/123')
      .set('Authorization', `Bearer ${viewerToken}`);

    expect(res.status).toBe(403);
  });

  it('should return 200 when valid token with correct role is provided', async () => {
    const adminToken = generateToken({ userId: '1', role: 'admin' });

    const res = await request(app)
      .get('/api/admin/resources')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
  });
});
```

## Input Validation Patterns

```typescript
describe('Input Validation - POST /api/resources', () => {
  it('should return 400 when required field is missing', async () => {
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({ type: 'example' }); // missing 'name'

    expect(res.status).toBe(400);
    expect(res.body.error).toMatchObject({
      message: expect.any(String),
      fields: expect.arrayContaining([
        expect.objectContaining({ field: 'name' }),
      ]),
    });
  });

  it('should return 400 when field has wrong type', async () => {
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 123, type: 'example' }); // name should be string

    expect(res.status).toBe(400);
  });

  it('should return 400 when string exceeds max length', async () => {
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'x'.repeat(256), type: 'example' });

    expect(res.status).toBe(400);
  });

  it('should return 400 when email format is invalid', async () => {
    const res = await request(app)
      .post('/api/users')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Test', email: 'not-an-email' });

    expect(res.status).toBe(400);
  });

  it('should accept valid boundary values', async () => {
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'A', type: 'example' }); // minimum length

    expect(res.status).toBe(201);
  });
});
```

## Error Response Patterns

All error responses should follow a consistent format:

```typescript
describe('Error Response Format', () => {
  it('should return consistent error shape for 400', async () => {
    const res = await request(app)
      .post('/api/resources')
      .set('Authorization', `Bearer ${token}`)
      .send({});

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({
      error: {
        code: expect.any(String),       // e.g., 'VALIDATION_ERROR'
        message: expect.any(String),    // human-readable
      },
    });
    // Should NOT leak stack traces or internal details
    expect(res.body).not.toHaveProperty('stack');
  });

  it('should return consistent error shape for 500', async () => {
    // Trigger internal error via mock
    const res = await request(app)
      .get('/api/resources')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(500);
    expect(res.body).toMatchObject({
      error: {
        code: 'INTERNAL_ERROR',
        message: expect.any(String),
      },
    });
    // Must never expose internal implementation details
    expect(res.body.error.message).not.toContain('Cannot read properties');
  });
});
```

## Pagination Testing Patterns

```typescript
describe('Pagination - GET /api/resources', () => {
  it('should return first page with default page size', async () => {
    const res = await request(app)
      .get('/api/resources')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      data: expect.any(Array),
      meta: {
        page: 1,
        pageSize: expect.any(Number),
        total: expect.any(Number),
        totalPages: expect.any(Number),
      },
    });
    expect(res.body.data.length).toBeLessThanOrEqual(res.body.meta.pageSize);
  });

  it('should return requested page', async () => {
    const res = await request(app)
      .get('/api/resources?page=2&pageSize=5')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.meta.page).toBe(2);
    expect(res.body.data.length).toBeLessThanOrEqual(5);
  });

  it('should return empty array for page beyond total', async () => {
    const res = await request(app)
      .get('/api/resources?page=9999')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(200);
    expect(res.body.data).toEqual([]);
  });

  it('should return 400 for invalid page parameters', async () => {
    const res = await request(app)
      .get('/api/resources?page=-1')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(400);
  });
});
```

## Rate Limiting Test Considerations

```typescript
describe('Rate Limiting', () => {
  it('should return 429 when rate limit is exceeded', async () => {
    // Send requests up to the limit
    const limit = 100;
    const requests = Array.from({ length: limit + 1 }, () =>
      request(app)
        .get('/api/resources')
        .set('Authorization', `Bearer ${token}`)
    );

    const responses = await Promise.all(requests);
    const tooMany = responses.filter((r) => r.status === 429);

    expect(tooMany.length).toBeGreaterThan(0);
  });

  it('should include rate limit headers in response', async () => {
    const res = await request(app)
      .get('/api/resources')
      .set('Authorization', `Bearer ${token}`);

    expect(res.headers).toHaveProperty('x-ratelimit-limit');
    expect(res.headers).toHaveProperty('x-ratelimit-remaining');
  });
});
```

## File Upload Testing

```typescript
describe('File Upload - POST /api/uploads', () => {
  it('should return 201 when valid file is uploaded', async () => {
    const res = await request(app)
      .post('/api/uploads')
      .set('Authorization', `Bearer ${token}`)
      .attach('file', Buffer.from('file content'), 'test.txt');

    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({
      id: expect.any(String),
      filename: 'test.txt',
      size: expect.any(Number),
    });
  });

  it('should return 400 when no file is provided', async () => {
    const res = await request(app)
      .post('/api/uploads')
      .set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(400);
  });

  it('should return 400 when file exceeds size limit', async () => {
    const largeBuffer = Buffer.alloc(10 * 1024 * 1024); // 10MB

    const res = await request(app)
      .post('/api/uploads')
      .set('Authorization', `Bearer ${token}`)
      .attach('file', largeBuffer, 'large.bin');

    expect(res.status).toBe(400);
  });

  it('should return 400 when file type is not allowed', async () => {
    const res = await request(app)
      .post('/api/uploads')
      .set('Authorization', `Bearer ${token}`)
      .attach('file', Buffer.from('<?php echo "hack"; ?>'), 'exploit.php');

    expect(res.status).toBe(400);
  });
});
```

## Example Test Structure with Supertest

Complete test file structure for reference:

```typescript
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import request from 'supertest';
import { createApp } from '../app';
import { createTestDatabase, destroyTestDatabase } from './helpers/db';
import { generateToken } from './helpers/auth';
import { createUser } from './factories/user';

/**
 * Test Plan: Users API
 *
 * Scenario: CRUD operations on /api/users
 *   Given a running test server with seeded data
 *   When various HTTP methods are called with different auth states
 *   Then correct status codes and response shapes are returned
 */

let app: Express;
let db: TestDatabase;
let adminToken: string;
let userToken: string;

beforeAll(async () => {
  db = await createTestDatabase();
  app = createApp({ database: db });
  adminToken = generateToken({ role: 'admin' });
  userToken = generateToken({ role: 'user' });
});

afterAll(async () => {
  await destroyTestDatabase(db);
});

beforeEach(async () => {
  await db.truncate('users');
});

describe('/api/users', () => {
  describe('GET /api/users', () => {
    it('should return 200 with user list', async () => {
      await createUser(db, { name: 'Alice' });
      await createUser(db, { name: 'Bob' });

      const res = await request(app)
        .get('/api/users')
        .set('Authorization', `Bearer ${adminToken}`);

      expect(res.status).toBe(200);
      expect(res.body.data).toHaveLength(2);
    });

    it('should return 401 without auth', async () => {
      const res = await request(app).get('/api/users');
      expect(res.status).toBe(401);
    });
  });

  describe('POST /api/users', () => {
    it('should return 201 with created user', async () => {
      const res = await request(app)
        .post('/api/users')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Charlie', email: 'charlie@test.com' });

      expect(res.status).toBe(201);
      expect(res.body).toMatchObject({
        id: expect.any(String),
        name: 'Charlie',
        email: 'charlie@test.com',
      });
    });

    it('should return 400 when name is missing', async () => {
      const res = await request(app)
        .post('/api/users')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ email: 'missing-name@test.com' });

      expect(res.status).toBe(400);
    });

    it('should return 409 when email already exists', async () => {
      await createUser(db, { email: 'taken@test.com' });

      const res = await request(app)
        .post('/api/users')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Duplicate', email: 'taken@test.com' });

      expect(res.status).toBe(409);
    });
  });
});
```
