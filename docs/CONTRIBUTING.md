# Contributing to Salon Assistant

Thank you for considering contributing to Salon Assistant! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment](#development-environment)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Submitting Changes](#submitting-changes)
8. [Pull Request Process](#pull-request-process)
9. [Versioning](#versioning)
10. [Documentation](#documentation)
11. [Getting Help](#getting-help)

## Code of Conduct

Our project adopts a Code of Conduct that we expect project participants to adhere to. Please read the [full text](CODE_OF_CONDUCT.md) to understand what actions will and will not be tolerated.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- Git
- Docker and Docker Compose (recommended for local development)

### Project Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/salon-assistant.git
   cd salon-assistant
   ```
3. Add the original repository as an upstream remote:
   ```bash
   git remote add upstream https://github.com/original-owner/salon-assistant.git
   ```
4. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
7. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```
8. Configure your local environment:
   ```bash
   cp .env.example .env
   # Edit .env with appropriate values for development
   ```
9. Run database migrations:
   ```bash
   alembic upgrade head
   ```
10. Start the development server:
    ```bash
    uvicorn app.main:app --reload
    ```

## Development Environment

### Recommended Tools

- **IDE**: VSCode with Python and FastAPI extensions
- **Database Client**: DBeaver or pgAdmin for PostgreSQL
- **API Testing**: Postman or Insomnia
- **Container Management**: Docker Desktop

### Environment Variables

Key environment variables for development:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `LOG_LEVEL`: Set to DEBUG during development
- `ENVIRONMENT`: Set to development

See the `.env.example` file for a complete list of environment variables.

## Development Workflow

We follow a standard GitHub flow:

1. Create a new branch for each feature or bugfix
2. Implement your changes with appropriate tests
3. Submit a pull request to the main repository

### Branch Naming Convention

Use the following branch naming convention:
- `feature/short-description` - For new features
- `bugfix/issue-number-short-description` - For bug fixes
- `docs/short-description` - For documentation changes
- `refactor/short-description` - For code refactoring

### Commit Messages

Write clear, concise commit messages following these guidelines:
- Use the imperative mood ("Add feature" not "Added feature")
- First line is 50 characters or less
- Reference issues or pull requests when relevant
- Provide detailed description in the body when necessary

Example:
```
Add client notification preferences

- Add database model for storing preferences
- Create API endpoints for managing preferences
- Add service layer for preference processing
- Update documentation

Fixes #123
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:
- Line length: 88 characters (conforming to Black defaults)
- Use double quotes for strings unless you're avoiding escaping single quotes
- Use snake_case for variables, functions, and modules
- Use PascalCase for classes

### Type Hinting

Use type hints for all function definitions:

```python
def get_client_by_id(client_id: int) -> Optional[Client]:
    """
    Retrieve a client by ID.
    
    Args:
        client_id: The unique identifier of the client
        
    Returns:
        The client object if found, None otherwise
    """
    # function implementation
```

### Documentation

All modules, classes, and functions should have docstrings following the Google style:

```python
def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.
    """
```

### Code Formatting

We use the following tools to enforce code style:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run the formatting tools before submitting changes:
```bash
black app tests
isort app tests
flake8 app tests
mypy app
```

## Testing Guidelines

### Test Structure

- Tests should be organized in the `tests/` directory
- Maintain a parallel structure to the `app/` directory
- Use pytest fixtures for test setup and teardown
- Follow a naming convention: `test_<what is being tested>.py`

### Types of Tests

Write tests for:
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test interactions between components
- **API Tests**: Test API endpoints
- **End-to-End Tests**: Test complete workflows

### Running Tests

Run the test suite with pytest:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/v1/endpoints/test_clients.py

# Run tests with coverage report
pytest --cov=app
```

### Test Coverage

Aim for high test coverage, especially for critical components:
- Service layer: 90%+ coverage
- API endpoints: 85%+ coverage
- Models: 80%+ coverage

## Submitting Changes

### Before Submitting

Before submitting a pull request, ensure:
1. Your code passes all tests
2. You've added tests for new functionality
3. Your code passes linting and type checking
4. You've updated documentation as needed
5. You've followed the coding standards

### Pull Request Process

1. Create a pull request from your feature branch to the main repository's main branch
2. Fill in the PR template with all relevant information
3. Link any related issues
4. Request review from appropriate team members
5. Address any feedback from reviewers
6. Once approved, your changes will be merged by a maintainer

## Versioning

We use [Semantic Versioning](https://semver.org/) for versioning:
- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality additions
- PATCH version for backward-compatible bug fixes

## Documentation

### API Documentation

When adding or modifying API endpoints:
1. Update the docstrings with proper descriptions
2. Include appropriate status codes and response formats
3. Document request body schemas
4. Document authentication requirements

FastAPI automatically generates OpenAPI documentation from these docstrings.

### Project Documentation

Update the relevant markdown files in the `docs/` directory when making significant changes:
- `README.md` - Overview of the project
- `docs/README.md` - Detailed project documentation
- `docs/DEPLOYMENT.md` - Deployment instructions
- Other specific documentation files as needed

## Getting Help

If you need help or have questions:
1. Check the existing documentation
2. Look for similar issues in the issue tracker
3. Create a new issue with the "question" label
4. Reach out to the project maintainers

---

Thank you for contributing to Salon Assistant! Your efforts help improve the system for everyone. 