# Class & Type Naming

## Classes

```typescript
// Noun or noun phrase
class UserService { }
class OrderRepository { }
class EmailNotificationSender { }
class DatabaseConnectionPool { }

// Avoid redundant suffixes when context is clear
class User { }  // Not UserModel, UserClass
class Order { } // Not OrderEntity

// Use suffix for infrastructure
class UserController { }
class OrderService { }
class PaymentGateway { }
```

## Interfaces

```typescript
// Describe what it is, not what it does (usually)
interface User { }
interface OrderItem { }
interface ApiResponse<T> { }

// Props interfaces for components
interface UserProfileProps { }
interface ButtonProps { }

// Don't prefix with I
interface User { }      // Good
interface IUser { }     // Bad (Hungarian notation)
```

## Type Aliases

```typescript
// Describe the concept
type UserId = string;
type Timestamp = number;
type Status = 'pending' | 'active' | 'completed';

// Function types describe the action
type CreateUser = (data: UserData) => User;
type ValidateEmail = (email: string) => boolean;
type EventHandler<T> = (event: T) => void;
```

## React/Vue Components

```typescript
// Component names: PascalCase, descriptive
function UserProfileCard({ user }: Props) { }
function OrderSummaryTable({ orders }: Props) { }
function NavigationSidebar() { }
```
