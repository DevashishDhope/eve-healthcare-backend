# EVE Healthcare Backend Service

Production-ready backend service for diagnostic test bookings and simulated payments built for the EVE Healthcare SDE Intern Backend Engineering Assignment.

---

## 1. Overview
The service provides a robust API for managing diagnostic centres and medical tests, allowing authenticated patients to book appointments with historical price snapshots, simulate payments, and process external payment webhook callbacks with guaranteed database-level idempotency and concurrency protection.

---

## 2. Features
- **User Authentication**: Secure signup and login with bcrypt password hashing and JWT access tokens.
- **Diagnostic Catalogue**: Management of diagnostic centres, tests, and centre-specific test pricing offerings (`CentreTest`).
- **Booking Engine**: Validates future appointments, snapshotting offering prices at creation to preserve historical accuracy.
- **Booking State Machine**: Enforces strict transitions across `PENDING`, `CONFIRMED`, `FAILED`, and `CANCELLED`.
- **Payment Processing**: Simulated mock payment processing (`SUCCESS` / `FAILED`) with transactional row-locking.
- **Webhook Idempotency**: Database-level deduplication via unique event constraints and PostgreSQL partial unique indexes.
- **Security & Authorization**: Strict tenant isolation preventing patients from viewing, cancelling, or paying for other users' bookings.

---

## 3. Tech Stack
- **Framework**: FastAPI (Python 3.13)
- **Database**: PostgreSQL 18
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic
- **Validation**: Pydantic v2 & email-validator
- **Security**: PyJWT (`HS256`), bcrypt (12 rounds)
- **Testing**: Pytest & HTTPX TestClient running against native PostgreSQL (`eve_healthcare_test`)

---

## 4. Architecture
The application adheres to a clean, layered architecture:
```
┌────────────────────────────────────────────────────────┐
│                   API / Routers                        │
│   (Request validation, HTTP endpoints, Auth deps)      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Service Layer                         │
│  (Business logic, State transitions, Idempotency)      │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼──────────────┐  ┌──────────▼─────────────┐
│    Pydantic Schemas        │  │   SQLAlchemy Models    │
│  (Data validation & DTOs)  │  │ (PostgreSQL ORM & DB)  │
└────────────────────────────┘  └────────────────────────┘
```

---

## 5. Project Structure
```
EVE-Healthcare/
├── app/
│   ├── main.py                     # FastAPI application factory & router setup
│   ├── dependencies.py             # Auth & webhook security dependencies
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings (.env loading)
│   │   └── security.py             # Password hashing (bcrypt) & JWT operations
│   ├── db/
│   │   ├── base.py                 # DeclarativeBase
│   │   └── session.py              # Engine, sessionmaker, and get_db dependency
│   ├── models/
│   │   ├── user.py                 # User table
│   │   ├── diagnostic_centre.py    # DiagnosticCentre table
│   │   ├── diagnostic_test.py      # DiagnosticTest table
│   │   ├── centre_test.py          # CentreTest offering table
│   │   ├── booking.py              # Booking table
│   │   ├── payment.py              # Payment table (with partial unique index)
│   │   └── webhook_event.py        # PaymentWebhookEvent idempotency ledger
│   ├── schemas/
│   │   ├── auth.py                 # Signup, login, and token DTOs
│   │   ├── catalogue.py            # Centres, tests, and offerings DTOs
│   │   ├── booking.py              # Booking request and response DTOs
│   │   └── payment.py              # Payment and webhook DTOs
│   ├── services/
│   │   ├── auth_service.py         # User registration and authentication
│   │   ├── booking_service.py      # Booking creation and state lifecycle
│   │   ├── payment_service.py      # Simulated payments with row locking
│   │   └── webhook_service.py      # Webhook ingestion, verification, & idempotency
│   └── api/
│       └── routes/
│           ├── auth.py             # /auth endpoints
│           ├── centres.py          # /centres endpoints
│           ├── tests.py            # /tests endpoints
│           ├── centre_tests.py     # /centre-tests endpoints
│           ├── bookings.py         # /bookings endpoints
│           └── payments.py         # /payments endpoints & webhook
├── alembic/
│   ├── env.py                      # Alembic environment configured with app settings
│   └── versions/                   # Migration versions
├── tests/
│   ├── conftest.py                 # PostgreSQL test fixtures and schema management
│   ├── test_auth.py                # Authentication and JWT tests
│   ├── test_catalogue.py           # Catalogue CRUD and offering tests
│   ├── test_bookings.py            # Booking creation, price snapshot, cancellation tests
│   ├── test_authorization.py       # Cross-user isolation tests
│   ├── test_payments.py            # Simulated payments and partial index tests
│   └── test_webhooks.py            # Webhook idempotency and edge-case tests
├── .env.example
├── requirements.txt
├── alembic.ini
└── README.md
```

---

## 6. Database Design
- **`users`**: `id` (UUID PK), `email` (VARCHAR UNIQUE), `password_hash` (VARCHAR), `created_at`.
- **`diagnostic_centres`**: `id` (UUID PK), `name` (VARCHAR), `location` (VARCHAR), `created_at`.
- **`diagnostic_tests`**: `id` (UUID PK), `name` (VARCHAR), `description` (TEXT), `created_at`.
- **`centre_tests`**: `id` (UUID PK), `centre_id` (FK), `test_id` (FK), `price` (NUMERIC), `created_at`. Constraint: `UNIQUE(centre_id, test_id)`.
- **`bookings`**: `id` (UUID PK), `user_id` (FK), `centre_test_id` (FK), `appointment_datetime`, `amount` (NUMERIC snapshot), `status`, timestamps.
- **`payments`**: `id` (UUID PK), `booking_id` (FK), `transaction_reference` (VARCHAR UNIQUE), `amount` (NUMERIC), `status` (VARCHAR), `payment_method`, timestamps.
  - **Critical PostgreSQL Constraint**:
    ```sql
    CREATE UNIQUE INDEX uq_one_success_payment_per_booking
    ON payments (booking_id)
    WHERE status = 'SUCCESS';
    ```
- **`payment_webhook_events`**: `id` (UUID PK), `event_id` (VARCHAR UNIQUE), `booking_id` (FK), `payment_reference`, `event_type`, `payload` (JSONB), `status`, `processed_at`.

---

## 7. Setup & Installation

### 1. Clone & create virtual environment
```powershell
git clone <repository_url>
cd EVE-Healthcare

python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

---

## 8. PostgreSQL Configuration
PostgreSQL 18 is required. Ensure two databases exist:
1. `eve_healthcare` (development database)
2. `eve_healthcare_test` (isolated integration testing database)

---

## 9. Environment Variables
Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```ini
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/eve_healthcare
TEST_DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/eve_healthcare_test
JWT_SECRET_KEY=supersecretjwtkeyforassignmentchangethisinproduction12345
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
WEBHOOK_SECRET=eve_mock_webhook_secret_key_2026
```

---

## 10. Alembic Migrations
Apply database migrations to the development database:
```powershell
alembic upgrade head
```

---

## 11. Running the Application
Start the development server with live reload:
```powershell
uvicorn app.main:app --reload --port 8000
```
The server will start at `http://127.0.0.1:8000`.

---

## 12. Running Tests
Run the complete test suite against `eve_healthcare_test`:
```powershell
pytest -v
```

---

## 13. Interactive API Documentation (Swagger)
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

---

## 14. API Endpoints

| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/signup` | Public | Register new user account |
| `POST` | `/api/v1/auth/login` | Public | Login and receive Bearer JWT |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Retrieve current user profile |
| `POST` | `/api/v1/centres` | Public | Create diagnostic centre |
| `GET` | `/api/v1/centres` | Public | List diagnostic centres |
| `GET` | `/api/v1/centres/{id}` | Public | Get diagnostic centre by ID |
| `POST` | `/api/v1/tests` | Public | Create diagnostic test |
| `GET` | `/api/v1/tests` | Public | List diagnostic tests |
| `GET` | `/api/v1/tests/{id}` | Public | Get diagnostic test by ID |
| `POST` | `/api/v1/centre-tests` | Public | Link centre and test with price |
| `GET` | `/api/v1/centre-tests` | Public | List test offerings with pricing |
| `GET` | `/api/v1/centre-tests/{id}`| Public | Get offering details |
| `POST` | `/api/v1/bookings` | Bearer JWT | Book a diagnostic test offering |
| `GET` | `/api/v1/bookings` | Bearer JWT | List current user's bookings |
| `GET` | `/api/v1/bookings/{id}` | Bearer JWT | Retrieve specific booking |
| `POST` | `/api/v1/bookings/{id}/cancel` | Bearer JWT | Cancel a PENDING booking |
| `POST` | `/api/v1/payments` | Bearer JWT | Simulate payment (SUCCESS / FAILED) |
| `GET` | `/api/v1/payments/{id}` | Bearer JWT | Retrieve payment details |
| `POST` | `/api/v1/payments/webhook` | `X-Webhook-Secret` | Idempotent payment webhook |

---

## 15. Example API Flow (cURL)

### 1. Register & Login
```bash
# Signup
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "password123"}'
# => {"access_token": "eyJ...", "token_type": "bearer", ...}
```

### 2. Create Catalogue Offerings
```bash
# Create Centre
curl -X POST "http://localhost:8000/api/v1/centres" \
  -H "Content-Type: application/json" \
  -d '{"name": "Metro Diagnostics", "location": "Bangalore"}'

# Create Test
curl -X POST "http://localhost:8000/api/v1/tests" \
  -H "Content-Type: application/json" \
  -d '{"name": "Complete Blood Count", "description": "Full blood panel"}'

# Link with price (Centre-Test Offering)
curl -X POST "http://localhost:8000/api/v1/centre-tests" \
  -H "Content-Type: application/json" \
  -d '{"centre_id": "<CENTRE_UUID>", "test_id": "<TEST_UUID>", "price": 450.00}'
```

### 3. Book Test
```bash
curl -X POST "http://localhost:8000/api/v1/bookings" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"centre_test_id": "<CENTRE_TEST_UUID>", "appointment_datetime": "2026-10-15T10:00:00Z"}'
# => Status: PENDING, amount: 450.00
```

### 4. Simulate Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"booking_id": "<BOOKING_UUID>", "simulate_outcome": "SUCCESS"}'
# => Payment created, booking transitions to CONFIRMED
```

### 5. Send Webhook Update
```bash
curl -X POST "http://localhost:8000/api/v1/payments/webhook" \
  -H "X-Webhook-Secret: eve_mock_webhook_secret_key_2026" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_987654321",
    "event_type": "payment.succeeded",
    "data": {
      "booking_id": "<BOOKING_UUID>",
      "payment_reference": "TXN_EXT_7788",
      "status": "SUCCESS",
      "amount": 450.00
    }
  }'
```

---

## 16. Booking State Transitions
Allowed transitions:
- `PENDING` → `CONFIRMED`: Upon successful payment.
- `PENDING` → `FAILED`: Upon failed payment attempt.
- `PENDING` → `CANCELLED`: User-initiated cancellation.
- `FAILED` → `PENDING`: Retry attempt on failed payment.

Terminal state protection:
- `CONFIRMED` bookings cannot be cancelled or marked failed. Duplicate success events are acknowledged (`200 OK`) as no-ops.
- `CANCELLED` bookings cannot receive payments or be confirmed.

---

## 17. Payment Safety
1. **Row-Level Locking**: `SELECT ... FOR UPDATE` locks the booking record during payment operations, serializing concurrent requests.
2. **Partial Unique Index**: PostgreSQL enforces `uq_one_success_payment_per_booking` on `payments(booking_id) WHERE status = 'SUCCESS'`. Even if concurrent threads bypass application checks, the database engine guarantees that at most one successful payment can exist for any booking.

---

## 18. Webhook Idempotency
- **Unique Event Ledger**: `payment_webhook_events(event_id UNIQUE)` records every event.
- **Atomic Concurrency Handling**: Incoming requests execute an atomic insert. Duplicate or concurrent deliveries trigger a conflict check and immediately return `200 OK` (`status: "ignored"`).
- **Amount & Booking Verification**: The payload amount must match `booking.amount`. Mismatched amounts are rejected (`400 Bad Request`) to prevent payment tampering.

---

## 19. Price Snapshot Behavior
When a user books a test, the server retrieves the current price from `centre_tests` and writes it into `bookings.amount`. If the centre later updates or raises the test price, existing booking records remain unchanged.

---

## 20. Authorization
- Each booking is strictly tied to `user_id`.
- Requests to view, cancel, or pay for a booking verify `booking.user_id == current_user.id`. Unauthorized attempts return `403 Forbidden`.

---

## 21. Assumptions
1. Diagnostic centres and tests can be created freely or by clinic staff; bookings are restricted to authenticated patient users.
2. Once a booking is `CONFIRMED`, cancellation and refund processing requires manual clinic intervention and is disallowed via self-serve API.
3. Webhook calls are authenticated using a shared secret transmitted in the `X-Webhook-Secret` header.

---

## 22. Future Improvements
1. Role-based access control (RBAC) separating administrative staff from patients.
2. Slot-based appointment capacity limits per diagnostic centre.
3. Automated refund workflow for clinic-initiated cancellations.
4. HMAC-SHA256 signature verification for webhook payloads.
