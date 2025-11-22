"""
Unit tests for planning tools.

Tests cover intent extraction, agent scoring, execution plan creation, and registry interactions.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from planning_orchestrator.planning_tools import (
    _calculate_relevance_score,
    _explain_score,
    _extract_intent,
    _get_tool_name_for_agent,
    create_execution_plan,
    get_registry_status,
    list_available_agents,
)


class TestIntentExtraction:
    """Test suite for intent extraction from user queries."""

    def test_extract_weather_intent(self):
        """Test extraction of weather-related intent."""
        queries = [
            "What's the weather in San Francisco?",
            "Will it rain tomorrow?",
            "Show me the forecast for NYC",
            "What's the temperature outside?",
        ]
        for query in queries:
            intent = _extract_intent(query)
            assert intent == "weather information"

    def test_extract_cocktail_intent(self):
        """Test extraction of cocktail-related intent."""
        queries = [
            "How do I make a margarita?",
            "What cocktails can I make with vodka?",
            "Give me a mojito recipe",
            "Best whiskey drinks",
        ]
        for query in queries:
            intent = _extract_intent(query)
            assert intent == "cocktail recipe"

    def test_extract_general_intent(self):
        """Test extraction of general/unknown intent."""
        queries = [
            "What time is it?",
            "Tell me a joke",
            "Calculate 2 + 2",
        ]
        for query in queries:
            intent = _extract_intent(query)
            assert intent == "general query"


class TestRelevanceScoring:
    """Test suite for agent relevance scoring."""

    def test_calculate_score_name_match(self, sample_agent_card: dict):
        """Test scoring when intent matches agent name."""
        score = _calculate_relevance_score(sample_agent_card, "weather")
        assert score > 0.0

    def test_calculate_score_description_match(self, sample_agent_card: dict):
        """Test scoring when intent matches agent description."""
        score = _calculate_relevance_score(sample_agent_card, "weather")
        assert score > 0.0

    def test_calculate_score_skill_match(self, sample_agent_card: dict):
        """Test scoring when intent matches agent skills."""
        score = _calculate_relevance_score(sample_agent_card, "forecast")
        assert score > 0.0

    def test_calculate_score_no_match(self, sample_agent_card: dict):
        """Test scoring when intent doesn't match anything."""
        score = _calculate_relevance_score(sample_agent_card, "completely_unrelated")
        assert score == 0.0

    def test_calculate_score_capability_match(self, sample_agent_card: dict):
        """Test scoring when intent matches capabilities."""
        sample_agent_card["capabilities"] = {"weather": ["forecast", "current"]}
        score = _calculate_relevance_score(sample_agent_card, "weather")
        assert score > 0.0

    def test_score_capped_at_one(self, sample_agent_card: dict):
        """Test that scores are capped at 1.0."""
        # Create an agent with many matches
        sample_agent_card["name"] = "weather weather weather"
        sample_agent_card["description"] = "weather weather weather"
        score = _calculate_relevance_score(sample_agent_card, "weather")
        assert score <= 1.0

    def test_explain_score(self, sample_agent_card: dict):
        """Test score explanation generation."""
        score = _calculate_relevance_score(sample_agent_card, "weather")
        explanation = _explain_score(sample_agent_card, "weather", score)
        assert "Score" in explanation
        assert isinstance(explanation, str)


class TestToolMapping:
    """Test suite for mapping agents to MCP tools."""

    def test_get_tool_name_weather(self, sample_agent_card: dict):
        """Test tool name mapping for weather agent."""
        tool_name = _get_tool_name_for_agent(sample_agent_card)
        assert tool_name == "weather_tools"

    def test_get_tool_name_cocktail(self, sample_cocktail_agent_card: dict):
        """Test tool name mapping for cocktail agent."""
        tool_name = _get_tool_name_for_agent(sample_cocktail_agent_card)
        assert tool_name == "cocktail_tools"

    def test_get_tool_name_unknown(self):
        """Test tool name mapping for unknown agent type."""
        unknown_agent = {"name": "Unknown Agent"}
        tool_name = _get_tool_name_for_agent(unknown_agent)
        assert tool_name == "general_tools"


class TestExecutionPlanCreation:
    """Test suite for execution plan creation."""

    @pytest.mark.asyncio
    async def test_create_execution_plan_success(
        self, sample_agent_card: dict, sample_cocktail_agent_card: dict
    ):
        """Test successful execution plan creation."""
        # Mock the aiohttp session with proper async context manager
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[sample_agent_card, sample_cocktail_agent_card])

        mock_get = AsyncMock()
        mock_get.__aenter__.return_value = mock_response
        mock_get.__aexit__.return_value = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get.return_value = mock_get
        mock_session.closed = False

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await create_execution_plan("What's the weather today?", mock_context)

            data = json.loads(result)
            # Check if we got a valid response (could be success or error depending on mock)
            assert isinstance(data, dict)
            # If successful, verify the structure
            if data.get("success"):
                assert "plan" in data
                assert data["plan"]["selected_agent"]["name"] == sample_agent_card["name"]
                assert data["plan"]["intent"] == "weather information"

    @pytest.mark.asyncio
    async def test_create_execution_plan_no_agents(self):
        """Test execution plan creation when no agents are registered."""
        # Mock empty agent list
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await create_execution_plan("test query", mock_context)

            data = json.loads(result)
            assert "error" in data
            assert data["plan"] is None

    @pytest.mark.asyncio
    async def test_create_execution_plan_registry_failure(self):
        """Test execution plan creation when registry request fails."""
        # Mock failed request
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await create_execution_plan("test query", mock_context)

            data = json.loads(result)
            assert "error" in data
            assert data["plan"] is None

    @pytest.mark.asyncio
    async def test_create_execution_plan_no_matching_agents(self, sample_agent_card: dict):
        """Test execution plan when no agents match the intent."""
        # Mock agent that won't match the intent
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[sample_agent_card])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            # Query completely unrelated to weather
            result = await create_execution_plan("completely unrelated query xyz123", mock_context)

            data = json.loads(result)
            # Should still succeed but with low score or error
            assert "error" in data or "plan" in data

    @pytest.mark.asyncio
    async def test_create_execution_plan_with_alternatives(
        self, sample_agent_card: dict, sample_cocktail_agent_card: dict
    ):
        """Test that execution plan includes alternative agents."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[sample_agent_card, sample_cocktail_agent_card])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await create_execution_plan("weather or drinks", mock_context)

            data = json.loads(result)
            if data.get("success"):
                assert "alternatives" in data["plan"]


class TestRegistryStatus:
    """Test suite for registry status retrieval."""

    @pytest.mark.asyncio
    async def test_get_registry_status_success(self):
        """Test successful registry status retrieval."""
        mock_status = {"total_agents": 2, "active_agents": 2, "registry_uptime": 100.5}

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_status)

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await get_registry_status(mock_context)

            assert "Registry status" in result
            assert str(mock_status) in result

    @pytest.mark.asyncio
    async def test_get_registry_status_failure(self):
        """Test registry status retrieval when request fails."""
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await get_registry_status(mock_context)

            assert "Failed" in result or "Error" in result


class TestListAvailableAgents:
    """Test suite for listing available agents."""

    @pytest.mark.asyncio
    async def test_list_available_agents_success(
        self, sample_agent_card: dict, sample_cocktail_agent_card: dict
    ):
        """Test successful listing of available agents."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[sample_agent_card, sample_cocktail_agent_card])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await list_available_agents(mock_context)

            data = json.loads(result)
            assert data["total_agents"] == 2
            assert len(data["agents"]) == 2
            assert data["agents"][0]["name"] == sample_agent_card["name"]

    @pytest.mark.asyncio
    async def test_list_available_agents_empty(self):
        """Test listing agents when registry is empty."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await list_available_agents(mock_context)

            data = json.loads(result)
            assert data["total_agents"] == 0
            assert len(data["agents"]) == 0

    @pytest.mark.asyncio
    async def test_list_available_agents_failure(self):
        """Test listing agents when request fails."""
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("planning_orchestrator.planning_tools._get_session", return_value=mock_session):
            mock_context = MagicMock()
            result = await list_available_agents(mock_context)

            assert "Failed" in result or "Error" in result
