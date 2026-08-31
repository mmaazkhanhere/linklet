# Specification 03: Public Redirect & Click Counter Resolution

- **Spec ID**: `SPEC-03`
- **Component**: Link Service & Redirect Router
- **Traceability**: [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) — FR-02, FR-04, NFR-01, Section 12.2
- **Status**: Ready for Implementation

---

## 1. Overview & Objective

The Public Redirect module resolves an active 7-character `short_code` to its underlying `destination_url` and redirects visitors. It increments the logical link's cumulative `total_clicks` counter atomically without lost updates and isolates system root routes (`/health`, `/links`, `/auth`) from short code parameter space.

---

## 2. API Endpoint Specification

### `GET /{short_code}`

Resolves an active short code and redirects the client to the stored destination URL.

- **Authentication**: None (Public Endpoint)
- **Path Parameter**: `short_code` (String, 7 Base62 characters)
- **Success Response**: `307 Temporary Redirect` or `302 Found`
  - **Headers**: `Location: <destination_url>`
  - **Body**: Empty

### Error Response (`404 Not Found`)
Returned if `short_code` does not exist in `links` table or has been hard-deleted:
```json
{
  "error": {
    "code": "LINK_NOT_FOUND",
    "message": "The requested short link does not exist or has been removed.",
    "details": null
  }
}
```

---

## 3. Atomic Click Counter Increment (FR-04)

To prevent lost updates under concurrent redirect traffic without requiring heavy table locks:

1. Look up destination URL and increment total clicks in a single SQL operation:
   ```sql
   UPDATE links
   SET total_clicks = total_clicks + 1
   WHERE short_code = :short_code
   RETURNING destination_url;
   ```
2. Alternatively, execute atomic update within the resolution transaction:
   ```sql
   UPDATE links SET total_clicks = total_clicks + 1 WHERE id = :link_id;
   ```
3. **DO NOT** perform application read-modify-write (`link.total_clicks += 1` in Python state followed by `UPDATE links SET total_clicks = ...`), as concurrent requests will overwrite each other's increments.

---

## 4. Root Namespace & Reserved Route Isolation

Because the redirect endpoint resides at the root level (`GET /{short_code}`), the framework router MUST reserve system routes so they are never parsed as short codes.

### Reserved Route Registry
The following root paths MUST NOT be matched by the `/{short_code}` route:
- `/health` (Health check)
- `/docs` (Swagger UI)
- `/redoc` (ReDoc UI)
- `/openapi.json` (OpenAPI specification)
- `/auth/*` (Authentication endpoints)
- `/links/*` (Link management endpoints)
- `/metrics` (Prometheus operational metrics)

#### Implementation Mechanism:
Define system management routers (`/auth`, `/links`, `/health`) BEFORE mounting the catch-all `/{short_code}` router in FastAPI, or validate `short_code` against reserved words.

---

## 5. Performance & Latency Constraints (NFR-01)

- **Target**: 95% of redirect requests MUST complete within 500 ms under baseline workload (~3 QPS peak).
- **Execution Path**: Redirect handling MUST be direct and minimal: DB lookup + atomic counter update + return `Location` header. No external network calls are allowed on the redirect path.

---

## 6. Test & Acceptance Criteria

| ID | Scenario | Input / Action | Expected Result |
|----|----------|----------------|-----------------|
| `TC-REDIR-01` | Successful Redirect | Active `short_code` | `307 Temporary Redirect` / `302 Found`, `Location` header set to destination URL |
| `TC-REDIR-02` | Click Counter Incremented | Single redirect request | `total_clicks` in `links` table increases by exactly 1 |
| `TC-REDIR-03` | Non-Existent Code | Request `GET /nonexistent` | `404 Not Found`, code `LINK_NOT_FOUND` |
| `TC-REDIR-04` | Reserved Route Protection | Request `GET /health` | Resolved by health router, NOT treated as short code |
| `TC-REDIR-05` | Concurrent Redirects | 20 parallel requests to same `short_code` | All 20 requests succeed, `total_clicks` increases by exactly 20 |
| `TC-REDIR-06` | Unauthenticated Access | Redirect request with no Auth header | Redirect succeeds (public access) |
