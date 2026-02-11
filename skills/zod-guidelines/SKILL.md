---
name: zod-guidelines
description: Data validation guidelines using Zod including schemas, API request validation, form validation, and error handling. Auto-loaded when working with validation code.
user-invocable: false
---

# Data Validation Guidelines

## Core Principles

1. **Validate at boundaries** - API endpoints, form submissions, external data
2. **Fail fast** - Reject invalid data immediately
3. **Be specific** - Clear error messages for each validation failure
4. **Type safety** - Schema validation provides runtime types
5. **Defense in depth** - Client and server validation

## Schema Validation with Zod

### Basic Schemas

```typescript
import { z } from 'zod';

// Primitive types
const stringSchema = z.string();
const numberSchema = z.number();
const booleanSchema = z.boolean();
const dateSchema = z.date();

// With constraints
const emailSchema = z.string().email();
const positiveNumber = z.number().positive();
const nonEmptyString = z.string().min(1);

// Object schema
const userSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
  role: z.enum(['admin', 'user', 'guest']),
  createdAt: z.date(),
});

// Infer TypeScript type
type User = z.infer<typeof userSchema>;
```

### Common Patterns

```typescript
// Optional with default
const configSchema = z.object({
  port: z.number().default(3000),
  debug: z.boolean().default(false),
});

// Nullable vs Optional
const schema = z.object({
  optional: z.string().optional(),      // string | undefined
  nullable: z.string().nullable(),      // string | null
  both: z.string().nullish(),           // string | null | undefined
});

// Transform data
const trimmedString = z.string().trim();
const lowercaseEmail = z.string().email().toLowerCase();
const parsedDate = z.string().transform(s => new Date(s));

// Coercion (parse from string)
const coercedNumber = z.coerce.number();  // "123" -> 123
const coercedBoolean = z.coerce.boolean(); // "true" -> true
const coercedDate = z.coerce.date();       // "2024-01-15" -> Date
```

### Validation and Parsing

```typescript
// Parse (throws on error)
try {
  const user = userSchema.parse(input);
  // user is typed as User
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error(error.errors);
  }
}

// Safe parse (returns result object)
const result = userSchema.safeParse(input);
if (result.success) {
  const user = result.data;  // Typed as User
} else {
  const errors = result.error.errors;
}

// Partial validation (all fields optional)
const partialUser = userSchema.partial();

// Pick specific fields
const nameOnly = userSchema.pick({ name: true, email: true });

// Omit fields
const withoutId = userSchema.omit({ id: true });
```

## API Request Validation

### Express Middleware

```typescript
import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';

// Validation middleware factory
function validate<T extends z.ZodSchema>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse({
      body: req.body,
      query: req.query,
      params: req.params,
    });

    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          details: result.error.errors.map(e => ({
            path: e.path.join('.'),
            message: e.message,
          })),
        },
      });
    }

    req.validated = result.data;
    next();
  };
}

// Usage
const createUserSchema = z.object({
  body: z.object({
    name: z.string().min(1),
    email: z.string().email(),
  }),
});

app.post('/users', validate(createUserSchema), (req, res) => {
  const { name, email } = req.validated.body;
  // ... create user
});
```

### Request Schema Patterns

```typescript
// GET with query params
const listUsersSchema = z.object({
  query: z.object({
    page: z.coerce.number().min(1).default(1),
    limit: z.coerce.number().min(1).max(100).default(20),
    search: z.string().optional(),
    status: z.enum(['active', 'inactive']).optional(),
  }),
});

// GET with path params
const getUserSchema = z.object({
  params: z.object({
    id: z.string().uuid(),
  }),
});

// POST/PUT with body
const updateUserSchema = z.object({
  params: z.object({
    id: z.string().uuid(),
  }),
  body: z.object({
    name: z.string().min(1).max(100).optional(),
    email: z.string().email().optional(),
  }).refine(
    data => Object.keys(data).length > 0,
    { message: 'At least one field must be provided' }
  ),
});
```

## Custom Validators

### Reusable Validators

```typescript
// Custom validator factories
const stringId = () => z.string().uuid();
const pagination = () => z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
});

const dateString = () => z.string().refine(
  s => !isNaN(Date.parse(s)),
  { message: 'Invalid date format' }
).transform(s => new Date(s));

// Use in schemas
const listSchema = z.object({
  query: pagination(),
});
```

## Known Gotchas

### Coercion Behavior

```typescript
// z.coerce.number() behavior
z.coerce.number().parse('');     // NaN (might want to handle)
z.coerce.number().parse('abc');  // NaN
z.coerce.number().parse(null);   // 0

// Safer: check for NaN
const safeNumber = z.coerce.number().refine(
  n => !Number.isNaN(n),
  { message: 'Invalid number' }
);
```

### Optional vs Nullable

```typescript
// Optional: field can be omitted
z.string().optional()  // string | undefined

// Nullable: field can be null
z.string().nullable()  // string | null

// Both:
z.string().nullish()   // string | null | undefined

// Default only works for undefined
z.string().optional().default('hello')  // Works
z.string().nullable().default('hello')  // null stays null!
```

### Parse vs SafeParse

```typescript
// parse() throws - use in trusted contexts
const data = schema.parse(trustedInput);

// safeParse() returns result - use for user input
const result = schema.safeParse(userInput);
if (!result.success) {
  // Handle errors
}
```

## Additional References

- [Form Validation](references/zod-form-validation.md) - Client-side form validation with React Hook Form and field-level validation
- [Advanced Patterns](references/zod-advanced-patterns.md) - Refinements, error handling, sanitization, and complex validation patterns
