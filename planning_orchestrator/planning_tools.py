"""
Planning tools for the orchestrator agent.

These tools allow the orchestrator to discover agents and create execution plans
without directly executing A2A calls.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
import aiohttp
from google.adk.tools.tool_context import ToolContext

# Configure logging with structured format
import os
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logger = logging.getLogger(__name__)

# Global session for reuse
_global_session: Optional[aiohttp.ClientSession] = None


async def _get_session() -> aiohttp.ClientSession:
    """Get or create a global HTTP session."""
    global _global_session
    if _global_session is None or _global_session.closed:
        _global_session = aiohttp.ClientSession()
    return _global_session


def _calculate_relevance_score(agent: Dict[str, Any], intent: str) -> float:
    """Calculate how relevant an agent is for the given intent."""
    score = 0.0
    intent_lower = intent.lower()

    # Check agent name (weight: 0.2)
    if intent_lower in agent.get("name", "").lower():
        score += 0.2

    # Check agent description (weight: 0.3)
    description = agent.get("description", "").lower()
    if intent_lower in description:
        score += 0.3

    # Check skills (weight: 0.4)
    skills = agent.get("skills", [])
    for skill in skills:
        skill_score = 0.0

        # Check skill name and description
        if intent_lower in skill.get("name", "").lower():
            skill_score += 0.15
        if intent_lower in skill.get("description", "").lower():
            skill_score += 0.15

        # Check skill tags
        tags = skill.get("tags", [])
        for tag in tags:
            if intent_lower in tag.lower() or tag.lower() in intent_lower:
                skill_score += 0.05

        # Check skill examples
        examples = skill.get("examples", [])
        for example in examples:
            if intent_lower in example.lower() or any(word in intent_lower for word in example.lower().split()):
                skill_score += 0.05

        score += min(skill_score, 0.4)  # Cap skill contribution

    # Check capabilities (weight: 0.1)
    capabilities = agent.get("capabilities", {})
    for cap_key, cap_value in capabilities.items():
        if intent_lower in cap_key.lower():
            score += 0.1
            break

    return min(score, 1.0)  # Cap at 1.0


def _explain_score(agent: Dict[str, Any], intent: str, score: float) -> str:
    """Explain why an agent received a particular score."""
    reasons = []
    intent_lower = intent.lower()

    if intent_lower in agent.get("name", "").lower():
        reasons.append("name matches intent")

    if intent_lower in agent.get("description", "").lower():
        reasons.append("description matches intent")

    skills = agent.get("skills", [])
    for skill in skills:
        if intent_lower in skill.get("name", "").lower():
            reasons.append(f"skill '{skill.get('name')}' matches")
        elif intent_lower in skill.get("description", "").lower():
            reasons.append(f"skill description matches")
        elif any(intent_lower in tag.lower() or tag.lower() in intent_lower for tag in skill.get("tags", [])):
            reasons.append("skill tags match")

    if not reasons:
        reasons.append("partial keyword match")

    return f"Score {score:.2f}: {', '.join(reasons)}"


async def create_execution_plan(user_query: str, tool_context: ToolContext) -> str:
    """
    Analyze user query and create an execution plan.

    Args:
        user_query: The user's original query

    Returns:
        JSON string containing execution plan
    """
    registry_url = "http://localhost:8080"

    try:
        logger.info(f"🧠 Creating execution plan for: {user_query}")

        # Determine intent from user query
        intent = _extract_intent(user_query)
        logger.info(f"🎯 Extracted intent: {intent}")

        # Discover agents from registry
        session = await _get_session()
        url = f"{registry_url}/registry/agents"

        async with session.get(url) as response:
            if response.status != 200:
                error_msg = f"Failed to retrieve agents: HTTP {response.status}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({"error": error_msg, "plan": None})

            agents = await response.json()

            if not agents:
                return json.dumps({
                    "error": "No agents currently registered",
                    "plan": None
                })

            # Score agents based on intent
            scored_agents = []
            for agent in agents:
                score = _calculate_relevance_score(agent, intent)
                if score > 0:
                    scored_agents.append({
                        "agent": agent,
                        "score": score,
                        "reasoning": _explain_score(agent, intent, score)
                    })

            # Sort by score (highest first)
            scored_agents.sort(key=lambda x: x["score"], reverse=True)

            if not scored_agents:
                return json.dumps({
                    "error": f"No agents found matching intent: '{intent}'",
                    "available_agents": [a['name'] for a in agents],
                    "plan": None
                })

            # Create execution plan
            best_agent = scored_agents[0]
            plan = {
                "user_query": user_query,
                "intent": intent,
                "selected_agent": {
                    "name": best_agent["agent"]["name"],
                    "url": best_agent["agent"]["url"],
                    "score": best_agent["score"],
                    "reasoning": best_agent["reasoning"]
                },
                "execution_method": "mcp_tool",
                "tool_name": _get_tool_name_for_agent(best_agent["agent"]),
                "parameters": {
                    "query": user_query
                },
                "alternatives": [
                    {
                        "name": alt["agent"]["name"],
                        "url": alt["agent"]["url"],
                        "score": alt["score"]
                    } for alt in scored_agents[1:3]  # Top 2 alternatives
                ]
            }

            logger.info(f"✅ Created execution plan: selected {plan['selected_agent']['name']} (score: {plan['selected_agent']['score']})")

            return json.dumps({
                "success": True,
                "plan": plan
            })

    except Exception as e:
        error_msg = f"Error creating execution plan: {e}"
        logger.error(f"❌ {error_msg}")
        return json.dumps({"error": error_msg, "plan": None})


def _extract_intent(user_query: str) -> str:
    """Extract intent from user query."""
    query_lower = user_query.lower()

    # Weather-related keywords
    weather_keywords = ["weather", "forecast", "temperature", "rain", "snow", "sunny", "cloudy", "wind", "humidity"]
    if any(keyword in query_lower for keyword in weather_keywords):
        return "weather information"

    # Cocktail-related keywords
    cocktail_keywords = ["cocktail", "drink", "recipe", "bartender", "martini", "mojito", "margarita", "whiskey", "vodka", "gin", "rum"]
    if any(keyword in query_lower for keyword in cocktail_keywords):
        return "cocktail recipe"

    # Default intent
    return "general query"


def _get_tool_name_for_agent(agent: Dict[str, Any]) -> str:
    """Map agent to corresponding MCP tool name."""
    agent_name = agent.get("name", "").lower()

    if "weather" in agent_name:
        return "weather_tools"
    elif "cocktail" in agent_name:
        return "cocktail_tools"
    else:
        return "general_tools"


async def get_registry_status(tool_context: ToolContext) -> str:
    """
    Get the current status of the registry.

    Returns:
        JSON string with registry status information
    """
    registry_url = "http://localhost:8080"

    try:
        session = await _get_session()
        url = f"{registry_url}/registry/status"

        async with session.get(url) as response:
            if response.status == 200:
                status = await response.json()
                logger.info("📊 Retrieved registry status")
                return f"Registry status: {status}"
            else:
                error_msg = f"Failed to retrieve registry status: HTTP {response.status}"
                logger.error(f"❌ {error_msg}")
                return error_msg

    except Exception as e:
        error_msg = f"Error retrieving registry status: {e}"
        logger.error(f"❌ {error_msg}")
        return error_msg


async def list_available_agents(tool_context: ToolContext) -> str:
    """
    Get all registered agents from the registry.

    Returns:
        JSON string containing all registered agents
    """
    registry_url = "http://localhost:8080"

    try:
        session = await _get_session()
        url = f"{registry_url}/registry/agents"

        async with session.get(url) as response:
            if response.status == 200:
                agents = await response.json()
                logger.info(f"📋 Retrieved {len(agents)} agents from registry")

                agent_list = []
                for agent in agents:
                    agent_list.append({
                        "name": agent.get("name"),
                        "description": agent.get("description"),
                        "url": agent.get("url"),
                        "capabilities": list(agent.get("capabilities", {}).keys()),
                        "skills": [skill.get("name") for skill in agent.get("skills", [])]
                    })

                return json.dumps({
                    "total_agents": len(agents),
                    "agents": agent_list
                })
            else:
                error_msg = f"Failed to retrieve agents: HTTP {response.status}"
                logger.error(f"❌ {error_msg}")
                return error_msg

    except Exception as e:
        error_msg = f"Error connecting to registry: {e}"
        logger.error(f"❌ {error_msg}")
        return error_msg