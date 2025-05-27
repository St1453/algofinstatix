# Users Module

This module handles all user related functionality following Domain-Driven Design (DDD) principles, including authentication and authorization.

## Project management
It is important to note that PRD(Product Requirements Document) is a document that outlines the requirements for a software project. It is a living document that is updated as the project progresses. Make a workflow that creates a PRD from scratch, chats with AI and updates the PRD as the project progresses.

## Directory Structure
- `application/`: Application services that orchestrate the flow of data.
  - `use_cases/`: Authentication and user management use cases
  - `dtos/`: Data transfer objects for requests/responses
- `domain/`: Core business logic, entities, value objects, and domain services.
  - `entities/`: Core domain models (User, etc.)
  - `value_objects/`: Domain-specific value objects
  - `interfaces/`: Repository and service interfaces
  - `services/`: Domain services (Authentication, Token, etc.)
- `infrastructure/`: Implementation details and external concerns.
  - `repositories/`: Database implementations
  - `services/`: External service integrations (JWT, Password Hashing)
  - `security/`: Security-related implementations
- `presentation/`: API endpoints and request/response models.
  - `routes/`: API route definitions
  - `schemas/`: Pydantic models for requests/responses
  - `dependencies/`: FastAPI dependencies

## Authentication

### Security Implementation
- **Password Hashing**: Uses `passlib` with `bcrypt` for secure password storage
- **JWT Tokens**: Uses `python-jose` with `cryptography` for token generation/validation
- **Token Types**:
  - Access Token (short-lived, 15-30 minutes)
  - Refresh Token (long-lived, 7-30 days)

### Authentication Flows
1. **Login**
   - Verify credentials
   - Generate access and refresh tokens
   - Store refresh token hash in database

2. **Token Refresh**
   - Validate refresh token
   - Issue new access token
   - Optionally rotate refresh token

3. **Logout**
   - Invalidate refresh token
   - Add to token blacklist if needed

### Security Best Practices
- All passwords are hashed using bcrypt
- Tokens are signed with RS256 (asymmetric encryption)
- Refresh tokens are stored as hashed values
- Token blacklisting for immediate revocation
- Secure cookie settings (httpOnly, secure, sameSite)
- Rate limiting on authentication endpoints
- Input validation on all endpoints

## Layer Structure and Communication

The communication between layers follows these principles:

1. **Presentation → Application**
   - Handles HTTP/API concerns
   - Validates input data
   - Transforms DTOs to domain models

2. **Application → Domain**
   - Handles transactions
   - Orchestrates domain logic
   - Manages domain events

3. **Application → Infrastructure**
   - Depends on interfaces
   - Uses dependency injection
   - Handles cross-cutting concerns
   - Manages external service calls

4. **Infrastructure → Domain**
   - Implements domain interfaces
   - Handles persistence
   - Manages external services
   - Implements security concerns
