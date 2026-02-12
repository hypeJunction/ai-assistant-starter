# Variable Naming

## Be Descriptive

```typescript
// Bad - unclear
const d = new Date();
const u = getUser();
const arr = items.filter(x => x.active);

// Good - descriptive
const currentDate = new Date();
const currentUser = getUser();
const activeItems = items.filter(item => item.active);
```

## Avoid Abbreviations

```typescript
// Bad - requires mental translation
const usrMgr = new UserManager();
const errMsg = 'Invalid input';
const txn = createTransaction();
const cfg = loadConfig();

// Good - full words
const userManager = new UserManager();
const errorMessage = 'Invalid input';
const transaction = createTransaction();
const config = loadConfig();

// Acceptable abbreviations (universally understood)
const id = user.id;       // identifier
const url = '/api/users'; // uniform resource locator
const api = new Api();    // application programming interface
const html = render();    // hypertext markup language
const css = styles();     // cascading style sheets
const db = database;      // database (in context)
```

## Use Pronounceable Names

```typescript
// Bad - hard to discuss
const yyyymmdd = formatDate();
const cstmrLst = getCustomers();
const genymdhms = generateTimestamp();

// Good - can be spoken
const dateString = formatDate();
const customerList = getCustomers();
const timestamp = generateTimestamp();
```

## Booleans

```typescript
// Prefix with is, has, can, should, will
const isActive = true;
const hasPermission = user.role === 'admin';
const canEdit = isOwner || hasPermission;
const shouldRender = isVisible && hasData;
const willRedirect = authRequired && !isAuthenticated;

// Bad - unclear boolean intent
const active = true;
const permission = checkPermission();
const edit = true;
const render = checkVisibility();
```

## Collections

```typescript
// Plural names for arrays/collections
const users = await fetchUsers();
const orderItems = order.items;
const selectedIds = new Set<string>();

// Bad - singular for collections
const user = await fetchUsers();  // Misleading!
const orderItem = order.items;
```

## Numbers

```typescript
// Include unit or context when relevant
const timeoutMs = 5000;
const maxRetries = 3;
const itemCount = items.length;
const priceInCents = 999;
const temperatureCelsius = 22.5;

// Bad - unit unclear
const timeout = 5000;  // Seconds? Milliseconds?
const price = 999;     // Dollars? Cents?
```

## Strings

```typescript
// Indicate type when not obvious
const userId = '550e8400-e29b-41d4-a716-446655440000';
const userEmail = 'user@example.com';
const dateString = '2024-01-15';
const jsonPayload = JSON.stringify(data);
const htmlContent = '<div>Hello</div>';
```
