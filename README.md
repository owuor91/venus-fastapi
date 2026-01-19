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
- Photo model for user photo uploads with AWS S3 integration
- GenderEnum for gender selection (MALE, FEMALE)
- Soft delete support via `active` field
- Pydantic schemas for request/response validation
- AWS S3 integration for photo storage

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
│   │   ├── profile.py          # Profile model (profile_id as primary key, one-to-one with User)
│   │   ├── match.py            # Match model (match_id as primary key)
│   │   └── photo.py            # Photo model (photo_id as primary key)
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py             # User schemas (RegisterRequest, LoginRequest, etc.)
│   │   ├── profile.py          # Profile schemas (ProfileCompletionRequest, etc.)
│   │   ├── match.py            # Match schemas (MatchCreateRequest, Match, etc.)
│   │   ├── photo.py            # Photo schemas (Photo, etc.)
│   │   └── token.py            # Token schemas (LoginResponse, etc.)
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, database session)
│   │   └── v1/                 # API v1 routes
│   │       ├── __init__.py
│   │       ├── auth.py         # Authentication endpoints (register, login, profile completion)
│   │       ├── matches.py      # Match endpoints
│   │       └── photos.py       # Photo upload endpoints
│   └── core/                   # Core functionality
│       ├── __init__.py
│       ├── security.py         # JWT and password hashing
│       ├── config.py           # Application settings
│       └── s3_helper.py        # AWS S3 upload helper functions
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

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed on your system

### Quick Start with Docker

1. **Build and start services**:
   ```bash
   docker-compose up --build
   # or with newer Docker: docker compose up --build
   ```
   
   **Note:** Database migrations run automatically on container startup. The entrypoint script waits for the database to be ready, then runs `alembic upgrade head` before starting the FastAPI server.

2. **Access the API**:
   - API: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Docker Commands

- **Start services in background**:
  ```bash
  docker-compose up -d
  # or: docker compose up -d
  ```

- **View logs**:
  ```bash
  docker-compose logs -f web
  # or: docker compose logs -f web
  ```

- **Stop services**:
  ```bash
  docker-compose down
  # or: docker compose down
  ```

- **Stop and remove volumes** (clears database data):
  ```bash
  docker-compose down -v
  # or: docker compose down -v
  ```

- **Run migrations manually** (migrations run automatically on startup, but you can run them manually if needed):
  ```bash
  docker-compose exec web alembic upgrade head
  # or: docker compose exec web alembic upgrade head
  ```

- **Create a new migration**:
  ```bash
  docker-compose exec web alembic revision --autogenerate -m "Description"
  # or: docker compose exec web alembic revision --autogenerate -m "Description"
  ```

- **Access database**:
  ```bash
  docker-compose exec db psql -U venus_fastapi -d venus_fastapi
  # or: docker compose exec db psql -U venus_fastapi -d venus_fastapi
  ```

- **Run tests**:
  ```bash
  docker-compose exec web pytest
  # or: docker compose exec web pytest
  ```

### Environment Variables

The docker-compose.yml supports environment variables from your `.env` file. Make sure your `.env` file includes:

```env
# Database (used by docker-compose for PostgreSQL service)
POSTGRES_USER=venus_fastapi
POSTGRES_PASSWORD=
POSTGRES_DB=venus_fastapi

# Application (used by FastAPI app)
DATABASE_URL=postgresql://venus_fastapi@db:5432/venus_fastapi
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
MAX_PHOTO_SIZE_MB=10
```

**Note:** The `DATABASE_URL` in docker-compose uses `db` as the hostname (the PostgreSQL service name) instead of `localhost`.

### Development vs Production

**Development mode (current docker-compose.yml):**
- Connects to host's PostgreSQL via `host.docker.internal`
- Uses the same database as local development
- Code is mounted as volume (changes reflect immediately)
- `.env` file is mounted
- Hot-reload enabled (`--reload` flag)
- Changes persist because both local and Docker use the same database

**Production mode (use docker-compose.prod.yml):**
- Uses separate PostgreSQL container (isolated database)
- No volume mounts for code (code baked into image)
- No `--reload` flag (uses multiple workers)
- Database data persists in Docker volume
- Use environment variables or secrets management
- Multiple workers for better performance
- Use: `docker compose -f docker-compose.prod.yml up -d`

**For Managed Database (AWS RDS, Cloud SQL, etc.):**
- Don't include `db` service in docker-compose
- Set `DATABASE_URL` to your managed database connection string
- Example: `DATABASE_URL=postgresql://user:pass@rds-instance.region.rds.amazonaws.com:5432/dbname`

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

### Photos

- **POST** `/api/v1/photos` - Upload a photo to S3
  - Requires authentication
  - Request: Multipart form data with field name `image`
  - Accepted file types: `png`, `jpg`, `jpeg`, `gif`
  - Maximum file size: 10MB (configurable via `MAX_PHOTO_SIZE_MB` in `.env`)
  - Note: `user_id` is automatically set from the authenticated user
  - Note: `created_by` and `updated_by` are automatically set to the authenticated user's user_id
  - Returns: Photo object with `photo_url` (public S3 URL)
  - The uploaded photo is stored in S3 at: `users/{user_id}/photos/{photo_id}.{ext}`
  - Photos are uploaded with `public-read` ACL for public access

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

### Photo Model

The Photo model (`app/models/photo.py`) includes:
- `photo_id`: UUID (primary key)
- `user_id`: UUID (foreign key to User, required)
- `photo_url`: String (required, S3 URL of the uploaded photo)
- `verified`: Boolean (default: False)
- `user`: Relationship to User model
- Inherits all BaseModel fields

**Features:**
- Photos are uploaded to AWS S3 with public-read ACL
- S3 path structure: `users/{user_id}/photos/{photo_id}.{ext}`
- File validation: only png, jpg, jpeg, gif allowed
- File size limit: configurable (default 10MB)

## Development

### Code Structure

- `app/models/`: SQLAlchemy database models
  - `base.py`: BaseModel with common fields
  - `enums.py`: GenderEnum
  - `user.py`: User model
  - `profile.py`: Profile model
  - `match.py`: Match model
  - `photo.py`: Photo model
- `app/schemas/`: Pydantic schemas for request/response validation
  - `user.py`: User schemas (RegisterRequest, LoginRequest, User, etc.)
  - `profile.py`: Profile schemas (ProfileCompletionRequest, Profile, etc.)
  - `match.py`: Match schemas (MatchCreateRequest, Match, etc.)
  - `photo.py`: Photo schemas (Photo, etc.)
  - `token.py`: Token schemas (LoginResponse, Token, etc.)
- `app/api/`: API route handlers
  - `deps.py`: Dependencies (database session, authentication)
  - `v1/auth.py`: Authentication endpoints
  - `v1/matches.py`: Match endpoints
  - `v1/photos.py`: Photo upload endpoints
- `app/core/`: Core functionality (config, security, S3)
  - `config.py`: Application settings (database, JWT, AWS S3)
  - `security.py`: JWT and password hashing
  - `s3_helper.py`: AWS S3 upload helper functions
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
- `tests/test_photos.py` - Tests for photo upload endpoints
- `tests/conftest.py` - Shared test fixtures and configuration

Tests use an in-memory SQLite database for fast, isolated test execution.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
