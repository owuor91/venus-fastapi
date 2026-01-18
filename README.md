# Venus Dating App API

A REST API for a dating app built with FastAPI, PostgreSQL, Alembic, and JWT authentication.

## Features

- FastAPI framework for high performance
- PostgreSQL database with SQLAlchemy ORM
- Alembic for database migrations
- JWT authentication
- BaseModel with common fields (date_created, date_updated, created_by, updated_by, active, meta)
  - Note: BaseModel does not include an `id` field; each model defines its own primary key (e.g., user_id, profile_id)
- User model with authentication fields (user_id, first_name, last_name, email, avatar_url, fcm_token)
- Profile model with one-to-one relationship to User (phone_number, gender, date_of_birth, bio, online)
- GenderEnum for gender selection (MALE, FEMALE)
- Soft delete support via `active` field
- Pydantic schemas for request/response validation

## Project Structure

```
venus-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database connection and session management
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py            # BaseModel (common fields for all models, no id field)
│   │   ├── enums.py           # GenderEnum (MALE, FEMALE)
│   │   ├── user.py             # User model (user_id as primary key)
│   │   └── profile.py          # Profile model (profile_id as primary key, one-to-one with User)
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py             # User schemas (RegisterRequest, LoginRequest, etc.)
│   │   ├── profile.py          # Profile schemas (ProfileCompletionRequest, etc.)
│   │   └── token.py            # Token schemas (LoginResponse, etc.)
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, database session)
│   │   └── v1/                 # API v1 routes
│   │       ├── __init__.py
│   │       └── auth.py         # Authentication endpoints (register, login, profile completion)
│   └── core/                   # Core functionality
│       ├── __init__.py
│       ├── security.py         # JWT and password hashing
│       └── config.py           # Settings management
├── alembic/                    # Alembic configuration
│   ├── versions/               # Migration versions
│   ├── env.py
│   └── script.py.mako
├── alembic.ini                 # Alembic configuration file
├── .env.example                # Environment variables example
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd venus-fastapi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: A secure secret key for JWT tokens (generate a strong random string)
   - `ALGORITHM`: JWT algorithm (default: HS256)
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time in minutes (default: 30)

5. **Create the PostgreSQL database**:
   ```bash
   createdb venus_db  # or use your preferred method
   ```

6. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

7. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

- **POST** `/api/v1/auth/register` - Register a new user
  - Request body (JSON): 
    ```json
    {
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "password": "password"
    }
    ```
  - Note: `created_by` and `updated_by` are automatically set to the user's email
  - Returns: User object (without password)

- **POST** `/api/v1/auth/login` - Login and get access token
  - Request body (JSON):
    ```json
    {
      "email": "user@example.com",
      "password": "password"
    }
    ```
  - Returns:
    ```json
    {
      "access_token": "...",
      "token_type": "bearer",
      "user_id": "uuid-here",
      "first_name": "John",
      "last_name": "Doe",
      "email": "user@example.com",
      "profile": null
    }
    ```
  - Note: `profile` will be `null` if the user hasn't completed their profile

- **POST** `/api/v1/auth/profile/complete` - Complete or update user profile
  - Requires authentication
  - Request body (JSON):
    ```json
    {
      "phone_number": "+1234567890",
      "gender": "MALE",
      "date_of_birth": "1990-05-15",
      "bio": "User bio here"
    }
    ```
  - Note: `gender` must be either `"MALE"` or `"FEMALE"`
  - Note: `created_by` and `updated_by` are automatically set to the authenticated user's user_id
  - Returns: Profile object
  - If profile already exists, it will be updated; otherwise, a new profile will be created

### Matches

- **POST** `/api/v1/matches` - Create or update a match
  - Requires authentication
  - Request body (JSON):
    ```json
    {
      "my_id": "uuid-here",
      "partner_id": "uuid-here",
      "thread_id": "uuid-here",
      "last_message": "Optional message text",
      "last_message_date": "2026-01-18T12:00:00Z",
      "sent_by": "uuid-here"
    }
    ```
  - Required fields: `my_id`, `partner_id`, `thread_id`
  - Optional fields: `last_message`, `last_message_date`, `sent_by`
  - Note: `my_id` must match the authenticated user's `user_id`
  - Note: `created_by` and `updated_by` are automatically set to the authenticated user's user_id
  - Returns: Match object
  - If a match with the same (`my_id`, `partner_id`, `thread_id`) already exists, it will be updated; otherwise, a new match will be created

- **GET** `/api/v1/matches` - Get all active matches for the authenticated user
  - Requires authentication
  - Returns: Array of Match objects
  - Returns all active matches where the current user is either `my_id` or `partner_id`
  - Only returns matches where `active == True`

### Protected Endpoints

All protected endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

## BaseModel

All models inherit from `BaseModel` which provides common fields. Note that `BaseModel` does **not** include an `id` field - each model must define its own primary key (e.g., `user_id`, `profile_id`).

### BaseModel Fields

- `date_created`: DateTime (timezone-aware), automatically set on creation
- `date_updated`: DateTime (timezone-aware), automatically updated on record changes
- `created_by`: String, tracks who created the record
  - For unauthenticated requests (e.g., registration): set to user's email
  - For authenticated requests: set to user's user_id (UUID as string)
- `updated_by`: String, tracks who last updated the record
  - For unauthenticated requests: set to user's email
  - For authenticated requests: set to user's user_id (UUID as string)
- `active`: Boolean, default `True` (for soft deletes)
- `meta`: JSON, default `{}` (new dict instance per record), nullable (for extensibility)

## Models

### User Model

The User model (`app/models/user.py`) includes:
- `user_id`: UUID (primary key)
- `first_name`: String (required)
- `last_name`: String (required)
- `email`: String (unique, indexed, required)
- `avatar_url`: String (nullable)
- `fcm_token`: String (nullable, for push notifications)
- `hashed_password`: String (required)
- `profile`: One-to-one relationship with Profile model
- Inherits all BaseModel fields

### Profile Model

The Profile model (`app/models/profile.py`) includes:
- `profile_id`: UUID (primary key)
- `user_id`: UUID (foreign key to User, unique - enforces one-to-one relationship)
- `phone_number`: String (unique, required)
- `gender`: String (required, stores GenderEnum value: "MALE" or "FEMALE")
- `date_of_birth`: Date (required)
- `bio`: String (required)
- `online`: Boolean (default: True)
- `user`: Relationship back to User model
- Inherits all BaseModel fields

**Constraints:**
- One-to-one relationship with User (enforced by unique constraint on `user_id`)
- `phone_number` must be unique across all profiles

## Development

### Code Structure

- `app/models/`: SQLAlchemy database models
  - `base.py`: BaseModel with common fields
  - `enums.py`: GenderEnum
  - `user.py`: User model
  - `profile.py`: Profile model
- `app/schemas/`: Pydantic schemas for request/response validation
  - `user.py`: User schemas (RegisterRequest, LoginRequest, User, etc.)
  - `profile.py`: Profile schemas (ProfileCompletionRequest, Profile, etc.)
  - `token.py`: Token schemas (LoginResponse, Token, etc.)
- `app/api/`: API route handlers
  - `deps.py`: Dependencies (database session, authentication)
  - `v1/auth.py`: Authentication endpoints
- `app/core/`: Core functionality (config, security)
- `app/database.py`: Database connection and session management

### Running Tests

The project uses `pytest` for testing. To run tests:

1. **Install test dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run all tests**:
   ```bash
   pytest
   ```

3. **Run tests with coverage**:
   ```bash
   pytest --cov=app --cov-report=html
   ```

4. **Run specific test file**:
   ```bash
   pytest tests/test_auth.py
   ```

5. **Run specific test**:
   ```bash
   pytest tests/test_auth.py::TestRegistration::test_register_all_params_present
   ```

**Test Structure:**
- `tests/test_auth.py` - Tests for registration and login endpoints
- `tests/test_profile.py` - Tests for profile completion endpoint
- `tests/test_matches.py` - Tests for matches endpoints
- `tests/conftest.py` - Shared test fixtures and configuration

Tests use an in-memory SQLite database for fast, isolated test execution.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
