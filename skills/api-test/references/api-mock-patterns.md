# API Mock and Test Infrastructure Patterns

Patterns for test database management, API mocking strategies, contract testing, and test data factories. Complements `api-test-patterns.md` with infrastructure-level concerns.

## Test Database Strategies

### Strategy 1: In-Memory Database

Best for: Unit-style API tests, fast feedback, CI environments.

```typescript
// Using SQLite in-memory with Prisma
// prisma/schema.prisma — test datasource
datasource db {
  provider = "sqlite"
  url      = "file::memory:"
}

// test-setup.ts
import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';

let prisma: PrismaClient;

beforeAll(async () => {
  // Push schema to in-memory database
  execSync('npx prisma db push', {
    env: { ...process.env, DATABASE_URL: 'file::memory:' },
  });
  prisma = new PrismaClient();
});

afterAll(async () => {
  await prisma.$disconnect();
});
```

### Strategy 2: Test Database with Transaction Rollback

Best for: Integration tests that need real database behavior.

```typescript
// Each test runs in a transaction that rolls back
import { PrismaClient } from '@prisma/client';

let prisma: PrismaClient;

beforeEach(async () => {
  // Start a transaction
  await prisma.$executeRaw`BEGIN`;
});

afterEach(async () => {
  // Roll back all changes
  await prisma.$executeRaw`ROLLBACK`;
});
```

### Strategy 3: Isolated Test Database

Best for: Full integration tests, complex queries, database-specific features.

```typescript
// docker-compose.test.yml
// services:
//   test-db:
//     image: postgres:16
//     environment:
//       POSTGRES_DB: test_db
//       POSTGRES_PASSWORD: test
//     ports:
//       - "5433:5432"

// test-setup.ts
beforeAll(async () => {
  // Run migrations on test database
  execSync('npx prisma migrate deploy', {
    env: { ...process.env, DATABASE_URL: process.env.TEST_DATABASE_URL },
  });
});

// Clean between tests
afterEach(async () => {
  // Truncate all tables (order matters for foreign keys)
  const tables = await prisma.$queryRaw`
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  `;
  for (const { tablename } of tables) {
    await prisma.$executeRawUnsafe(
      `TRUNCATE TABLE "${tablename}" CASCADE`
    );
  }
});
```

### Choosing a Strategy

| Strategy | Speed | Fidelity | Isolation | Best For |
|----------|-------|----------|-----------|----------|
| In-memory | Fast | Low (SQLite vs Postgres) | Full | Unit-style API tests |
| Transaction rollback | Medium | High | Good | Most integration tests |
| Isolated test DB | Slow | Highest | Full | DB-specific features, migrations |

## API Mocking with MSW (Mock Service Worker)

MSW intercepts requests at the network level — works in both browser and Node.js.

### Server Setup

```typescript
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Mock GET /api/users
  http.get('/api/users', () => {
    return HttpResponse.json({
      data: [
        { id: '1', name: 'Alice', email: 'alice@example.com' },
        { id: '2', name: 'Bob', email: 'bob@example.com' },
      ],
    });
  }),

  // Mock POST /api/users with validation
  http.post('/api/users', async ({ request }) => {
    const body = await request.json();

    if (!body.name || !body.email) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Missing required fields' } },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      { id: '3', ...body },
      { status: 201 }
    );
  }),

  // Mock with dynamic params
  http.get('/api/users/:id', ({ params }) => {
    if (params.id === 'nonexistent') {
      return HttpResponse.json(
        { error: { code: 'NOT_FOUND', message: 'User not found' } },
        { status: 404 }
      );
    }
    return HttpResponse.json({ id: params.id, name: 'Test User' });
  }),
];
```

### Test Integration

```typescript
// mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// vitest.setup.ts
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Per-Test Overrides

```typescript
import { server } from './mocks/server';
import { http, HttpResponse } from 'msw';

test('handles server error gracefully', async () => {
  // Override the default handler for this test only
  server.use(
    http.get('/api/users', () => {
      return HttpResponse.json(
        { error: { code: 'INTERNAL_ERROR', message: 'Database connection failed' } },
        { status: 500 }
      );
    })
  );

  const res = await request(app).get('/api/users');
  expect(res.status).toBe(500);
});
```

## Test Data Factories

Factories create consistent, valid test data with sensible defaults and easy overrides.

### Basic Factory Pattern

```typescript
// factories/user.ts
interface CreateUserInput {
  name?: string;
  email?: string;
  role?: 'admin' | 'user' | 'viewer';
}

let counter = 0;

export function buildUser(overrides: CreateUserInput = {}) {
  counter++;
  return {
    name: overrides.name ?? `Test User ${counter}`,
    email: overrides.email ?? `user${counter}@test.com`,
    role: overrides.role ?? 'user',
  };
}

// With database persistence
export async function createUser(
  db: PrismaClient,
  overrides: CreateUserInput = {}
) {
  return db.user.create({ data: buildUser(overrides) });
}
```

### Usage in Tests

```typescript
import { createUser, buildUser } from './factories/user';

test('admin can list all users', async () => {
  const admin = await createUser(db, { role: 'admin' });
  await createUser(db, { name: 'Alice' });
  await createUser(db, { name: 'Bob' });

  const token = generateToken(admin);
  const res = await request(app)
    .get('/api/users')
    .set('Authorization', `Bearer ${token}`);

  expect(res.status).toBe(200);
  expect(res.body.data).toHaveLength(3);
});

test('validates user input', async () => {
  // buildUser for request body without DB persistence
  const payload = buildUser({ email: 'invalid-email' });

  const res = await request(app)
    .post('/api/users')
    .set('Authorization', `Bearer ${adminToken}`)
    .send(payload);

  expect(res.status).toBe(400);
});
```

### Factory with Related Records

```typescript
// factories/order.ts
export async function createOrder(
  db: PrismaClient,
  overrides: Partial<OrderInput> = {}
) {
  // Create dependencies if not provided
  const user = overrides.userId
    ? { id: overrides.userId }
    : await createUser(db);

  const product = overrides.productId
    ? { id: overrides.productId }
    : await createProduct(db);

  return db.order.create({
    data: {
      userId: user.id,
      productId: product.id,
      quantity: overrides.quantity ?? 1,
      status: overrides.status ?? 'pending',
    },
  });
}
```

## Contract Testing

Ensure API consumers and providers agree on the contract (request/response shapes).

### Schema-Based Contract Testing

```typescript
import { z } from 'zod';

// Define the contract schema
const UserResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'viewer']),
  createdAt: z.string().datetime(),
});

const UserListResponseSchema = z.object({
  data: z.array(UserResponseSchema),
  meta: z.object({
    page: z.number(),
    pageSize: z.number(),
    total: z.number(),
  }),
});

// Test that the API matches the contract
test('GET /api/users matches response contract', async () => {
  const res = await request(app)
    .get('/api/users')
    .set('Authorization', `Bearer ${adminToken}`);

  expect(res.status).toBe(200);

  // Parse with Zod — throws if contract violated
  const parsed = UserListResponseSchema.parse(res.body);
  expect(parsed.data.length).toBeGreaterThan(0);
});
```

### Error Contract Testing

```typescript
const ErrorResponseSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
  }),
});

test('error responses match contract', async () => {
  const res = await request(app)
    .get('/api/users/nonexistent')
    .set('Authorization', `Bearer ${adminToken}`);

  expect(res.status).toBe(404);
  ErrorResponseSchema.parse(res.body);
});
```

## Test Server Setup Patterns

### Supertest with Express

```typescript
import { describe, it, beforeAll, afterAll, beforeEach } from 'vitest';
import request from 'supertest';
import { createApp } from '../app';

let app: Express;

beforeAll(async () => {
  app = await createApp({ database: testDb });
});

afterAll(async () => {
  await testDb.disconnect();
});
```

### Supertest with Next.js API Routes

```typescript
import { createMocks } from 'node-mocks-http';
import handler from '@/pages/api/users';

test('GET /api/users returns user list', async () => {
  const { req, res } = createMocks({
    method: 'GET',
    headers: { authorization: `Bearer ${token}` },
  });

  await handler(req, res);

  expect(res._getStatusCode()).toBe(200);
  expect(JSON.parse(res._getData())).toHaveProperty('data');
});
```

## Authentication Test Helpers

```typescript
// helpers/auth.ts
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';

interface TokenPayload {
  userId: string;
  role: 'admin' | 'user' | 'viewer';
}

export function generateToken(
  payload: Partial<TokenPayload> = {}
): string {
  return jwt.sign(
    {
      userId: payload.userId ?? 'test-user-id',
      role: payload.role ?? 'user',
    },
    JWT_SECRET,
    { expiresIn: '1h' }
  );
}

export function generateExpiredToken(): string {
  return jwt.sign(
    { userId: 'test-user-id', role: 'user' },
    JWT_SECRET,
    { expiresIn: '-1h' } // already expired
  );
}

// Pre-generate common tokens
export const tokens = {
  admin: generateToken({ role: 'admin' }),
  user: generateToken({ role: 'user' }),
  viewer: generateToken({ role: 'viewer' }),
  expired: generateExpiredToken(),
  malformed: 'not-a-valid-jwt',
};
```

## Test Organization

### Directory Structure

```
tests/
├── api/
│   ├── helpers/
│   │   ├── auth.ts          # Token generation
│   │   ├── db.ts            # Database setup/teardown
│   │   └── request.ts       # Request helpers
│   ├── factories/
│   │   ├── user.ts          # User factory
│   │   ├── product.ts       # Product factory
│   │   └── order.ts         # Order factory
│   ├── mocks/
│   │   ├── handlers.ts      # MSW handlers
│   │   └── server.ts        # MSW server setup
│   ├── contracts/
│   │   └── schemas.ts       # Response schemas (Zod)
│   ├── users.spec.ts        # User endpoint tests
│   ├── products.spec.ts     # Product endpoint tests
│   └── orders.spec.ts       # Order endpoint tests
└── setup.ts                 # Global test setup
```

### Naming Conventions

```typescript
// Test file: matches the route group
// users.spec.ts for /api/users/*

describe('/api/users', () => {
  describe('GET /api/users', () => {
    describe('authentication', () => {
      it('should return 401 when no token provided', ...);
      it('should return 403 when user lacks admin role', ...);
    });

    describe('happy path', () => {
      it('should return 200 with user list', ...);
      it('should support pagination', ...);
    });

    describe('validation', () => {
      it('should return 400 for invalid page parameter', ...);
    });
  });

  describe('POST /api/users', () => {
    // Same structure: auth → happy path → validation → edge cases
  });
});
```
