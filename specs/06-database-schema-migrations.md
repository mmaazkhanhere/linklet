# Specification 06: Relational Database Schema & Migrations

- **Spec ID**: `SPEC-06`
- **Component**: Persistence & Database Module
- **Traceability**: [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) — Section 8, Section 13, Section 19
- **Status**: Ready for Implementation

---

## 1. Overview & Objective

The Database Schema & Migrations specification defines the relational persistence layer for Linklet. It details table definitions, primary and foreign keys, data constraints, performance indexes, and migration patterns required to support high-performance redirects and transactional idempotency.

---

## 2. Relational DDL Specifications

### 2.1 Table: `users`

Stores user account credentials and identity metadata.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email_address TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_email_address_key UNIQUE (email_address)
);
```

#### Constraints & Indexes:
- Primary Key: `id` (UUID)
- Unique Index: `users_email_address_key` on `email_address`

---

### 2.2 Table: `links`

Stores core short link mappings, ownership, destination URLs, and cumulative click metrics.

```sql
CREATE TABLE links (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    destination_url TEXT NOT NULL,
    short_code TEXT NOT NULL,
    total_clicks INTEGER NOT NULL DEFAULT 0,
    created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_links_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT links_short_code_key UNIQUE (short_code),
    CONSTRAINT chk_links_total_clicks_non_negative CHECK (total_clicks >= 0)
);
```

#### Constraints & Indexes:
- Primary Key: `id` (UUID)
- Foreign Key: `user_id` references `users(id)`
- Unique Index: `links_short_code_key` on `short_code` (Base62 uniqueness constraint authority)
- Check Constraint: `total_clicks >= 0`
- Secondary Index: `idx_links_user_id` on `user_id` (Optimizes `GET /links` query execution)

```sql
CREATE INDEX idx_links_user_id ON links(user_id);
```

---

### 2.3 Table: `idempotency_request`

Stores durable mutation idempotency processing states and replay payloads.

```sql
CREATE TABLE idempotency_request (
    idempotency_key TEXT NOT NULL,
    user_id UUID NOT NULL,
    operation TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_code INTEGER,
    response_body TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, operation, idempotency_key),
    CONSTRAINT fk_idempotency_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_idempotency_status CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')),
    CONSTRAINT chk_idempotency_operation CHECK (operation IN ('CREATE', 'DELETE', 'REGENERATE'))
);
```

#### Constraints & Indexes:
- Composite Primary Key: `(user_id, operation, idempotency_key)`
- Foreign Key: `user_id` references `users(id)`
- Check Constraints: `status` valid states, `operation` valid operations
- Index: `idx_idempotency_expires_at` on `expires_at` (Optimizes background TTL cleanup)

```sql
CREATE INDEX idx_idempotency_expires_at ON idempotency_request(expires_at);
```

---

## 3. Migration Sequencing Plan (Alembic)

Database schema evolution MUST be managed via sequential Alembic migration scripts in `alembic/versions/`:

1. `0001_create_users_table.py`: Defines `users` table and `users_email_address_key` unique constraint.
2. `0002_create_links_table.py`: Defines `links` table, foreign keys, `links_short_code_key` unique constraint, and `idx_links_user_id` index.
3. `0003_create_idempotency_request_table.py`: Defines `idempotency_request` table, composite primary key, and check constraints.

---

## 4. Test & Acceptance Criteria

| ID | Scenario | Verification Step | Expected Result |
|----|----------|-------------------|-----------------|
| `TC-DB-01` | Migration Execution | Run `alembic upgrade head` | All 3 tables created cleanly without errors |
| `TC-DB-02` | Unique Email Constraint | Insert 2 users with identical `email_address` | 2nd insert rejected with unique constraint error |
| `TC-DB-03` | Unique Short Code Constraint | Insert 2 links with identical `short_code` | 2nd insert rejected with unique constraint error |
| `TC-DB-04` | Non-Negative Clicks | Update `total_clicks` to -1 | Update rejected with check constraint error |
| `TC-DB-05` | Valid Idempotency Status | Insert `idempotency_request` with status `INVALID` | Insert rejected with check constraint error |
| `TC-DB-06` | Foreign Key Constraint | Insert `links` with non-existent `user_id` | Insert rejected with foreign key error |
