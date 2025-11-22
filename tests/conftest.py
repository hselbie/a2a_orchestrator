"""
Pytest configuration and shared fixtures for the A2A Dynamic Orchestrator.

This module provides reusable fixtures for testing all components of the system.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

from registry_service.fastapi_registry import InMemoryAgentRegistry, app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def registry() -> AsyncGenerator[InMemoryAgentRegistry]:
    """Create a fresh registry instance for testing."""
    test_registry = InMemoryAgentRegistry(heartbeat_timeout=5, cleanup_interval=2)
    await test_registry.start_cleanup_task()
    yield test_registry
    await test_registry.stop_cleanup_task()


@pytest.fixture
def registry_client() -> Generator[TestClient]:
    """Create a FastAPI test client for the registry."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_agent_card() -> dict:
    """Provide a sample agent card for testing."""
    return {
        "name": "Test Weather Agent",
        "description": "A test weather agent for unit testing",
        "url": "http://localhost:9999",
        "version": "1.0.0",
        "capabilities": {
            "weather": ["forecast", "current", "alerts"],
            "locations": ["US"],
        },
        "skills": [
            {
                "name": "get_weather_forecast",
                "description": "Get weather forecast for a location",
                "parameters": ["location", "days"],
            }
        ],
    }


@pytest.fixture
def sample_cocktail_agent_card() -> dict:
    """Provide a sample cocktail agent card for testing."""
    return {
        "name": "Test Cocktail Agent",
        "description": "A test cocktail agent for unit testing",
        "url": "http://localhost:9998",
        "version": "1.0.0",
        "capabilities": {
            "cocktails": ["recipes", "ingredients", "search"],
        },
        "skills": [
            {
                "name": "search_cocktails",
                "description": "Search for cocktail recipes",
                "parameters": ["query"],
            }
        ],
    }


@pytest.fixture
def mock_weather_response() -> dict:
    """Provide a mock weather API response."""
    return {
        "location": "San Francisco, CA",
        "temperature": 65,
        "conditions": "Partly Cloudy",
        "forecast": [
            {"day": "Monday", "high": 68, "low": 55, "conditions": "Sunny"},
            {"day": "Tuesday", "high": 70, "low": 57, "conditions": "Clear"},
        ],
    }


@pytest.fixture
def mock_cocktail_response() -> dict:
    """Provide a mock cocktail API response."""
    return {
        "name": "Margarita",
        "ingredients": [
            "2 oz Tequila",
            "1 oz Lime juice",
            "1 oz Cointreau",
        ],
        "instructions": "Shake with ice and strain into a salt-rimmed glass.",
        "glass": "Margarita glass",
    }
