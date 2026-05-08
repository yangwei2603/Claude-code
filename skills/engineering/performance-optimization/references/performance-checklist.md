# Performance Checklist

Reference file for performance-optimization, code-review-and-quality, and shipping-and-launch skills.

## Core Web Vitals Thresholds

| Metric | Good | Needs Work | Poor |
|--------|------|------------|------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## Frontend Performance

### Bundle Optimization
- [ ] Code-split by route (lazy load non-critical pages)
- [ ] Tree-shaking enabled (no dead code in bundle)
- [ ] Dynamic imports for heavy dependencies (charts, rich text editors)
- [ ] Preload critical fonts and hero images
- [ ] Bundle size < 200KB gzipped for initial load (target)

### Image & Media
- [ ] Images in next-gen formats (WebP/AVIF > JPEG/PNG)
- [ ] Responsive images with `srcset` and correct `sizes`
- [ ] Lazy loading for below-fold images (`loading="lazy"`)
- [ ] Explicit `width` and `height` on all images (prevents CLS)
- [ ] Video posters and lazy video loading
- [ ] Icons use SVG or icon font (not full image sprites)

### Rendering
- [ ] Critical CSS inlined in `<head>`
- [ ] Non-critical CSS loaded with `media="print" onload="this.media='all'"`
- [ ] No render-blocking scripts (defer/async or dynamic import)
- [ ] `content-visibility: auto` for long off-screen lists
- [ ] Virtual scrolling for lists > 100 items

### Network
- [ ] CDN used for static assets
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] Resource hints: `preconnect`, `dns-prefetch`, `preload`
- [ ] Compression enabled (Brotli > Gzip)
- [ ] Service worker for caching repeat visits
- [ ] API responses use gzip/brotli compression

## Backend Performance

### Database
- [ ] Indexes on all foreign keys and filter columns
- [ ] Slow query log reviewed (queries > 100ms flagged)
- [ ] No N+1 queries (use `JOIN`/`include`/`eager_load`)
- [ ] Pagination on all list endpoints (no `SELECT *` without limits)
- [ ] Connection pooling configured (PgBouncer, RDS Proxy)
- [ ] Read replicas for read-heavy workloads

### Caching
- [ ] Expensive computations cached (Redis, Memcached)
- [ ] Cache invalidation strategy defined before implementing
- [ ] Cache key namespacing prevents collisions
- [ ] Cache TTLs are intentional (not just "1 hour")
- [ ] Stale-while-revalidate for non-critical data

### API
- [ ] Response times < 200ms p95 for simple reads
- [ ] Response times < 500ms p95 for complex operations
- [ ] Batch endpoints for bulk operations
- [ ] No blocking operations on the main thread
- [ ] Background jobs for slow operations (email, report generation)

### Resource Management
- [ ] Connection pool sizes tuned for expected load
- [ ] Memory limits set on all containers
- [ ] Auto-scaling configured with appropriate thresholds
- [ ] Rate limiting prevents resource exhaustion

## Common Anti-Patterns

### Backend
| Anti-Pattern | Symptom | Fix |
|---|---|---|
| N+1 queries | 1 query per item in list | `JOIN` or `include` |
| Full table scans | Slow queries on large tables | Add indexes, use EXPLAIN |
| Unbounded result sets | Memory spikes | Add pagination and limits |
| Synchronous heavy compute | Request timeouts | Move to background job |
| No connection pooling | Database connection errors under load | Configure pool size |
| Missing cache | Repeated expensive computation | Redis/Memcached with TTL |

### Frontend
| Anti-Pattern | Symptom | Fix |
|---|---|---|
| Large JS bundle | Slow initial load | Code-split, lazy load |
| Unoptimized images | High LCP | WebP, srcset, lazy load |
| Render-blocking resources | White screen delay | async/defer, inline critical CSS |
| Excessive re-renders | High JS thread usage | Memo, useMemo, useCallback |
| Memory leaks | Tab crashes over time | Cleanup subscriptions and timers |
| No virtualization | Slow scroll on long lists | Virtual scrolling (TanStack Virtual) |

## Profiling Tools

| Environment | Tool | What to Find |
|---|---|---|
| Chrome | DevTools Performance tab | Long tasks, forced reflows |
| Chrome | Lighthouse | Core Web Vitals scores |
| Chrome | Network tab | Waterfall, blocking time |
| Node.js | `clinic.js`, `0x` | CPU hotspots, memory leaks |
| Python | `cProfile`, `py-spy` | Slow function calls |
| PostgreSQL | `EXPLAIN ANALYZE` | Slow query plans |
| API | APM (Datadog/New Relic) | Distributed trace timelines |
| CDN | Provider dashboard | Cache hit ratios, origin load |

## Load Testing Checklist

- [ ] Baseline: establish performance under normal traffic
- [ ] Stress test: find breaking point
- [ ] Spike test: sudden traffic surge
- [ ] Soak test: sustained load reveals memory leaks
- [ ] p50, p95, p99 latency tracked (not just averages)
- [ ] Error rate tracked at each percentile
- [ ] Results documented and regression alerts configured

## Pre-Launch Performance Checklist

1. Run Lighthouse CI against all critical pages (score ≥ 90)
2. Load test at 2x expected peak traffic — p95 < SLO
3. Verify all database queries < 100ms (p95) under load
4. Confirm CDN cache hit ratio > 90% for static assets
5. Check no memory growth over 30-minute sustained load
6. Verify Core Web Vitals in field data (Chrome UX Report)
7. Confirm auto-scaling responds within 60 seconds
8. Review slow query log in production (no new slow queries)
