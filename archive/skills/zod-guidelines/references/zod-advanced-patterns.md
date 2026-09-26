# Zod Advanced Patterns

Reference for advanced Zod patterns including refinements, error handling, sanitization, and complex validation.

## Custom Validators

### Custom Refinements

```typescript
// Simple refinement
const positiveNumber = z.number().refine(
  n => n > 0,
  { message: 'Must be positive' }
);

// With context
const dateRange = z.object({
  startDate: z.date(),
  endDate: z.date(),
}).refine(
  data => data.endDate > data.startDate,
  {
    message: 'End date must be after start date',
    path: ['endDate'],
  }
);

// Async refinement
const uniqueUsername = z.string().refine(
  async (username) => {
    const exists = await db.users.findUnique({ where: { username } });
    return !exists;
  },
  { message: 'Username already taken' }
);
```

### Custom Error Messages

```typescript
const userSchema = z.object({
  name: z.string({
    required_error: 'Name is required',
    invalid_type_error: 'Name must be a string',
  }).min(1, 'Name cannot be empty').max(100, 'Name is too long'),

  age: z.number({
    required_error: 'Age is required',
    invalid_type_error: 'Age must be a number',
  }).int('Age must be a whole number').positive('Age must be positive'),
});
```

## Error Handling

### Formatting Errors

```typescript
import { z } from 'zod';

function formatZodErrors(error: z.ZodError) {
  return error.errors.map(e => ({
    field: e.path.join('.'),
    message: e.message,
    code: e.code,
  }));
}

// API response format
function handleValidationError(error: z.ZodError) {
  return {
    error: {
      code: 'VALIDATION_ERROR',
      message: 'Validation failed',
      details: formatZodErrors(error),
    },
  };
}

// Example output
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "email", "message": "Invalid email", "code": "invalid_string" },
      { "field": "age", "message": "Expected number, received string", "code": "invalid_type" }
    ]
  }
}
```

### Error Map Customization

```typescript
const customErrorMap: z.ZodErrorMap = (issue, ctx) => {
  if (issue.code === z.ZodIssueCode.invalid_type) {
    if (issue.expected === 'string') {
      return { message: 'This field must be text' };
    }
    if (issue.expected === 'number') {
      return { message: 'This field must be a number' };
    }
  }
  return { message: ctx.defaultError };
};

z.setErrorMap(customErrorMap);
```

## Sanitization

### Input Sanitization

```typescript
// Trim and normalize strings
const cleanString = z.string()
  .trim()
  .transform(s => s.replace(/\s+/g, ' '));  // Normalize whitespace

// Lowercase email
const email = z.string()
  .email()
  .toLowerCase()
  .trim();

// Remove HTML
import DOMPurify from 'dompurify';

const safeHtml = z.string().transform(s =>
  DOMPurify.sanitize(s, { ALLOWED_TAGS: [] })
);

// Limit length
const limitedString = z.string()
  .max(1000)
  .transform(s => s.slice(0, 1000));
```

### Type Coercion

```typescript
// From query strings/form data
const querySchema = z.object({
  page: z.coerce.number().default(1),
  active: z.string()
    .transform(s => s === 'true')
    .pipe(z.boolean()),
  ids: z.string()
    .transform(s => s.split(','))
    .pipe(z.array(z.string().uuid())),
});

// Parse: ?page=2&active=true&ids=uuid1,uuid2
// Result: { page: 2, active: true, ids: ['uuid1', 'uuid2'] }
```

## Complex Validation

### Discriminated Unions

```typescript
const eventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('click'),
    x: z.number(),
    y: z.number(),
  }),
  z.object({
    type: z.literal('keypress'),
    key: z.string(),
    modifiers: z.array(z.enum(['ctrl', 'alt', 'shift'])),
  }),
  z.object({
    type: z.literal('scroll'),
    direction: z.enum(['up', 'down']),
    amount: z.number(),
  }),
]);

type Event = z.infer<typeof eventSchema>;
```

### Recursive Schemas

```typescript
// Tree structure
interface Category {
  id: string;
  name: string;
  children: Category[];
}

const categorySchema: z.ZodType<Category> = z.lazy(() =>
  z.object({
    id: z.string().uuid(),
    name: z.string(),
    children: z.array(categorySchema),
  })
);
```

### Cross-Field Validation

```typescript
const orderSchema = z.object({
  items: z.array(z.object({
    productId: z.string(),
    quantity: z.number().positive(),
    price: z.number().positive(),
  })).min(1, 'Order must have at least one item'),

  discount: z.number().min(0).max(100).optional(),
  total: z.number().positive(),
}).refine(
  data => {
    const subtotal = data.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const discountAmount = subtotal * (data.discount || 0) / 100;
    const expectedTotal = subtotal - discountAmount;
    return Math.abs(data.total - expectedTotal) < 0.01;
  },
  { message: 'Total does not match calculated value' }
);
```
