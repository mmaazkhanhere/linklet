# URL Shortener App

## Architecture & Software Requirements Document

**MVP / Version 1.0**

| **Document Type**      | Combined Software Requirements Specification (SRS) and Software Architecture Document (SAD) |
|------------------------|---------------------------------------------------------------------------------------------|
| **Backend**            | Python + FastAPI                                                                            |
| **Architecture Style** | Modular monolith / single backend service                                                   |
| **Scale Baseline**     | 100 active creators; ~500 link creations/day; ~50,000 redirects/day                         |
| **Status**             | Architecture baseline approved for implementation planning                                  |

*Purpose: define the MVP product scope, system behavior, architecture, data model, operational assumptions, risks, and implementation boundaries for a production-reasonable learning project.*

# Document Contents

- 1\. Executive Summary

- 2\. Product Scope and Objectives

- 3\. Actors and System Boundary

- 4\. Functional Requirements

- 5\. Non-Functional Requirements

- 6\. Capacity and Scale Assumptions

- 7\. API and Use-Case Boundary

- 8\. Data Model and Persistence Design

- 9\. Idempotency Strategy

- 10\. High-Level Architecture (C4)

- 11\. Backend Component Architecture

- 12\. Runtime Flows

- 13\. Transaction and Consistency Requirements

- 14\. Failure, Bottleneck, and Risk Analysis

- 15\. Architecture Trade-offs and Evolution Triggers

- 16\. Security Requirements

- 17\. Observability and Operations

- 18\. Testing and Acceptance Criteria

- 19\. Implementation Constraints and Open Decisions

- 20\. MVP Definition of Done

# 1. Executive Summary

The URL Shortener MVP is a small authenticated link-management application with a public redirect path. Authenticated users can create, list, regenerate, and delete short links. Any visitor who possesses an active short link can open it without authentication and be redirected to its destination. The system records a cumulative click count for each logical link.

The MVP is intentionally designed for low scale and simplicity: one FastAPI backend, one durable relational database, no cache, no queue, no microservices, and no per-click analytics store. The architecture emphasizes correctness, ownership enforcement, idempotent mutations, durable mappings, immediate invalidation after delete/regenerate, and clear evolution triggers rather than premature distributed-system complexity.

| Architecture principle: requirements and measured/estimated load drive complexity. V1 capacity is small enough that raw throughput is not a primary architectural challenge. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

# 2. Product Scope and Objectives

## 2.1 Product Objective

Provide a simple, durable, authenticated URL shortening service that lets users manage their own short links while allowing anyone with an active short URL to follow the redirect.

## 2.2 In Scope

- Authenticated account usage for link management.

- Creation of a short link for a valid HTTP/HTTPS destination URL.

- Public redirection from an active short code to the destination URL.

- Listing the authenticated user's own links.

- Cumulative total-click counting for successful redirect requests.

- Deletion of a link with immediate invalidation after successful deletion.

- Regeneration of the current short code while preserving the logical link and cumulative click count.

- Request idempotency for CREATE, DELETE, and REGENERATE mutations.

- Durable link mappings with no automatic expiration.

## 2.3 Out of Scope for V1

- Custom aliases.

- Advanced malicious/phishing URL detection.

- Per-click event history, unique visitors, geography, devices, referrers, or time-series analytics.

- Soft-delete recovery or audit-history retention.

- Caching, asynchronous click pipelines, message queues, microservices, sharding, or multi-region architecture.

- Product-level limit on the number of links a user may create.

- Automatic link expiration.

# 3. Actors and System Boundary

| **Actor**          | **Authentication** | **Capabilities**                                                                                                           |
|--------------------|--------------------|----------------------------------------------------------------------------------------------------------------------------|
| Authenticated User | Required           | Create links; list owned links; regenerate owned links; delete owned links.                                                |
| Link Visitor       | Not required       | Open an active short URL and receive a redirect. May be authenticated or anonymous; management privileges are not implied. |

## 3.1 Trust Boundary

- The backend derives caller identity from the authentication mechanism; client-supplied user IDs are not trusted for authorization.

- A short code grants redirect capability only. It does not grant ownership, edit, delete, or regeneration capability.

- Ownership is enforced server-side by comparing the authenticated user identity to the Link owner.

# 4. Functional Requirements

| **ID** | **Requirement**       | **Specification**                                                                                                                                                                                                  |
|--------|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01  | Create Short Link     | An authenticated user can submit a valid absolute HTTP or HTTPS destination URL and receive a generated short link.                                                                                                |
| FR-02  | Public Redirect       | Any visitor can request an active short code and receive an HTTP redirect to the stored destination URL.                                                                                                           |
| FR-03  | List Own Links        | An authenticated user can list only links they own. An empty list is a successful response.                                                                                                                        |
| FR-04  | Click Count           | Each successful redirect request increments the logical link's cumulative total_clicks by one. Repeated visits count repeatedly; unique visitors are not tracked.                                                  |
| FR-05  | Delete Link           | An authenticated owner can delete a link. After successful deletion, requests beginning afterward must not resolve the former short code.                                                                          |
| FR-06  | Regenerate Link       | An authenticated owner can regenerate the short code for an existing logical link. The old code becomes invalid, while link identity, owner, destination, creation time, and cumulative click count are preserved. |
| FR-07  | Ownership Isolation   | Authenticated users cannot list, regenerate, or delete links owned by another user.                                                                                                                                |
| FR-08  | URL Validation        | Only syntactically valid absolute HTTP or HTTPS destination URLs are accepted.                                                                                                                                     |
| FR-09  | Short-Code Uniqueness | An active short code must uniquely resolve to at most one logical Link.                                                                                                                                            |
| FR-10  | Mutation Idempotency  | CREATE, DELETE, and REGENERATE support idempotency keys. Repeated requests with the same user, operation, key, and request payload are processed once and can replay the stored result.                            |
| FR-11  | Idempotency Misuse    | Reuse of the same idempotency key by the same user and operation with a different request payload is rejected.                                                                                                     |
| FR-12  | Durability            | Short-link mappings have no automatic expiration and remain durable until explicitly deleted by their owner.                                                                                                       |

# 5. Non-Functional Requirements

| **ID** | **Attribute**            | **Requirement**                                                                                                                                            |
|--------|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| NFR-01 | Latency                  | At expected V1 load, 95% of relevant application requests should complete within 500 ms, excluding latency of the external destination website.            |
| NFR-02 | Availability             | Target service availability is 99.9%. The current single-database design is acknowledged as a risk against this target and must be measured in deployment. |
| NFR-03 | Consistency - Delete     | After a delete operation successfully commits, new redirect requests must not resolve the deleted short code.                                              |
| NFR-04 | Consistency - Regenerate | Regeneration must atomically replace the active short code: after successful commit, the old code no longer resolves and the new code does.                |
| NFR-05 | Data Integrity           | Short-code uniqueness, referential integrity, non-negative click counts, and user ownership must remain valid under concurrency and failures.              |
| NFR-06 | Security                 | Passwords are never stored in plaintext. Authorization decisions are performed on the server using authenticated identity and resource ownership.          |
| NFR-07 | Maintainability          | The backend should remain a modular monolith with clear API, service, validation/generation, and persistence responsibilities.                             |

# 6. Capacity and Scale Assumptions

| **Metric**                       | **V1 Estimate** | **Basis**                                                 |
|----------------------------------|-----------------|-----------------------------------------------------------|
| Active link creators             | 100             | MVP design target.                                        |
| New links per user per day       | 5               | Product usage assumption.                                 |
| New links per day                | 500             | 100 × 5.                                                  |
| Average creation QPS             | ~0.006          | 500 / 86,400.                                             |
| Peak creation QPS                | ~0.03           | 5× peak multiplier.                                       |
| Views per newly created link/day | 100             | Workload assumption for estimation.                       |
| Redirects per day                | ~50,000         | 500 links/day × 100 views.                                |
| Average redirect QPS             | ~0.58           | 50,000 / 86,400.                                          |
| Peak redirect QPS                | ~2.9            | 5× average.                                               |
| Click state changes/day          | ~50,000         | One cumulative counter increment per successful redirect. |
| Storage per Link assumption      | 5 KB            | Conservative estimation value.                            |
| New Link storage/day             | ~2.5 MB         | 500 × 5 KB.                                               |
| New Link storage/year            | ~912.5 MB       | Approximate base link-record growth.                      |
| Three-year base Link storage     | ~2.74 GB        | Excludes indexes, DB overhead, backups, and user data.    |

Capacity conclusion: V1 is low-throughput and low-storage. The database is not expected to be capacity-bound under the estimated workload. Redirect correctness, persistence availability, idempotency, and transaction behavior are more important architectural concerns than horizontal scale.

# 7. API and Use-Case Boundary

| **Method** | **Endpoint**     | **Auth**         | **Purpose**                                                     | **Success Result**                             |
|------------|------------------|------------------|-----------------------------------------------------------------|------------------------------------------------|
| POST       | /links           | Required         | Create a short link.                                            | Created link representation.                   |
| GET        | /links           | Required         | List links owned by current user.                               | Array of link representations; \[\] when none. |
| PUT        | /links/{link_id} | Required + owner | Regenerate the current short code for an existing logical Link. | Updated link/new short URL.                    |
| DELETE     | /links/{link_id} | Required + owner | Delete an owned Link.                                           | Successful deletion response.                  |
| GET        | /{short_code}    | Public           | Resolve an active short code and redirect.                      | HTTP redirect to destination URL.              |

## 7.1 Link Response Shape

link_id

destination_url

short_code

total_clicks

created_on

## 7.2 API Error Classes

- Unauthenticated request to a protected endpoint.

- Authenticated caller does not own the requested Link.

- Malformed or unsupported destination URL.

- Requested Link or short code does not exist / is no longer active.

- Short-code unique constraint conflict during generation (handled internally by retry when possible).

- Idempotency-key reuse with a different request hash.

- Temporary processing conflict for an in-progress idempotent operation.

- Database or server failure.

| Exact HTTP status codes and error-body schema remain implementation-level decisions, but error classes and behavior are part of the architecture boundary. |
|------------------------------------------------------------------------------------------------------------------------------------------------------------|

# 8. Data Model and Persistence Design

## 8.1 Conceptual Entities

| **Entity**         | **Fields**                                                                                                                  | **Relationship / Notes**                                                                         |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| User               | id, name, email_address, hashed_password                                                                                    | One User owns zero or many Links.                                                                |
| Link               | id, user_id, destination_url, short_code, total_clicks, created_on                                                          | Every Link has exactly one User owner. Regeneration mutates short_code on the same logical Link. |
| IdempotencyRequest | idempotency_key, request_hash, response_code, response_body, status, operation, user_id, created_at, updated_at, expires_at | Tracks durable mutation processing and replay for CREATE/DELETE/REGENERATE.                      |

## 8.2 Relational Schema Baseline

users

- id UUID PRIMARY KEY

- name TEXT NOT NULL

- email_address TEXT UNIQUE NOT NULL

- hashed_password TEXT NOT NULL

links

- id UUID PRIMARY KEY

- destination_url TEXT NOT NULL

- short_code TEXT UNIQUE NOT NULL

- created_on TIMESTAMPTZ NOT NULL

- user_id UUID NOT NULL

- total_clicks INTEGER NOT NULL DEFAULT 0

- FOREIGN KEY (user_id) REFERENCES users(id)

- CHECK (total_clicks >= 0)

idempotency_request

- idempotency_key TEXT NOT NULL

- request_hash TEXT NOT NULL

- response_code INTEGER

- response_body TEXT

- status TEXT NOT NULL -- PROCESSING \| COMPLETED \| FAILED

- operation TEXT NOT NULL -- CREATE \| DELETE \| REGENERATE

- user_id UUID NOT NULL

- created_at TIMESTAMPTZ NOT NULL

- updated_at TIMESTAMPTZ NOT NULL

- expires_at TIMESTAMPTZ NOT NULL

- FOREIGN KEY (user_id) REFERENCES users(id)

- UNIQUE (user_id, operation, idempotency_key)

- CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED'))

- CHECK (operation IN ('CREATE', 'DELETE', 'REGENERATE'))

## 8.3 Required Indexes / Constraints

- Primary-key indexes on users.id and links.id.

- Unique index/constraint on users.email_address.

- Unique index/constraint on links.short_code.

- Index on links.user_id to support GET /links efficiently. A composite (user_id, id) form is acceptable if it matches query/pagination strategy.

- Unique index/constraint on (user_id, operation, idempotency_key).

- A separate composite user(email_address, id) index is not required merely for uniqueness because email_address UNIQUE already provides an index in common relational databases; add only if query evidence justifies it.

## 8.4 Core Data Invariants

- Every Link references exactly one existing User.

- A short_code identifies at most one Link.

- destination_url is not globally unique; multiple users and multiple logical links may reference the same destination.

- total_clicks is never negative.

- Regeneration preserves link id, user_id, destination_url, total_clicks, and created_on while replacing short_code.

- Hard deletion removes the Link; its former short code must no longer resolve.

# 9. Idempotency Strategy

Idempotency applies to CREATE, DELETE, and REGENERATE. The client supplies an idempotency key. The server scopes the key by authenticated user and operation and stores a hash of the request payload.

| **Case**                                             | **Required Behavior**                                                                                                      |
|------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| Same user + operation + key + same request hash      | Process once. Retries return/replay the stored result when COMPLETED.                                                      |
| Same user + operation + key + different request hash | Reject as invalid key reuse.                                                                                               |
| Concurrent requests with same scoped key             | Database uniqueness allows only one request record to claim the operation.                                                 |
| Status = PROCESSING                                  | A later retry must not blindly execute the mutation again. Recovery/expiration behavior must be defined in implementation. |
| Status = COMPLETED                                   | Return the persisted response_code and response_body.                                                                      |
| Status = FAILED                                      | Implementation must define whether the same key replays failure or may be retried after a controlled transition.           |

## 9.1 Important Transaction Requirement

Business-state mutation and idempotency-state transition must be coordinated so that a committed Link change cannot be silently followed by a duplicate retry because the idempotency record remained ambiguous. The preferred V1 implementation should use one database transaction whenever the business data and idempotency record are stored in the same relational database.

# 10. High-Level Architecture (C4)

The C4 context and container views define the system boundary and major deployable/runtime containers. The architecture is a modular monolith: one FastAPI backend owns application logic and communicates with one durable relational database. The public redirect path bypasses the management frontend and reaches the backend directly.

![C4 System Context and Container Architecture](URL_Shortener_MVP_C4_Architecture.png)

*Figure 1. C4 System Context and Container Architecture for the URL Shortener MVP.*

## 10.1 Container Responsibilities

| **Container**            | **Responsibility**                                                                                                                                                                                                |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Frontend Web Application | User interface for authenticated users to create and manage their links.                                                                                                                                          |
| FastAPI Backend          | Authentication integration, authorization/ownership checks, link-management orchestration, URL validation, short-code generation, redirect resolution, click counting, idempotency, and persistence coordination. |
| Relational Database      | Durable users, links, idempotency state, uniqueness constraints, indexes, and transaction guarantees.                                                                                                             |

## 10.2 Explicitly Excluded Containers

- No cache: current peak redirect load is small and immediate invalidation requirements would add cache-consistency complexity.

- No message queue/background worker: V1 uses synchronous click counting and mutation processing.

- No microservices: there is no requirement for independent scaling/deployment boundaries at V1.

- No separate analytics store: only an aggregate click counter is required.

# 11. Backend Component Architecture

| **Component**                | **Responsibility**                                                                                                                | **Representative Contract**                                                                                                       |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Link API                     | HTTP request/response boundary; invokes service methods; maps results/errors to HTTP semantics.                                   | create_link, list_links, regenerate_link, delete_link, redirect endpoint                                                          |
| Authentication               | Identifies the caller for protected operations.                                                                                   | current_user                                                                                                                      |
| Link Service                 | Owns Link business rules, ownership checks, idempotency orchestration, short-code retry orchestration, and use-case coordination. | create_link(), resolve_link(), regenerate_link(), delete_link(), list_links()                                                     |
| URL Validator                | Validates destination URL scheme and syntax.                                                                                      | validate(destination_url)                                                                                                         |
| Short Code Generator         | Generates candidate short codes; has no DB responsibility.                                                                        | generate_code()                                                                                                                   |
| Link Repository              | Persistence abstraction for Links and click updates.                                                                              | create_link(), get_by_id(), get_by_short_code(), increment_click_count(), update_short_code(), delete_link(), get_links_by_user() |
| Idempotency Repository/logic | Claims idempotency keys and persists processing/result state.                                                                     | begin/claim, complete, fail, get/replay                                                                                           |
| Database                     | Enforces durable constraints and transaction atomicity.                                                                           | Relational persistence                                                                                                            |

Ownership checking is a Link Service business rule rather than a standalone component in V1. The same FastAPI deployment may use separate management and redirect routers for clarity, but they are not separate services.

# 12. Runtime Flows

## 12.1 Create Link

1.  Request reaches Link API.

2.  Authentication identifies the current user; unauthenticated requests are rejected.

3.  Link Service validates the destination URL.

4.  Idempotency logic claims or resolves the scoped idempotency key and verifies request_hash consistency.

5.  Link Service asks Short Code Generator for a candidate code.

6.  Repository attempts to insert the Link. The database UNIQUE(short_code) constraint is the final collision authority.

7.  If insertion fails due to short-code collision, Link Service generates another candidate and retries.

8.  Business change and idempotency completion are committed consistently.

9.  Created-link response is returned and stored for replay.

## 12.2 Redirect

10. Visitor requests /{short_code}.

11. Link API asks Link Service to resolve the code.

12. Repository queries the active Link by short_code.

13. If no Link exists, return a not-found/invalid-link response; do not redirect.

14. If the Link exists, increment total_clicks atomically.

15. Link Service returns destination_url.

16. Link API returns an HTTP redirect to the visitor.

## 12.3 Regenerate

17. Authenticated request identifies link_id and current user.

18. Repository loads the Link.

19. Link Service verifies ownership.

20. Idempotency logic claims/resolves the regeneration request.

21. Generate a new candidate short code.

22. Atomically update the existing Link row to the new short_code; preserve identity, owner, destination, created_on, and total_clicks.

23. If the new code conflicts with UNIQUE(short_code), generate another and retry.

24. Commit mutation and idempotency result consistently.

25. Return the updated link. After commit, the old short code no longer resolves.

## 12.4 Delete

26. Authenticated request identifies link_id and current user.

27. Repository loads the Link.

28. Link Service verifies ownership.

29. Idempotency logic claims/resolves the delete request.

30. Hard-delete the Link in a transaction.

31. Commit deletion and idempotency result consistently.

32. Return success. New redirect requests after commit must not resolve the former code.

## 12.5 List Links

33. Authenticate and identify current user.

34. Repository queries Links by user_id only.

35. Return link_id, destination_url, short_code, total_clicks, and created_on.

36. If none exist, return an empty array rather than an error.

# 13. Transaction and Consistency Requirements

| **Concern**                 | **Required V1 Behavior**                                                                                                                    |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| Short-code collision        | Do not rely on check-before-insert. Generate a candidate and let the unique DB constraint protect the insert/update; retry on conflict.     |
| Concurrent click increments | Use an atomic database increment (conceptually total_clicks = total_clicks + 1), not application read-modify-write.                         |
| Regeneration                | Single logical/transactional state transition. Either the old code remains active or the new code becomes active; no durable partial state. |
| Deletion                    | Hard delete must be transactional. After successful commit, future redirect lookups must not resolve the row.                               |
| Idempotent mutations        | Where possible, mutation and idempotency completion occur in the same transaction.                                                          |
| Delete vs redirect race     | A redirect already in flight before deletion may complete. Requests beginning after successful deletion must not resolve the deleted code.  |
| Concurrent regenerations    | Behavior must be explicit. Recommended V1: serialize/guard updates or use optimistic concurrency so silent lost updates are avoided.        |

# 14. Failure, Bottleneck, and Risk Analysis

| **Failure / Risk**                    | **Effect**                                                      | **Severity** | **Existing Protection / Status**                                            |
|---------------------------------------|-----------------------------------------------------------------|--------------|-----------------------------------------------------------------------------|
| Database unavailable                  | Create/list/delete/regenerate and redirects become unavailable. | High         | None at architecture level; DB is a single dependency.                      |
| Backend instance crashes              | In-flight requests may fail or be retried.                      | Medium       | Idempotency partially protects mutations.                                   |
| Short-code collision                  | One generation attempt conflicts.                               | Low          | UNIQUE(short_code) + service retry.                                         |
| Duplicate mutation request            | Could otherwise execute multiple times.                         | Low/Medium   | Database-backed idempotency.                                                |
| Idempotency stuck at PROCESSING       | Retries may be blocked or ambiguous.                            | Medium       | expires_at exists; recovery semantics still need implementation definition. |
| Commit succeeds but response is lost  | Client may retry an already-successful operation.               | Medium       | COMPLETED idempotency record should replay stored response.                 |
| Concurrent click updates              | Click increments may be lost.                                   | Medium       | Must use atomic increment.                                                  |
| Delete vs redirect race               | An already in-flight request may still redirect.                | Medium       | Consistency boundary defined around successful delete commit.               |
| Concurrent regenerations              | One request may overwrite another silently.                     | Medium       | Needs explicit locking/version strategy.                                    |
| Storage/QPS overload at current scale | Little practical impact.                                        | Low          | Estimated workload is far below normal relational DB capacity.              |

# 15. Architecture Trade-offs and Evolution Triggers

| **Decision**                | **Benefit**                                                                                       | **Cost / Risk**                                                                   | **Revisit When**                                                                            |
|-----------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| Single FastAPI backend      | Simple development, deployment, tracing, and transactions.                                        | Whole backend deploys together; no independent scaling/reliability boundaries.    | A capability demonstrably needs independent scaling, deployment, ownership, or reliability. |
| Single relational database  | Simple management and strong transactions; ample V1 capacity.                                     | Single point of failure for redirects and management operations.                  | 99.9% target cannot be met or DB becomes measured bottleneck.                               |
| No cache                    | No extra service or invalidation complexity; immediate delete/regenerate behavior remains simple. | All redirect lookups hit DB.                                                      | Measured DB or redirect latency/load approaches limits.                                     |
| Hard deletion               | Simple and matches current product scope.                                                         | No recovery or audit history.                                                     | Product requires recovery window, auditing, or retention.                                   |
| Aggregate total_clicks only | Minimal storage and simple queries.                                                               | No time-series, referrer, device, geography, or unique-visitor analytics.         | Analytics/dashboard requirements expand.                                                    |
| Synchronous click counting  | Simple and counts update immediately.                                                             | Analytics write lies on redirect critical path.                                   | Redirect latency/write volume matters more or eventual analytics becomes acceptable.        |
| Database-backed idempotency | Durable retry behavior across restarts and multiple instances.                                    | Mutation and idempotency state require careful transaction/recovery coordination. | Mutation scale or architecture justifies another durable coordination mechanism.            |
| No custom alias             | Simplifies generation and collision rules.                                                        | Users cannot choose memorable codes.                                              | Product explicitly requires aliases.                                                        |

# 16. Security Requirements

- Store only password hashes; never plaintext passwords.

- Use a proven password-hashing algorithm/library appropriate at implementation time; do not implement cryptography manually.

- Protected endpoints require authentication.

- Ownership checks are performed server-side using authenticated identity and persisted user_id.

- Do not trust user_id/author_id supplied by clients for authorization.

- Accept only absolute HTTP/HTTPS destination URLs in V1.

- Use parameterized ORM/query mechanisms; do not construct SQL from user input.

- Idempotency keys are scoped by user and operation and must not allow one user to inspect another user's stored response.

- Return errors that do not unnecessarily disclose another user's resource existence.

- Use HTTPS in deployed environments for credentials, tokens, and management operations.

| Advanced malicious-URL reputation scanning is explicitly out of scope for V1. URL syntax validation is not equivalent to phishing/malware detection. |
|------------------------------------------------------------------------------------------------------------------------------------------------------|

# 17. Observability and Operations

Although V1 is small, the 99.9% availability and 500 ms latency goals require basic measurement. Observability should remain lightweight.

- Structured request logs with request/correlation ID; avoid logging passwords, raw auth tokens, or other secrets.

- Metrics for request count, latency percentiles, error rate, redirect success/failure, DB errors, short-code collision retries, idempotency status counts, and click-update failures.

- Health/readiness endpoint that reflects application readiness and, where appropriate, database connectivity.

- Database backup and restore procedure consistent with the durability requirement.

- Alerts or at minimum operational visibility for sustained backend/DB failures that threaten availability.

# 18. Testing and Acceptance Criteria

| **Area**             | **Minimum Acceptance Criteria**                                                                                                         |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Create               | Authenticated valid URL creates one Link and returns a short code. Invalid scheme is rejected. Unauthenticated request is rejected.     |
| Short-code collision | Forced collision cannot create duplicate short_code; service retries or returns controlled failure.                                     |
| Idempotent create    | Same user/operation/key/hash repeated concurrently or after response loss produces one logical mutation and a consistent replay result. |
| Idempotency misuse   | Same scoped key with different request payload is rejected.                                                                             |
| Redirect             | Existing code returns HTTP redirect to destination and increments total_clicks once per successful request.                             |
| Concurrent redirects | Parallel redirects do not lose click increments.                                                                                        |
| Delete               | Owner can delete; non-owner cannot; after commit the former code no longer resolves.                                                    |
| Regenerate           | Owner can regenerate; non-owner cannot; code changes, old code becomes invalid, destination/id/owner/click count remain unchanged.      |
| List                 | User receives only owned links; empty ownership returns \[\].                                                                           |
| Failure recovery     | Response-loss retry can replay COMPLETED idempotency result; PROCESSING expiry/recovery behavior is tested once defined.                |
| Performance          | Under expected V1 load, measured p95 for relevant application operations is below 500 ms in the target environment.                     |
| Persistence          | Backup/restore or equivalent verification demonstrates durable recovery of user/link mappings.                                          |

# 19. Implementation Constraints and Open Decisions

## 19.1 Confirmed Constraints

- Backend language/framework: Python + FastAPI.

- Architecture: modular monolith.

- Persistence: one relational database for V1.

- No cache/message queue/microservices in baseline architecture.

- Hard-delete Links.

- Short-code generation is application-owned, uniqueness is database-enforced.

## 19.2 Open Decisions Before or During Implementation

| **Decision**                                  | **What Must Be Defined**                                                                                                  |
|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Database technology / ORM / migration tooling | Select a relational DB and persistence stack suitable for FastAPI and transactional idempotency.                          |
| Authentication mechanism                      | Define signup/login/token/session behavior and password-hash implementation.                                              |
| Short-code alphabet and length                | Choose entropy, allowed characters, collision retry ceiling, and reserved-route handling.                                 |
| Root redirect route namespace                 | GET /{short_code} is concise but may collide with routes such as /docs or /health; define reserved paths or use a prefix. |
| PROCESSING idempotency recovery               | Define timeout/expiry, ownership of retry after expiry, and whether orphaned PROCESSING entries are failed/reclaimed.     |
| FAILED idempotency replay                     | Define whether failure is replayed permanently for the key or can transition to a retryable state.                        |
| Click update failure policy                   | Decide whether an analytics write failure blocks redirect. Current synchronous flow places this on the critical path.     |
| Concurrent regeneration control               | Choose row locking, optimistic versioning, or another explicit conflict policy.                                           |
| User deletion policy                          | Account deletion is not currently a V1 use case; if added, choose RESTRICT vs CASCADE/retention semantics.                |
| Exact HTTP statuses and schemas               | Finalize REST status codes, validation responses, and standard error body.                                                |

# 20. MVP Definition of Done

- All confirmed functional requirements FR-01 through FR-12 are implemented and covered by automated tests.

- Protected operations authenticate callers and enforce link ownership server-side.

- Short-code uniqueness is enforced by the database and collision retry is tested.

- CREATE, DELETE, and REGENERATE idempotency behavior is implemented, including request-hash mismatch detection and documented PROCESSING recovery semantics.

- Redirects correctly resolve active codes, atomically increment click counts, and return HTTP redirects.

- Delete and regenerate meet their post-commit invalidation guarantees.

- Database migrations define all required tables, constraints, foreign keys, and indexes.

- p95 application latency is measured against the 500 ms target under expected V1 load.

- Deployment includes basic health checks, structured logging, and a database backup/restore strategy.

- Open implementation decisions in Section 19 are resolved or explicitly deferred with rationale.

# Appendix A — Architecture Decision Summary

The MVP architecture is intentionally conservative: one FastAPI modular monolith and one relational database. The design avoids cache, queues, microservices, and detailed analytics because the estimated peak workload (~3 redirects/second) does not justify the operational and consistency cost. Correctness is instead concentrated in database constraints, atomic counter updates, transactional regeneration/deletion, and durable idempotency.

# Appendix B — Traceability: Requirement to Component

| **Requirement Area**             | **Primary Components**                                                    |
|----------------------------------|---------------------------------------------------------------------------|
| Authenticated management         | Link API, Authentication, Link Service                                    |
| URL validation                   | Link Service, URL Validator                                               |
| Short-code generation/uniqueness | Link Service, Short Code Generator, Link Repository, DB unique constraint |
| Redirect resolution              | Link API, Link Service, Link Repository, Database                         |
| Click counting                   | Link Service, Link Repository, atomic DB update                           |
| Ownership                        | Authentication, Link Service, Link Repository                             |
| Delete/regenerate consistency    | Link Service, Link Repository, Database transaction                       |
| Idempotency                      | Link Service / Idempotency logic, Idempotency repository, Database        |
| Durability                       | Relational Database, backup/restore operations                            |
