# Error Boundaries (UI)

Reference patterns for React and Vue error boundaries, extracted from the error handling guidelines.

## React Error Boundary

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('React error boundary caught error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Usage
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>
```

## Vue Error Handler

```typescript
// Global error handler
app.config.errorHandler = (error, instance, info) => {
  logger.error('Vue error', {
    error: error instanceof Error ? error.message : error,
    component: instance?.$options.name,
    info,
  });
};

// Component-level
export default {
  errorCaptured(error: Error, instance: ComponentPublicInstance, info: string) {
    logger.error('Component error', { error: error.message, info });
    return false; // Don't propagate
  }
};
```
