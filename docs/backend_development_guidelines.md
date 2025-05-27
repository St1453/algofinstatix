# Backend Development Guidelines

## Table of Contents
- [Project Instruction](#project-instruction)
- [Code Style](#code-style)
- [API Design](#api-design)
- [Database](#database)
- [Testing](#testing)
- [Security](#security)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)

## Project Instruction

### Project management
It is important to note that PRD(Product Requirements Document) is a document that outlines the requirements for a software project. It is a living document that is updated as the project progresses. Make a workflow that creates a PRD from scratch, chats with AI and updates the PRD as the project progresses.

### Directory Layout

```
backend/
├── src/
│   ├── shared/                  # Shared code across domains
│   │   ├── domain/              # Shared domain models and interfaces
│   │   └── infrastructure/      # Shared infrastructure (config, database, etc.)
│   │
│   └── {domain}/                # Domain-specific packages (e.g., users, orders)
│       ├── application/         # Application services and use cases
│       ├── domain/              # Domain models and business rules
│       │   ├── entities/        # Domain entities
│       │   ├── interfaces/      # Repository and service interfaces
│       │   └── schemas/         # Pydantic schemas for validation
│       ├── infrastructure/      # Infrastructure implementations
│       │   ├── models/          # SQLAlchemy ORM models
│       │   └── repositories/    # Repository implementations
│       └── presentation/        # API endpoints and controllers
│
├── tests/                      # Test files
│   ├── integration/             # Integration tests
│   └── unit/                    # Unit tests
│
└── alembic/                    # Database migrations
```

### Architecture Layers

1. **Domain Layer**
   - Contains business logic and rules
   - Defines entities, value objects, and domain services
   - Declares interfaces for external services
   - No infrastructure dependencies

2. **Application Layer**
   - Orchestrates domain objects to perform tasks
   - Implements use cases
   - Handles transactions and security
   - Depends on domain layer

3. **Infrastructure Layer**
   - Implements domain interfaces
   - Handles database operations
   - Manages external services
   - Depends on domain layer

4. **Presentation Layer**
   - Handles HTTP requests/responses
   - Validates input/output
   - Maps between DTOs and domain objects
   - Depends on application layer

### Key Principles

- **Bounded Contexts**: Each domain is a self-contained module
- **Dependency Rule**: Dependencies point inward (domain has no dependencies)
- **Separation of Concerns**: Clear boundaries between layers
- **Testability**: Each layer can be tested in isolation


### Layer Communication
The communication between layers follows these principles:

1. **Presentation → Application**
2. **Application → Domain**
3. **Application → Infrastructure**
4. **Infrastructure → Domain**


## Code Style

### Python Standards
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) strictly
- Maximum line length: 88 characters (enforced by Black)
- Use type hints (PEP 484) for all function signatures and variables
- Use Google-style docstrings for all public modules, classes, and functions
- Keep functions small and focused (max 30 lines)
- Use `snake_case` for variables and functions
- Use `PascalCase` for class names
- Use `UPPER_CASE` for constants
- Avoid global variables

### Code Organization
- Use absolute imports
- Group imports in this order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use `__all__` in `__init__.py` to define public API
- One class per file
- Keep related functions together

### Best Practices
- Follow SOLID principles
- Prefer composition over inheritance
- Use dataclasses for data containers
- Use pathlib for filesystem operations
- Use type annotations consistently
- Write pure functions when possible
- Use context managers for resource handling
- Implement `__str__` and `__repr__` for classes
- Use enums for fixed sets of values

## API Design

### RESTful Principles
- Use nouns instead of verbs in endpoints
- Use plural nouns for collections
- Use hyphens for multi-word path segments
- Use query parameters for filtering, sorting, and pagination
- Use proper HTTP methods:
  - `GET`: Retrieve resources (idempotent)
  - `POST`: Create resources
  - `PUT`: Update resources (full update, idempotent)
  - `PATCH`: Partial updates
  - `DELETE`: Remove resources (idempotent)

### Response Format

#### Success Response
```json
{
  "success": true,
  "data": {
    "id": "123",
    "name": "Example",
    "created_at": "2025-05-24T08:00:00Z"
  }
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource": "user",
      "id": "123"
    }
  }
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Success with no response body |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation errors |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Unexpected error |
| 503 | Service Unavailable - Service temporarily unavailable |

### Best Practices
- Use consistent naming conventions
- Version APIs through headers, not URLs
- Implement proper error handling
- Document all endpoints with OpenAPI/Swagger
- Use proper content negotiation
- Implement rate limiting
- Use proper caching headers
- Implement proper CORS policies
- Validate all inputs
- Sanitize all outputs

## Database

### Configuration

#### Environment Variables
```plaintext
# Database Configuration
POSTGRES_SERVER=127.0.0.1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=algofinstatix
POSTGRES_PORT=5432

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_ECHO=false
```

### Best Practices

#### SQLAlchemy ORM
- Use SQLAlchemy 2.0+ with async support
- Follow repository pattern for database access
- Use Alembic for database migrations
- Implement proper connection pooling
- Use transactions for write operations
- Implement proper indexing
- Use proper column types and constraints
- Add database-level constraints
- Document complex queries

#### Models
- Use `mapped_column` for column definitions
- Add proper indexes
- Implement `__tablename__` explicitly
- Use proper relationship definitions
- Add `__repr__` for debugging
- Use proper cascade rules
- Implement soft deletes with `is_deleted` flag
- Add audit fields (created_at, updated_at, deleted_at)

#### Queries
- Use parameterized queries
- Avoid N+1 query problems
- Use proper joins
- Implement pagination
- Use proper filtering
- Implement proper sorting
- Use proper locking when needed
- Implement proper error handling

## Testing

### Test Structure
```
tests/
├── conftest.py           # Test fixtures
├── integration/         # Integration tests
│   └── test_*.py
└── unit/                # Unit tests
    └── test_*.py
```

### Unit Tests
- Test one thing per test case
- Use descriptive test names
- Use fixtures for test data
- Mock external dependencies
- Test edge cases
- Test error conditions
- Keep tests fast and isolated
- Use proper assertions

### Integration Tests
- Test API endpoints
- Test database operations
- Test external service integrations
- Test authentication/authorization
- Test error responses
- Test rate limiting
- Test validation
- Test security headers

### Test Data
- Use factories for test data
- Use fixtures for common test setups
- Clean up test data
- Use proper test isolation
- Use proper test databases
- Use proper test transactions
- Implement proper test teardown

### Test Coverage
- Aim for high test coverage
- Test edge cases
- Test error conditions
- Test boundary conditions
- Test race conditions
- Test performance
- Test security
- Test documentation

## Error Handling

### Error Types
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {}
  }
}
```

### Best Practices
- Use custom exception classes
- Log detailed error information server-side
- Handle database errors gracefully
- Implement proper HTTP status codes
- Include error codes for programmatic handling
- Sanitize error messages in production
- Document all possible error responses
- Implement proper error boundaries

## Best Practices

### Code Quality
- Follow SOLID principles
- Write clean, maintainable code
- Keep functions small and focused (max 30 lines)
- Use meaningful, descriptive names
- Write self-documenting code
- Follow the DRY principle
- Keep code style consistent
- Document complex logic

### Performance
- Optimize database queries
- Implement proper caching (Redis)
- Use connection pooling
- Implement pagination for large datasets
- Use background tasks for long operations
- Optimize response sizes
- Implement rate limiting
- Monitor and optimize performance

### Documentation
- Keep README up to date
- Document all public APIs
- Document database schema
- Document environment variables
- Document deployment process
- Document testing strategy
- Document security considerations
- Document operational procedures

### Team Workflow
- Use feature branches (`feature/description`)
- Write meaningful commit messages
- Create small, focused PRs
- Request code reviews
- Address review feedback promptly
- Keep PRs up to date with main
- Write tests for new features
- Document breaking changes in PRs

### Global Error Handling
- Use FastAPI's exception handlers for consistent error responses
- Implement custom exception classes in `shared/errors/exceptions.py`
- Always return structured error responses:
  ```json
  {
    "success": false,
    "error": {
      "code": "ERROR_CODE",
      "message": "User-friendly error message"
    }
  }
  ```

### Local Error Handling
- Use domain-specific exceptions for business logic errors
- Validate inputs using Pydantic models
- Use context managers for resource cleanup
- Log all errors with appropriate severity levels

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {}
  }
}
```

### Exception Hierarchy
- `BaseError`: Base exception for all custom errors
  - `ValidationError`: Input validation failed
  - `AuthenticationError`: Authentication failed
  - `AuthorizationError`: Permission denied
  - `NotFoundError`: Resource not found
  - `ConflictError`: Resource conflict
  - `RateLimitError`: Rate limit exceeded
  - `ServiceError`: Internal server error

### Best Practices
- Use specific error types for different error cases
- Include helpful error messages for client applications
- Log detailed error information server-side
- Handle database errors gracefully
- Implement proper HTTP status codes
