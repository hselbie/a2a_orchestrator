"""
Unit tests for the FastAPI registry service.

Tests cover agent registration, heartbeat monitoring, cleanup, and all API endpoints.
"""

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from registry_service.fastapi_registry import InMemoryAgentRegistry


class TestInMemoryAgentRegistry:
    """Test suite for InMemoryAgentRegistry class."""

    @pytest.mark.asyncio
    async def test_register_agent(self, registry: InMemoryAgentRegistry, sample_agent_card: dict):
        """Test successful agent registration."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        agent_card = registry.register_agent(registration)

        assert agent_card.name == sample_agent_card["name"]
        assert agent_card.url == sample_agent_card["url"]
        assert sample_agent_card["url"] in registry.agents
        assert sample_agent_card["url"] in registry.last_seen

    @pytest.mark.asyncio
    async def test_register_duplicate_agent(
        self, registry: InMemoryAgentRegistry, sample_agent_card: dict
    ):
        """Test that registering the same agent twice updates the existing entry."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)

        # Register once
        registry.register_agent(registration)
        assert len(registry.agents) == 1

        # Register again - should update, not duplicate
        registry.register_agent(registration)
        assert len(registry.agents) == 1

    @pytest.mark.asyncio
    async def test_unregister_agent(self, registry: InMemoryAgentRegistry, sample_agent_card: dict):
        """Test successful agent unregistration."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        registry.register_agent(registration)

        # Unregister
        result = registry.unregister_agent(sample_agent_card["url"])
        assert result is True
        assert sample_agent_card["url"] not in registry.agents
        assert sample_agent_card["url"] not in registry.last_seen

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self, registry: InMemoryAgentRegistry):
        """Test unregistering an agent that doesn't exist."""
        result = registry.unregister_agent("http://nonexistent:9999")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_heartbeat(self, registry: InMemoryAgentRegistry, sample_agent_card: dict):
        """Test heartbeat timestamp updates."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        registry.register_agent(registration)

        initial_timestamp = registry.last_seen[sample_agent_card["url"]]
        await asyncio.sleep(0.1)

        # Update heartbeat
        result = registry.update_heartbeat(sample_agent_card["url"])
        assert result is True

        updated_timestamp = registry.last_seen[sample_agent_card["url"]]
        assert updated_timestamp > initial_timestamp

    @pytest.mark.asyncio
    async def test_update_heartbeat_nonexistent_agent(self, registry: InMemoryAgentRegistry):
        """Test updating heartbeat for non-existent agent."""
        result = registry.update_heartbeat("http://nonexistent:9999")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_agents(
        self,
        registry: InMemoryAgentRegistry,
        sample_agent_card: dict,
        sample_cocktail_agent_card: dict,
    ):
        """Test retrieving all registered agents."""
        from registry_service.fastapi_registry import AgentRegistration

        # Register multiple agents
        reg1 = AgentRegistration(**sample_agent_card)
        reg2 = AgentRegistration(**sample_cocktail_agent_card)

        registry.register_agent(reg1)
        registry.register_agent(reg2)

        agents = registry.get_all_agents()
        assert len(agents) == 2
        assert any(a.name == sample_agent_card["name"] for a in agents)
        assert any(a.name == sample_cocktail_agent_card["name"] for a in agents)

    @pytest.mark.asyncio
    async def test_get_agent(self, registry: InMemoryAgentRegistry, sample_agent_card: dict):
        """Test retrieving a specific agent by URL."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        registry.register_agent(registration)

        agent = registry.get_agent(sample_agent_card["url"])
        assert agent is not None
        assert agent.name == sample_agent_card["name"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, registry: InMemoryAgentRegistry):
        """Test retrieving an agent that doesn't exist."""
        agent = registry.get_agent("http://nonexistent:9999")
        assert agent is None

    @pytest.mark.asyncio
    async def test_get_status(
        self,
        registry: InMemoryAgentRegistry,
        sample_agent_card: dict,
        sample_cocktail_agent_card: dict,
    ):
        """Test registry status reporting."""
        from registry_service.fastapi_registry import AgentRegistration

        # Register agents
        reg1 = AgentRegistration(**sample_agent_card)
        reg2 = AgentRegistration(**sample_cocktail_agent_card)
        registry.register_agent(reg1)
        registry.register_agent(reg2)

        status = registry.get_status()
        assert status.total_agents == 2
        assert status.active_agents == 2
        assert status.registry_uptime > 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_agents(
        self, registry: InMemoryAgentRegistry, sample_agent_card: dict
    ):
        """Test automatic cleanup of stale agents."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        registry.register_agent(registration)

        # Manually set last_seen to be old enough to trigger cleanup
        registry.last_seen[sample_agent_card["url"]] = time.time() - 100

        # Run cleanup
        removed_count = await registry.cleanup_stale_agents()
        assert removed_count == 1
        assert sample_agent_card["url"] not in registry.agents

    @pytest.mark.asyncio
    async def test_cleanup_no_stale_agents(
        self, registry: InMemoryAgentRegistry, sample_agent_card: dict
    ):
        """Test cleanup when no agents are stale."""
        from registry_service.fastapi_registry import AgentRegistration

        registration = AgentRegistration(**sample_agent_card)
        registry.register_agent(registration)

        # Run cleanup immediately - agent should still be fresh
        removed_count = await registry.cleanup_stale_agents()
        assert removed_count == 0
        assert sample_agent_card["url"] in registry.agents


class TestRegistryAPI:
    """Test suite for FastAPI registry endpoints."""

    def test_health_check(self, registry_client: TestClient):
        """Test health check endpoint."""
        response = registry_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["registry"] == "running"

    def test_register_agent_endpoint(self, registry_client: TestClient, sample_agent_card: dict):
        """Test POST /registry/register endpoint."""
        response = registry_client.post("/registry/register", json=sample_agent_card)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_agent_card["name"]
        assert data["url"] == sample_agent_card["url"]

    def test_reregister_agent_endpoint(self, registry_client: TestClient, sample_agent_card: dict):
        """Test PUT /registry/register endpoint."""
        # Initial registration
        registry_client.post("/registry/register", json=sample_agent_card)

        # Re-register with PUT
        response = registry_client.put("/registry/register", json=sample_agent_card)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_agent_card["name"]

    def test_list_agents_endpoint(
        self,
        registry_client: TestClient,
        sample_agent_card: dict,
        sample_cocktail_agent_card: dict,
    ):
        """Test GET /registry/agents endpoint."""
        # Register multiple agents
        registry_client.post("/registry/register", json=sample_agent_card)
        registry_client.post("/registry/register", json=sample_cocktail_agent_card)

        # List all agents
        response = registry_client.get("/registry/agents")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) == 2

    def test_get_agent_endpoint(self, registry_client: TestClient, sample_agent_card: dict):
        """Test GET /registry/agents/{url} endpoint."""
        # Register agent
        registry_client.post("/registry/register", json=sample_agent_card)

        # Get specific agent (URL encoding needed)
        import urllib.parse

        encoded_url = urllib.parse.quote(sample_agent_card["url"], safe="")
        response = registry_client.get(f"/registry/agents/{encoded_url}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_agent_card["name"]

    def test_get_nonexistent_agent_endpoint(self, registry_client: TestClient):
        """Test GET /registry/agents/{url} with non-existent agent."""
        import urllib.parse

        encoded_url = urllib.parse.quote("http://nonexistent:9999", safe="")
        response = registry_client.get(f"/registry/agents/{encoded_url}")
        assert response.status_code == 404

    def test_heartbeat_endpoint(self, registry_client: TestClient, sample_agent_card: dict):
        """Test POST /registry/heartbeat endpoint."""
        # Register agent first
        registry_client.post("/registry/register", json=sample_agent_card)

        # Send heartbeat
        response = registry_client.post(
            "/registry/heartbeat", json={"url": sample_agent_card["url"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_heartbeat_nonexistent_agent(self, registry_client: TestClient):
        """Test heartbeat for non-existent agent."""
        response = registry_client.post(
            "/registry/heartbeat", json={"url": "http://nonexistent:9999"}
        )
        assert response.status_code == 404

    def test_unregister_endpoint(self, registry_client: TestClient, sample_agent_card: dict):
        """Test DELETE /registry/unregister/{url} endpoint."""
        # Register agent
        registry_client.post("/registry/register", json=sample_agent_card)

        # Unregister
        import urllib.parse

        encoded_url = urllib.parse.quote(sample_agent_card["url"], safe="")
        response = registry_client.delete(f"/registry/unregister/{encoded_url}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_unregister_nonexistent_agent_endpoint(self, registry_client: TestClient):
        """Test unregistering non-existent agent."""
        import urllib.parse

        encoded_url = urllib.parse.quote("http://nonexistent:9999", safe="")
        response = registry_client.delete(f"/registry/unregister/{encoded_url}")
        assert response.status_code == 404

    def test_registry_status_endpoint(
        self,
        registry_client: TestClient,
        sample_agent_card: dict,
        sample_cocktail_agent_card: dict,
    ):
        """Test GET /registry/status endpoint."""
        # Register agents
        registry_client.post("/registry/register", json=sample_agent_card)
        registry_client.post("/registry/register", json=sample_cocktail_agent_card)

        # Get status
        response = registry_client.get("/registry/status")
        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 2
        assert data["active_agents"] == 2
        assert "registry_uptime" in data
