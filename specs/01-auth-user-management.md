# Specification 01: Authentication & User Management

- **Spec ID**: `SPEC-01`
- **Component**: Authentication & User Module
- **Traceability**: [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) — FR-07, NFR-06, Section 8, Section 16
- **Status**: Ready for Implementation

---

## 1. Overview & Objective

The Authentication & User Management module establishes identity for callers of Linklet's management endpoints (`/links`, `/links/{id}`). It guarantees password security, generates secure JSON Web Tokens (JWT) for authenticated sessions, and provides a server-side caller context (`current_user`) for ownership enforcement.

---

## 2. Key Architecture Invariants

1. **Plaintext Passwords**: Passwords MUST NEVER be stored in plaintext or logged.
2. **Password Hashing**: Passwords MUST be hashed using standard cryptographic algorithms (e.g., Argon2id or bcrypt via `passlib`).
3. **Server-Side Authorization**: Identity and ownership decisions MUST use the authenticated `user_id` parsed from the JWT. Client-supplied user IDs in headers or payload MUST NOT be trusted.
4. **Token Format**: Standard OAuth2 Bearer JWT containing `sub` (user UUID) and `exp` (expiration timestamp).

---

## 3. Data Schemas

### 3.1 User Registration Payload (`UserRegisterRequest`)
```json
{
  "name": "Jane Doe",
  "email_address": "jane@example.com",
  "password": "SecurePassword123!"
}
```
- `name`: String, non-empty, max 100 characters.
- `email_address`: String, valid RFC 5322 email syntax, unique across `users` table.
- `password`: String, minimum 8 characters.

### 3.2 User Response (`UserResponse`)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Jane Doe",
  "email_address": "jane@example.com"
}
```

### 3.3 Token Response (`TokenResponse`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

## 4. API Endpoints

### 4.1 Register User (`POST /auth/register`)

Creates a new user account with a hashed password.

- **Authentication**: None (Public)
- **Request Body**: `UserRegisterRequest`
- **Response**: `201 Created` with `UserResponse` body.

#### Error Scenarios:
- `400 Bad Request`: Invalid email syntax or password length < 8.
- `409 Conflict`: Email address already registered (`users_email_address_key` unique violation).

---

### 4.2 Login / Get Token (`POST /auth/token`)

Authenticates user credentials and returns a Bearer access token.

- **Authentication**: None (Public)
- **Request Body**: `OAuth2PasswordRequestForm` (standard `username` [maps to email] and `password`) OR `UserLoginRequest` (`email_address`, `password`).
- **Response**: `200 OK` with `TokenResponse` body.

#### Error Scenarios:
- `401 Unauthorized`: User not found or password verification failed. Response body:
  ```json
  {
    "error": {
      "code": "INVALID_CREDENTIALS",
      "message": "Invalid email address or password.",
      "details": null
    }
  }
  ```

---

### 4.3 Get Current User Profile (`GET /auth/me`)

Retrieves profile details for the currently authenticated caller.

- **Authentication**: Required (`Authorization: Bearer <token>`)
- **Response**: `200 OK` with `UserResponse` body.

#### Error Scenarios:
- `401 Unauthorized`: Token missing, expired, corrupted, or signature verification failed.

---

## 5. Middleware & Dependency Contracts

### `get_current_user` Dependency
FastAPI dependency that must be injected into all protected routes:

1. Extract `Authorization` HTTP header (`Bearer <token>`).
2. Verify JWT signature using server secret key and decode payload.
3. Check token `exp` timestamp. If expired, raise `401 Unauthorized`.
4. Extract `sub` (User UUID).
5. Fetch `User` from repository. If user does not exist, raise `401 Unauthorized`.
6. Return `User` domain model object to route handler.

---

## 6. Test & Acceptance Criteria

| ID | Scenario | Input / Action | Expected Result |
|----|----------|----------------|-----------------|
| `TC-AUTH-01` | Successful Registration | Valid `UserRegisterRequest` | `201 Created`, user returned without `hashed_password` field |
| `TC-AUTH-02` | Duplicate Email | Register with existing email | `409 Conflict`, error code `EMAIL_ALREADY_EXISTS` |
| `TC-AUTH-03` | Invalid Email Format | Register with `not-an-email` | `422 Unprocessable Entity` validation error |
| `TC-AUTH-04` | Successful Login | Correct email + password | `200 OK`, valid JWT access token returned |
| `TC-AUTH-05` | Wrong Password Login | Valid email + invalid password | `401 Unauthorized`, `INVALID_CREDENTIALS` |
| `TC-AUTH-06` | Expired Token Access | Protected endpoint with expired token | `401 Unauthorized` |
| `TC-AUTH-07` | Valid Token Access | Protected endpoint with valid token | `200 OK`, request succeeds |
