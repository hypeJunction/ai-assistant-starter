# Naming Gotchas

## Anti-Patterns

```typescript
// Single-letter variables (except in short lambdas)
const n = users.length;  // Bad
const count = users.length;  // Good

// Short lambdas are OK
users.filter(u => u.active);  // OK
users.filter(user => user.active);  // Also OK

// Numbered names
const user1 = getUser();
const user2 = getAdmin();
// Better:
const regularUser = getUser();
const adminUser = getAdmin();

// Type in name (Hungarian notation)
const strName = 'John';     // Bad
const arrUsers = [];        // Bad
const objConfig = {};       // Bad
const name = 'John';        // Good
const users = [];           // Good
const config = {};          // Good

// Negated booleans
const isNotActive = false;  // Bad - double negative in conditions
const isActive = true;      // Good

// Vague names
const data = fetch();       // Bad - what data?
const info = getInfo();     // Bad - what info?
const temp = calculate();   // Bad - temporary what?
```

## Reserved Words

```typescript
// Avoid JavaScript reserved words
const class = 'user';    // Error
const className = 'user'; // OK

const new = createItem(); // Error
const newItem = createItem(); // OK
```

## Shadowing

```typescript
// Avoid shadowing outer scope variables
const user = getCurrentUser();

function processOrder(order: Order) {
  const user = order.user;  // Shadows outer user
  // Confusing: which user?
}

// Better: be specific
function processOrder(order: Order) {
  const orderUser = order.user;
  // Clear distinction
}
```

## Consistency in Codebase

```typescript
// Pick one and stick to it
fetchUsers() vs getUsers()      // Pick one style
userId vs user_id vs userID     // Pick one format
onClick vs handleClick          // Pick one pattern
```
