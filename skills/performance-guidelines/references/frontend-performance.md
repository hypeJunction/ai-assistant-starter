Additional frontend performance techniques covering image optimization, list virtualization, and input event management.

### Image Optimization

```typescript
// Use responsive images
<picture>
  <source media="(max-width: 768px)" srcset="image-small.webp" />
  <source media="(max-width: 1200px)" srcset="image-medium.webp" />
  <img src="image-large.webp" alt="Description" loading="lazy" />
</picture>

// Lazy load images
<img src="image.jpg" loading="lazy" decoding="async" alt="Description" />

// Use modern formats with fallback
<picture>
  <source srcset="image.avif" type="image/avif" />
  <source srcset="image.webp" type="image/webp" />
  <img src="image.jpg" alt="Description" />
</picture>
```

### Virtualization for Long Lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            {items[virtualRow.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Debounce and Throttle

```typescript
import { debounce, throttle } from 'lodash-es';

// Debounce: Wait for pause in events (search input)
const debouncedSearch = debounce((query: string) => {
  fetchSearchResults(query);
}, 300);

// Throttle: Limit event frequency (scroll, resize)
const throttledScroll = throttle(() => {
  updateScrollPosition();
}, 100);

// Cleanup on unmount
useEffect(() => {
  window.addEventListener('scroll', throttledScroll);
  return () => {
    window.removeEventListener('scroll', throttledScroll);
    throttledScroll.cancel();
  };
}, []);
```
