# Function Naming

## Naming Patterns

```typescript
// Actions: verb + noun
function createUser(data: UserData): User { }
function updateOrder(id: string, changes: OrderChanges): Order { }
function deleteComment(id: string): void { }
function sendEmail(to: string, subject: string): void { }

// Getters: get + noun (for computed/fetched)
function getUserById(id: string): User | undefined { }
function getActiveOrders(): Order[] { }
function getCurrentUser(): User { }

// Checkers: is/has/can + adjective/noun
function isValidEmail(email: string): boolean { }
function hasPermission(user: User, action: string): boolean { }
function canAccessResource(user: User, resource: Resource): boolean { }

// Transformers: noun + to + noun, or verb
function userToDto(user: User): UserDto { }
function formatDate(date: Date): string { }
function parseConfig(raw: string): Config { }

// Event handlers: handle + event or on + event
function handleClick(event: MouseEvent): void { }
function handleSubmit(data: FormData): void { }
const onClick = () => { };
const onUserCreate = (user: User) => { };
```

## Avoid Generic Names

```typescript
// Bad - too generic
function process(data: unknown) { }
function handle(item: Item) { }
function doStuff() { }
function getData() { }
function manage(entity: Entity) { }

// Good - specific
function validateUserInput(input: unknown) { }
function applyDiscount(item: CartItem) { }
function sendWelcomeEmail() { }
function fetchOrderHistory() { }
function archiveInactiveUsers() { }
```

## React/Vue Event Handlers

```typescript
// Component props
interface ButtonProps {
  onClick?: () => void;
  onHover?: () => void;
  onFocus?: () => void;
}

// Handler functions
const handleClick = () => { };
const handleFormSubmit = (data: FormData) => { };
const handleUserSelect = (user: User) => { };
```

## React/Vue Hooks

```typescript
// Hooks: use + description
function useLocalStorage<T>(key: string): [T, (value: T) => void] { }
function useDebounce<T>(value: T, delay: number): T { }
function useCurrentUser(): User | null { }
```
