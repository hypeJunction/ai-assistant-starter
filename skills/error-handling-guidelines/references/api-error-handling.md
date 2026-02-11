# API Error Handling

Reference patterns for server-side and client-side API error handling, plus user-facing message mapping, extracted from the error handling guidelines.

## Express/Node.js

```typescript
// Error handling middleware (must be last)
app.use((error: Error, req: Request, res: Response, next: NextFunction) => {
  // Log error
  logger.error('Request failed', {
    error: error.message,
    stack: error.stack,
    path: req.path,
    method: req.method,
  });

  // Determine response
  if (error instanceof AppError) {
    return res.status(error.statusCode).json({
      error: {
        code: error.code,
        message: error.message,
      }
    });
  }

  // Unknown error - don't expose details
  return res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    }
  });
});

// Async handler wrapper
const asyncHandler = (fn: RequestHandler): RequestHandler => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Usage
app.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  if (!user) {
    throw new NotFoundError('User', req.params.id);
  }
  res.json({ data: user });
}));
```

## Client-Side API Errors

```typescript
// API client error handling
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.error?.message || `HTTP ${response.status}`,
        errorData.error?.code || 'API_ERROR',
        response.status
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network error or other failure
    throw new ApiError(
      'Network request failed',
      'NETWORK_ERROR',
      0
    );
  }
}
```

## User-Facing Error Messages

### Message Mapping

```typescript
// Technical error codes to user messages
const userMessages: Record<string, string> = {
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNAUTHORIZED: 'Please sign in to continue.',
  FORBIDDEN: 'You don\'t have permission to perform this action.',
  NOT_FOUND: 'The requested item could not be found.',
  CONFLICT: 'This action conflicts with existing data.',
  RATE_LIMIT: 'Too many requests. Please wait a moment.',
  NETWORK_ERROR: 'Connection failed. Please check your internet.',
  INTERNAL_ERROR: 'Something went wrong. Please try again later.',
};

export function getUserMessage(error: unknown): string {
  if (error instanceof AppError) {
    return userMessages[error.code] || userMessages.INTERNAL_ERROR;
  }
  return userMessages.INTERNAL_ERROR;
}
```

### Form Validation Errors

```typescript
// Display field-level errors
function renderFieldError(errors: ValidationError['fields'], fieldName: string): string | undefined {
  const fieldError = errors.find(e => e.field === fieldName);
  return fieldError?.message;
}

// Usage in form
<input name="email" />
{errors.email && <span className="error">{errors.email}</span>}
```
