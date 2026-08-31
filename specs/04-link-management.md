# Specification 04: Link Lifecycle Management (List, Regenerate, Delete)

- **Spec ID**: `SPEC-04`
- **Component**: Link Service & Management Router
- **Traceability**: [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) — FR-03, FR-05, FR-06, FR-07, NFR-03, NFR-04, Section 12.3–12.5
- **Status**: Ready for Implementation

---

## 1. Overview & Objective

The Link Lifecycle Management module allows authenticated users to list their owned links, regenerate short codes for existing links while preserving accumulated metrics, and hard-delete links. It strictly enforces server-side user ownership isolation and guarantees post-commit invalidation for deleted or regenerated short codes.

---

## 2. API Endpoint Specifications

### 2.1 List Owned Links (`GET /links`)

Returns all short link mappings owned by the authenticated caller.

- **Authentication**: Required (`Authorization: Bearer <token>`)
- **Success Response**: `200 OK`
- **Response Body**: Array of `LinkResponse` objects
  ```json
  [
    {
      "link_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "destination_url": "https://example.com/page1",
      "short_code": "aB3k9Xy",
      "total_clicks": 42,
      "created_on": "2026-08-31T12:00:00Z"
    }
  ]
  ```
- **Empty State**: If the caller owns zero links, return `200 OK` with an empty array `[]` (NOT `404 Not Found`).

---

### 2.2 Regenerate Short Code (`PUT /links/{link_id}`)

Replaces the active `short_code` for a link with a freshly generated code.

- **Authentication**: Required (`Authorization: Bearer <token>`)
- **Headers**: `Idempotency-Key` (Optional)
- **Path Parameter**: `link_id` (UUID)
- **Success Response**: `200 OK` with updated `LinkResponse`

#### Invariants & Preserved State (FR-06, NFR-04):
- **Mutated**: `short_code` (new Base62 candidate generated).
- **PRESERVED**: `link_id`, `user_id`, `destination_url`, `total_clicks`, `created_on`.
- **Post-Commit Invalidation**: The old short code MUST IMMEDIATELY stop resolving (`404 Not Found`). The new short code MUST resolve.

#### Error Scenarios:
- `404 Not Found`: Link does not exist OR link is owned by another user.
- `401 Unauthorized`: Unauthenticated caller.

---

### 2.3 Delete Link (`DELETE /links/{link_id}`)

Hard-deletes a link mapping from the database.

- **Authentication**: Required (`Authorization: Bearer <token>`)
- **Headers**: `Idempotency-Key` (Optional)
- **Path Parameter**: `link_id` (UUID)
- **Success Response**: `200 OK` or `204 No Content`
  ```json
  {
    "message": "Link successfully deleted."
  }
  ```

#### Invariants & Post-Commit Consistency (FR-05, NFR-03):
- The link row is permanently removed from the `links` table.
- Requests to `GET /{former_short_code}` initiating after delete transaction commit MUST receive `404 Not Found`.

#### Error Scenarios:
- `404 Not Found`: Link does not exist OR link is owned by another user.
- `401 Unauthorized`: Unauthenticated caller.

---

## 3. Server-Side Ownership Enforcement (FR-07)

To prevent resource enumeration and unauthorized access:

1. All repository queries for individual link mutation (`PUT`, `DELETE`) MUST filter by BOTH `link_id` AND `user_id`:
   ```sql
   SELECT * FROM links WHERE id = :link_id AND user_id = :current_user_id;
   ```
2. If no row is returned, the API MUST return `404 Not Found` (rather than `403 Forbidden`). This prevents malicious users from discovering whether a specific `link_id` exists in another user's account.

---

## 4. Concurrent Regeneration Guard & Locking

To prevent race conditions during concurrent regeneration attempts:

1. Acquire a pessimistic row lock during regeneration:
   ```sql
   SELECT * FROM links WHERE id = :link_id AND user_id = :current_user_id FOR UPDATE;
   ```
2. Generate new Base62 candidate code.
3. Update `short_code` in `links` table. If unique collision occurs, retry candidate generation up to 5 times before committing transaction.

---

## 5. Test & Acceptance Criteria

| ID | Scenario | Input / Action | Expected Result |
|----|----------|----------------|-----------------|
| `TC-MGMT-01` | List Owned Links | `GET /links` with 2 owned links | `200 OK`, returns array of 2 `LinkResponse` items |
| `TC-MGMT-02` | List Empty Links | `GET /links` with 0 owned links | `200 OK`, returns `[]` |
| `TC-MGMT-03` | Regenerate Code | `PUT /links/{id}` on owned link | `200 OK`, `short_code` changed, `total_clicks` & `destination_url` unchanged |
| `TC-MGMT-04` | Old Code Invalidation | `GET /{old_code}` after regeneration | `404 Not Found` |
| `TC-MGMT-05` | New Code Resolution | `GET /{new_code}` after regeneration | `307 Temporary Redirect` to original destination |
| `TC-MGMT-06` | Delete Link | `DELETE /links/{id}` on owned link | `200 OK`, link deleted |
| `TC-MGMT-07` | Post-Delete Resolution | `GET /{deleted_code}` after deletion | `404 Not Found` |
| `TC-MGMT-08` | Cross-User Delete | User A deletes User B's `link_id` | `404 Not Found`, link NOT deleted |
| `TC-MGMT-09` | Cross-User Regenerate | User A regenerates User B's `link_id` | `404 Not Found`, code NOT regenerated |
