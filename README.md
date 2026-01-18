# Venus Dating App API

A REST API for a dating app built with FastAPI, PostgreSQL, Alembic, and JWT authentication.

## Features

- FastAPI framework for high performance
- PostgreSQL database with SQLAlchemy ORM
- Alembic for database migrations
- JWT authentication
- BaseModel with common fields (date_created, date_updated, created_by, updated_by, active, meta)
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
│   │   ├── base.py            # BaseModel (common fields for all models)
│   │   └── user.py             # User model
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py             # User schemas
│   │   └── token.py            # Token schemas
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, database session)
│   │   └── v1/                 # API v1 routes
│   │       ├── __init__.py
│   │       └── auth.py         # Authentication endpoints
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
  - Request body: `{"email": "user@example.com", "password": "password", "created_by": "system", "updated_by": "system"}`
  - Returns: User object

- **POST** `/api/v1/auth/login` - Login and get access token
  - Form data: `username` (email), `password`
  - Returns: `{"access_token": "...", "token_type": "bearer"}`

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

All models inherit from `BaseModel` which provides:

- `date_created`: DateTime (timezone-aware), automatically set on creation
- `date_updated`: DateTime (timezone-aware), automatically updated on record changes
- `created_by`: String, tracks who created the record
- `updated_by`: String, tracks who last updated the record
- `active`: Boolean, default `True` (for soft deletes)
- `meta`: JSON, default `{}`, nullable (for extensibility)

## Development

### Code Structure

- `app/models/`: SQLAlchemy database models
- `app/schemas/`: Pydantic schemas for request/response validation
- `app/api/`: API route handlers
- `app/core/`: Core functionality (config, security)
- `app/database.py`: Database connection and session management

### Running Tests

(Add test instructions when tests are added)

## License

(Add your license here)
