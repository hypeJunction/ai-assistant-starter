---
name: performance-guidelines
description: Performance guidelines for TypeScript including frontend optimization, backend query optimization, caching, memory management, and profiling. Auto-loaded when working on performance-sensitive code.
user-invocable: false
---

# Performance Guidelines

## Core Principles

1. **Measure first** - Don't optimize without profiling
2. **Optimize bottlenecks** - Focus on hot paths
3. **Consider tradeoffs** - Performance vs. readability/maintainability
4. **Set budgets** - Define acceptable thresholds
5. **Monitor continuously** - Performance degrades over time

## Performance Budgets

### Define Thresholds

```typescript
// Performance budgets
const PERFORMANCE_BUDGETS = {
  // Page load
  firstContentfulPaint: 1500,    // ms
  largestContentfulPaint: 2500,  // ms
  timeToInteractive: 3500,       // ms

  // Bundle size
  mainBundle: 200,     // KB (gzipped)
  chunkSize: 50,       // KB (gzipped)
  totalSize: 500,      // KB (gzipped)

  // API response
  apiResponse: 200,    // ms (p95)
  dbQuery: 50,         // ms (p95)

  // Runtime
  frameRate: 60,       // fps
  inputLatency: 100,   // ms
};
```

## Frontend Performance

### Bundle Optimization

```typescript
// Dynamic imports for code splitting
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// Use in component
<Suspense fallback={<Loading />}>
  <HeavyComponent />
</Suspense>

// Route-based splitting
const routes = [
  {
    path: '/dashboard',
    component: lazy(() => import('./pages/Dashboard')),
  },
  {
    path: '/settings',
    component: lazy(() => import('./pages/Settings')),
  },
];
```

### Memoization

```typescript
// React: Memoize expensive computations
const expensiveResult = useMemo(() => {
  return items.filter(complexFilter).sort(complexSort);
}, [items]);

// React: Memoize callbacks
const handleClick = useCallback((id: string) => {
  setSelected(id);
}, []);

// React: Memoize components
const MemoizedComponent = memo(function Component({ data }: Props) {
  return <div>{data.name}</div>;
});

// Vue: Computed properties are automatically cached
const filteredItems = computed(() => {
  return items.value.filter(complexFilter).sort(complexSort);
});
```

## Backend Performance

### Database Query Optimization

```typescript
// Avoid N+1 queries
// Bad - N+1 problem
const users = await db.users.findMany();
for (const user of users) {
  user.orders = await db.orders.findMany({ where: { userId: user.id } });
}

// Good - eager loading
const users = await db.users.findMany({
  include: { orders: true },
});

// Good - batch loading
const users = await db.users.findMany();
const userIds = users.map(u => u.id);
const orders = await db.orders.findMany({
  where: { userId: { in: userIds } },
});
```

### Pagination

```typescript
// Always paginate large datasets
async function getUsers(page: number, limit: number = 20) {
  const offset = (page - 1) * limit;

  const [users, total] = await Promise.all([
    db.users.findMany({
      skip: offset,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    db.users.count(),
  ]);

  return {
    data: users,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
}

// For very large datasets, use cursor-based pagination
async function getUsersCursor(cursor?: string, limit: number = 20) {
  const users = await db.users.findMany({
    take: limit + 1, // Fetch one extra to check for more
    cursor: cursor ? { id: cursor } : undefined,
    skip: cursor ? 1 : 0,
    orderBy: { id: 'asc' },
  });

  const hasMore = users.length > limit;
  const items = hasMore ? users.slice(0, -1) : users;

  return {
    data: items,
    nextCursor: hasMore ? items[items.length - 1].id : null,
  };
}
```

## Common Anti-Patterns

### Avoid These

```typescript
// Bad - unnecessary re-renders
function Component({ items }) {
  // Creates new function on every render
  return items.map(item => (
    <Item key={item.id} onClick={() => handleClick(item.id)} />
  ));
}

// Good - stable callback
function Component({ items }) {
  const handleItemClick = useCallback((id: string) => {
    handleClick(id);
  }, []);

  return items.map(item => (
    <Item key={item.id} onClick={handleItemClick} id={item.id} />
  ));
}

// Bad - blocking the main thread
const result = heavyComputation(largeData);

// Good - use Web Workers for heavy computation
const worker = new Worker('./heavy-worker.js');
worker.postMessage(largeData);
worker.onmessage = (e) => setResult(e.data);

// Bad - synchronous I/O in Node.js
const data = fs.readFileSync('file.json');

// Good - async I/O
const data = await fs.promises.readFile('file.json');
```

## Known Gotchas

### Premature Optimization

```typescript
// Don't optimize without measuring
// Most code is not performance-critical

// Measure first:
// 1. Profile in production-like conditions
// 2. Identify actual bottlenecks
// 3. Set measurable goals
// 4. Optimize and verify improvement
```

### Hidden Costs

```typescript
// JSON.parse/stringify are expensive
const copy = JSON.parse(JSON.stringify(obj));  // Slow
const copy = structuredClone(obj);             // Better

// Array methods create new arrays
const result = arr.filter(...).map(...).reduce(...);  // 3 iterations
// Consider single loop if performance-critical
```

### Browser Reflows

```typescript
// Bad - triggers reflow for each read
elements.forEach(el => {
  const height = el.offsetHeight;  // Triggers reflow
  el.style.height = `${height + 10}px`;  // Triggers reflow
});

// Good - batch reads, then writes
const heights = elements.map(el => el.offsetHeight);  // Single reflow
elements.forEach((el, i) => {
  el.style.height = `${heights[i] + 10}px`;
});
```

## Additional References

- [Frontend Performance](references/frontend-performance.md) — Image optimization, virtualization, debounce/throttle
- [Backend Performance](references/backend-performance.md) — Caching strategies, connection pooling, async processing
- [Profiling & Memory](references/profiling-memory.md) — Memory leak prevention, streaming, frontend/backend profiling
