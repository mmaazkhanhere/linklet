# Linklet — Spec-Driven Development (SDD) Suite

Welcome to the **Linklet Specification Suite**. This directory contains detailed, executable feature specifications designed for **Spec-Driven Development (SDD)**.

The specs in this folder expand upon [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) to provide unambiguous, implementation-ready guidance, requirements, API contracts, data schemas, edge cases, and test acceptance criteria.

---

## Directory Index

| Spec File | Topic | Key Focus & Scope |
|-----------|-------|-------------------|
| [01-auth-user-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/01-auth-user-management.md) | Authentication & User Management | Registration, JWT auth, password hashing, identity context |
| [02-link-creation.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/02-link-creation.md) | Short Link Creation | `POST /links`, URL syntax validation, Base62 generator, collision retries |
| [03-redirect-resolution.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/03-redirect-resolution.md) | Public Redirect & Click Counter | `GET /{short_code}`, 302/307 redirects, atomic click increment, route isolation |
| [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) | Link Lifecycle Management | `GET /links`, `PUT /links/{id}` (regenerate), `DELETE /links/{id}`, ownership checks |
| [05-idempotency-engine.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/05-idempotency-engine.md) | Idempotency Engine | Scoped keys `(user_id, operation, key)`, request hashing, unified DB transactions |
| [06-database-schema-migrations.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/06-database-schema-migrations.md) | Database & Migrations | Relational tables (`users`, `links`, `idempotency_request`), indexes, constraints |

---

## Global REST Error Format & API Conventions

All API errors across all protected and public endpoints must adhere to a standardized JSON error format compatible with RFC 7807 problem details:

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation of the error.",
    "details": null
  }
}
```

### Standard HTTP Status Codes

| HTTP Status | Category | Usage in Linklet |
|-------------|----------|-------------------|
| `200 OK` | Success | Standard response for `GET /links`, `PUT /links/{id}`, `DELETE /links/{id}` |
| `201 Created` | Success | Returned on successful creation (`POST /links`, `POST /auth/register`) |
| `302 Found` / `307 Temporary` | Redirect | Returned on successful short code resolution (`GET /{short_code}`) |
| `400 Bad Request` | Client Error | Malformed JSON body, invalid URL syntax, or invalid idempotency key payload mismatch |
| `401 Unauthorized` | Client Error | Missing or invalid authentication token |
| `404 Not Found` | Client Error | Short code does not exist or user attempting to access/modify a link they do not own |
| `409 Conflict` | Client Error | Unique constraint violation (e.g. email address already registered) |
| `422 Unprocessable Entity` | Client Error | Validation errors on request fields (e.g. missing required field) |
| `429 Too Many Requests` | Client Error | Idempotency processing lock conflict (request already `PROCESSING`) |
| `500 Internal Server Error` | Server Error | Unhandled backend or database infrastructure failures |

---

## Architecture Traceability Matrix

This matrix maps every Requirement ID from [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) to its primary driving specification file:

| Requirement ID | Requirement Summary | Target Spec File |
|----------------|---------------------|------------------|
| **FR-01** | Create Short Link | [02-link-creation.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/02-link-creation.md) |
| **FR-02** | Public Redirect | [03-redirect-resolution.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/03-redirect-resolution.md) |
| **FR-03** | List Own Links | [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **FR-04** | Click Count Increment | [03-redirect-resolution.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/03-redirect-resolution.md) |
| **FR-05** | Delete Link & Invalidate | [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **FR-06** | Regenerate Short Code | [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **FR-07** | Ownership Isolation | [01-auth-user-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/01-auth-user-management.md), [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **FR-08** | Absolute URL Validation | [02-link-creation.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/02-link-creation.md) |
| **FR-09** | Short Code Uniqueness | [02-link-creation.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/02-link-creation.md), [06-database-schema-migrations.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/06-database-schema-migrations.md) |
| **FR-10** | Mutation Idempotency | [05-idempotency-engine.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/05-idempotency-engine.md) |
| **FR-11** | Idempotency Key Misuse | [05-idempotency-engine.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/05-idempotency-engine.md) |
| **FR-12** | Mapping Durability | [06-database-schema-migrations.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/06-database-schema-migrations.md) |
| **NFR-01** | Latency (<500ms p95) | [03-redirect-resolution.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/03-redirect-resolution.md) |
| **NFR-03** | Immediate Delete Invalidation | [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **NFR-04** | Atomic Short Code Replacement | [04-link-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/04-link-management.md) |
| **NFR-05** | Core Data Invariants | [06-database-schema-migrations.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/06-database-schema-migrations.md) |
| **NFR-06** | Passwords & Server Authorization | [01-auth-user-management.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/specs/01-auth-user-management.md) |
| **NFR-07** | Modular Monolith Code Boundaries | All specs |

---

## Spec-Driven Development Workflow

1. **Pick a Spec**: Select a feature specification file (e.g. `02-link-creation.md`).
2. **Review Functional Scope & Schemas**: Examine the endpoint signatures, input/output schemas, and error definitions.
3. **Implement Unit & Integration Tests**: Write automated tests reflecting the acceptance criteria in the spec before or alongside implementation.
4. **Build Code against Invariants**: Follow the exact component responsibilities and edge case behavior detailed in the spec.
5. **Verify against Criteria**: Run test suites to ensure 100% compliance with spec invariants.
