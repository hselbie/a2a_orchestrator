# Testing Guide

This document provides comprehensive guidance on testing the A2A Dynamic Orchestrator system.

## Table of Contents

- [Overview](#overview)
- [Test Infrastructure](#test-infrastructure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Code Coverage](#code-coverage)
- [Code Quality](#code-quality)
- [CI/CD Pipeline](#cicd-pipeline)

## Overview

The test suite provides comprehensive coverage of core system components:

- **Registry Service**: Agent registration, heartbeat monitoring, cleanup
- **Planning Tools**: Intent extraction, agent scoring, execution planning
- **Integration Tests**: End-to-end system validation

### Test Statistics

- **Total Tests**: 46
- **Test Coverage**: 40% overall
  - Registry Service: 93%
  - Planning Tools: 83%
- **Test Framework**: pytest with async support

## Test Infrastructure

### Dependencies

All testing dependencies are defined in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
    "httpx>=0.27.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
    "black>=24.8.0",
]
```

### Installing Test Dependencies

```bash
# Install all dependencies including dev/test tools
uv sync --extra dev
```

### Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--verbose",
    "--cov=.",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-report=xml",
]
```

### Fixtures

Shared test fixtures are defined in `tests/conftest.py`:

- `registry`: Fresh InMemoryAgentRegistry instance
- `registry_client`: FastAPI TestClient for registry
- `sample_agent_card`: Mock weather agent configuration
- `sample_cocktail_agent_card`: Mock cocktail agent configuration
- `mock_weather_response`: Mock weather API response
- `mock_cocktail_response`: Mock cocktail API response

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=. --cov-report=html
```

### Run Specific Tests

```bash
# Run registry tests only
uv run pytest tests/test_registry.py -v

# Run planning tools tests only
uv run pytest tests/test_planning_tools.py -v

# Run specific test class
uv run pytest tests/test_registry.py::TestInMemoryAgentRegistry -v

# Run specific test method
uv run pytest tests/test_registry.py::TestInMemoryAgentRegistry::test_register_agent -v
```

### Run with Coverage

```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html

# Generate terminal coverage report
uv run pytest tests/ --cov=. --cov-report=term-missing
```

### Run System Integration Tests

```bash
# Prerequisites: Start all services first
# Terminal 1: uv run python -m registry_service.start
# Terminal 2: uv run python weather_agent/start.py
# Terminal 3: uv run python cocktail_agent/start.py
# Terminal 4: uv run python -m planning_orchestrator.start

# Then run system tests
uv run python tests/test_system.py
```

## Writing Tests

### Test Structure

```python
"""
Module docstring explaining what's being tested.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestComponentName:
    """Test suite for ComponentName."""

    def test_basic_functionality(self):
        """Test description."""
        # Arrange
        expected = "value"

        # Act
        result = function_under_test()

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

### Using Fixtures

```python
def test_with_registry(registry_client):
    """Test using the registry_client fixture."""
    response = registry_client.get("/health")
    assert response.status_code == 200
```

### Mocking External Dependencies

```python
@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked aiohttp session."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"key": "value"})

    with patch("module.get_session", return_value=mock_session):
        result = await function_that_makes_requests()
        assert result is not None
```

### Test Best Practices

1. **Arrange-Act-Assert Pattern**: Structure tests clearly
2. **Descriptive Names**: Use clear, descriptive test names
3. **One Assertion Per Concept**: Focus each test on one behavior
4. **Use Fixtures**: Leverage shared fixtures for common setup
5. **Mock External Calls**: Mock HTTP requests, database calls, etc.
6. **Test Edge Cases**: Include negative tests and edge cases
7. **Async Tests**: Use `@pytest.mark.asyncio` for async code

## Code Coverage

### Current Coverage

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
registry_service/fastapi_registry.py      149     11    93%
planning_orchestrator/planning_tools.py   147     25    83%
-----------------------------------------------------------
TOTAL                                     647    387    40%
```

### Coverage Goals

- **Core Components**: 80%+ coverage (registry, planning tools)
- **Overall Project**: 40%+ coverage
- **Critical Paths**: 100% coverage for registration, routing

### Viewing Coverage Reports

```bash
# Generate HTML report
uv run pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal report
uv run pytest --cov=. --cov-report=term-missing
```

### Coverage Configuration

Configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["."]
omit = [
    "*/tests/*",
    "*/.venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
]
```

## Code Quality

### Linting with Ruff

```bash
# Check code
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Check specific file
uv run ruff check registry_service/fastapi_registry.py
```

### Formatting with Black

```bash
# Format all code
uv run black .

# Check formatting without changes
uv run black . --check

# Format specific file
uv run black registry_service/fastapi_registry.py
```

### Type Checking with Mypy

```bash
# Run type checker
uv run mypy .

# Check specific file
uv run mypy registry_service/fastapi_registry.py

# Strict mode
uv run mypy . --strict
```

### Running All Quality Checks

```bash
# Run all checks
uv run ruff check . &&
  uv run black . --check &&
  uv run mypy .
```

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes a comprehensive CI/CD pipeline (`.github/workflows/ci.yml`) that runs on every push and pull request:

#### Jobs

1. **Test Suite**
   - Runs on Python 3.13
   - Executes all tests with coverage
   - Uploads coverage to Codecov
   - Caches dependencies for faster runs

2. **Code Quality**
   - Runs ruff linter
   - Checks black formatting
   - Runs mypy type checker

3. **Security Scan**
   - Trivy vulnerability scanner
   - Uploads results to GitHub Security tab

### Running CI Locally

```bash
# Simulate CI test job
uv sync --extra dev
uv run pytest tests/ --cov=. --cov-report=xml -v

# Simulate code quality job
uv run ruff check .
uv run black . --check
uv run mypy .
```

### CI Configuration

The CI pipeline is configured to:
- Run on pushes to `main` and `develop` branches
- Run on all pull requests
- Cache dependencies for faster execution
- Generate and upload coverage reports
- Perform security scanning

### Status Badges

Add these to your README.md:

```markdown
[![CI](https://github.com/username/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/username/repo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in the project root
cd a2a_orchestrator/

# Reinstall dependencies
uv sync --extra dev
```

**Async Test Failures**
```python
# Ensure async tests use the decorator
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

**Coverage Too Low**
```bash
# Run with detailed missing lines report
uv run pytest --cov=. --cov-report=term-missing

# Focus on specific modules
uv run pytest --cov=registry_service --cov=planning_orchestrator
```

**Fixture Not Found**
```python
# Ensure fixture is defined in conftest.py or imported properly
from tests.conftest import sample_agent_card
```

## Best Practices Summary

1. ✅ Run tests before committing
2. ✅ Write tests for new features
3. ✅ Maintain 80%+ coverage for core components
4. ✅ Use descriptive test names
5. ✅ Mock external dependencies
6. ✅ Test edge cases and error conditions
7. ✅ Keep tests fast and focused
8. ✅ Use CI/CD for automated testing
9. ✅ Review coverage reports regularly
10. ✅ Fix linting and typing issues

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Black](https://black.readthedocs.io/)
- [Mypy](https://mypy.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
