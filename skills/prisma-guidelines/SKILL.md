---
name: prisma-guidelines
description: "Prisma ORM guidelines including schema design, Client queries, transactions, migrations, and performance optimization. Auto-loaded when working with Prisma schema or Client code."
user-invocable: false
---

# Prisma Guidelines

## Core Principles

1. **Data integrity** - Use constraints, transactions, foreign keys
2. **Query efficiency** - Optimize queries, use indexes
3. **Safe migrations** - Always reversible, no data loss
4. **Security** - Parameterized queries, least privilege
5. **Consistency** - Naming conventions, patterns

## Prisma Schema Design

### Model Conventions

```prisma
// Models: PascalCase, singular
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  firstName String   @map("first_name")
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  orders Order[]

  @@map("users")
}

model Order {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  status    OrderStatus @default(PENDING)
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  user User @relation(fields: [userId], references: [id])

  @@index([userId])
  @@map("orders")
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}
```

### Standard Fields

```prisma
// Every model should have these
model Example {
  id        String   @id @default(uuid())
  // ... other fields ...
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("examples")
}

// Soft delete pattern (when needed)
model Example {
  // ...
  deletedAt DateTime? @map("deleted_at")  // null = not deleted
  // ...
}
```

### Relations

```prisma
// One-to-many
model User {
  id     String  @id @default(uuid())
  orders Order[]
  @@map("users")
}

model Order {
  id     String @id @default(uuid())
  userId String @map("user_id")
  user   User   @relation(fields: [userId], references: [id])
  @@map("orders")
}

// Many-to-many (explicit join table)
model Post {
  id   String     @id @default(uuid())
  tags PostTag[]
  @@map("posts")
}

model Tag {
  id    String    @id @default(uuid())
  posts PostTag[]
  @@map("tags")
}

model PostTag {
  postId String @map("post_id")
  tagId  String @map("tag_id")
  post   Post   @relation(fields: [postId], references: [id])
  tag    Tag    @relation(fields: [tagId], references: [id])
  @@id([postId, tagId])
  @@map("post_tags")
}
```

## Prisma Client Queries

### Basic CRUD

```typescript
// Create
const user = await prisma.user.create({
  data: { email, firstName },
});

// Read
const user = await prisma.user.findUnique({
  where: { email },
});

const users = await prisma.user.findMany({
  where: { firstName: { contains: 'John' } },
  orderBy: { createdAt: 'desc' },
});

// Update
const user = await prisma.user.update({
  where: { id },
  data: { firstName: 'Jane' },
});

// Delete
await prisma.user.delete({
  where: { id },
});
```

### Selecting Fields and Relations

```typescript
// Select only needed fields
const user = await prisma.user.findUnique({
  where: { id },
  select: { id: true, email: true, firstName: true },
});

// Include relations (avoids N+1)
const usersWithOrders = await prisma.user.findMany({
  include: {
    orders: {
      where: { status: 'CONFIRMED' },
      orderBy: { createdAt: 'desc' },
    },
  },
});

// Nested select
const user = await prisma.user.findUnique({
  where: { id },
  select: {
    id: true,
    email: true,
    orders: {
      select: { id: true, status: true },
    },
  },
});
```

### Filtering and Pagination

```typescript
// Complex filters
const users = await prisma.user.findMany({
  where: {
    AND: [
      { email: { endsWith: '@example.com' } },
      { createdAt: { gte: new Date('2024-01-01') } },
      { orders: { some: { status: 'CONFIRMED' } } },
    ],
  },
});

// Offset pagination
const users = await prisma.user.findMany({
  skip: 40,
  take: 20,
  orderBy: { createdAt: 'desc' },
});

// Cursor pagination (efficient for large datasets)
const users = await prisma.user.findMany({
  take: 20,
  cursor: { id: lastUserId },
  skip: 1, // skip the cursor itself
  orderBy: { createdAt: 'desc' },
});
```

### Aggregation and Grouping

```typescript
// Count
const count = await prisma.user.count({
  where: { deletedAt: null },
});

// Aggregate
const stats = await prisma.order.aggregate({
  _avg: { amount: true },
  _sum: { amount: true },
  _count: true,
  where: { status: 'CONFIRMED' },
});

// Group by
const ordersByStatus = await prisma.order.groupBy({
  by: ['status'],
  _count: true,
  _sum: { amount: true },
});
```

## Prisma Transactions

### Interactive Transactions

```typescript
// Multi-operation transaction
await prisma.$transaction(async (tx) => {
  await tx.account.update({
    where: { id: fromAccountId },
    data: { balance: { decrement: amount } },
  });

  await tx.account.update({
    where: { id: toAccountId },
    data: { balance: { increment: amount } },
  });
});
```

### Batch Transactions

```typescript
// Sequential batch (all-or-nothing)
const [user, profile] = await prisma.$transaction([
  prisma.user.create({ data: { email } }),
  prisma.profile.create({ data: { userId: '...' } }),
]);
```

### Transaction Options

```typescript
// Configuring timeout and isolation level
await prisma.$transaction(
  async (tx) => {
    // ... operations
  },
  {
    maxWait: 5000,  // Max wait for transaction slot (ms)
    timeout: 10000, // Max transaction duration (ms)
    isolationLevel: 'Serializable', // ReadCommitted | RepeatableRead | Serializable
  }
);
```

## Prisma Performance

### Avoiding N+1 Queries

```typescript
// Bad - N+1
const users = await prisma.user.findMany();
for (const user of users) {
  const orders = await prisma.order.findMany({
    where: { userId: user.id },
  });
}

// Good - include
const users = await prisma.user.findMany({
  include: { orders: true },
});

// Good - separate query with in filter
const users = await prisma.user.findMany();
const userIds = users.map(u => u.id);
const orders = await prisma.order.findMany({
  where: { userId: { in: userIds } },
});
```

### Raw Queries for Complex Operations

```typescript
// Use $queryRaw for complex queries Prisma Client can't express
const result = await prisma.$queryRaw`
  SELECT u.id, u.email, COUNT(o.id) as order_count
  FROM users u
  LEFT JOIN orders o ON o.user_id = u.id
  GROUP BY u.id
  HAVING COUNT(o.id) > ${minOrders}
`;

// Use $executeRaw for mutations
const affected = await prisma.$executeRaw`
  UPDATE orders
  SET status = 'CANCELLED'
  WHERE created_at < ${cutoffDate}
  AND status = 'PENDING'
`;
```

### Schema-Level Indexes

```prisma
model Order {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  status    OrderStatus
  createdAt DateTime @default(now()) @map("created_at")

  user User @relation(fields: [userId], references: [id])

  // Foreign key index
  @@index([userId])
  // Composite index for common queries
  @@index([userId, status])
  // Sort index
  @@index([createdAt(sort: Desc)])
  @@map("orders")
}
```

### Connection Management

```typescript
// Singleton pattern for Prisma Client
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development'
      ? ['query', 'error', 'warn']
      : ['error'],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}
```

## Additional References

- [Database Patterns](references/database-patterns.md) -- Generic SQL patterns: raw schema design, queries, transactions, indexes, and gotchas
- [Migrations](references/migrations.md) -- Migration structure, safe practices, and data migrations
- [Connection, Performance & Security](references/connection-performance-security.md) -- Connection pooling, query optimization, and database security
