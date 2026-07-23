# Pack AA event-bundle validation

Verdict: `PASS`

Pack A SHA-256: `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`
Pack AA release-candidate SHA-256: `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`

Independent checks: schema and sequential event indices; 100 production IDs × 10 replicas; 1,000 records; 2,000 h2 observations; finite vertices; positive proper times and lengths; input weights; AA4 exponential proper-length closure; AA5 BR closure; AA6 sigma/hard-process/h2 preservation.

| configurations | unique production/config | trials/config | replicas/input | h2 observations/config | AA4 | AA5 | AA6 |
|---:|---:|---:|---:|---:|---|---|---|
| 9 | 100 | 1000 | 10 | 2000 | PASS | PASS | PASS |
