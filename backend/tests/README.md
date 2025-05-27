# Test Suite

This directory contains the test suite for the AlgoFinStatiX backend.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared test fixtures and configurations
├── integration/          # Integration tests
│   └── test_*.py        # Test files for integration tests
├── unit/                 # Unit tests
│   └── test_*.py        # Test files for unit tests
└── utils/                # Test utilities
    └── test_*.py        # Utility test files
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Category
```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run utility tests
pytest tests/utils/
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=term-missing
```

## Writing Tests

- **Unit Tests**: Test individual components in isolation.
- **Integration Tests**: Test interactions between components.
- **Fixtures**: Use `conftest.py` for shared test fixtures.
- **Naming**: Follow `test_*.py` for test files and `test_*` for test functions.
- **Async Tests**: Use `pytest.mark.asyncio` for async test functions.

## Dependencies

- `pytest`: Test framework
- `pytest-asyncio`: For async test support
- `httpx`: For async HTTP client
- `pytest-cov`: For test coverage reporting

Add test dependencies to `pyproject.toml`.
