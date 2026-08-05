# Performance After Upgrade

Measured locally on 5 August 2026 using the same Python runtime and Vite production build as the baseline.

| Metric | Before | After | Result |
|---|---:|---:|---:|
| Python import/startup | 6,082.84 ms | 2,567.94 ms | 57.8% faster |
| Warm health endpoint | 1,506.39 ms | 123.23 ms | 91.8% faster |
| Agent catalogue | not available | 10.09 ms | below 500 ms target |
| Single eager JavaScript asset | 610,943 B | removed | route split |
| Landing critical JavaScript assets | 610,943 B | approximately 193 KB raw | approximately 68% smaller |
| Command-centre application chunk | 610,943 B | 27,290 B plus shared runtime | split from charts |
| Deferred chart chunk | eager | 394,250 B | loaded after shell |
| Initial command-centre critical API calls | 5 | 2 | 60% fewer |
| Landing critical API calls | 5 | 0 | no backend dependency to paint |

The previous health endpoint performed an outbound simulator call and sandbox/provider discovery. `/health` is now process-local; `/readiness` retains dependency checks. Database schema creation moved to lifespan and legacy demo seeding is deferred. Evidence, audit, agents and charts load after the shell. TanStack Query uses a 30-second stale time and disables focus refetch.

FCP/LCP are not claimed because a controlled Lighthouse trace was not available in the local validation environment. Render free-tier wake-up latency remains an infrastructure limitation.

