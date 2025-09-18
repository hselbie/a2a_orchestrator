"""
Planning-based orchestrator agent.

This orchestrator queries the registry, creates execution plans, and delegates
execution to a specialized executor agent with MCP tools.
"""

import json
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from .planning_tools import (
    create_execution_plan,
    get_registry_status,
    list_available_agents
)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# MCP Server configurations for executor tools
weather_server_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="python3",
        args=[str(PROJECT_ROOT / "mcp_server" / "weather.py")],
    )
)

cocktail_server_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="python3",
        args=[str(PROJECT_ROOT / "mcp_server" / "cocktail.py")],
    )
)


def create_planning_orchestrator_agent():
    """Create an orchestrator agent that uses planning and execution pattern."""

    # Create planning tools
    create_execution_plan_tool = FunctionTool(create_execution_plan)
    get_registry_status_tool = FunctionTool(get_registry_status)
    list_available_agents_tool = FunctionTool(list_available_agents)

    # Create MCP toolsets for direct execution
    weather_toolset = McpToolset(connection_params=weather_server_params)
    cocktail_toolset = McpToolset(connection_params=cocktail_server_params)

    # Create the orchestrator agent
    orchestrator_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="planning_orchestrator_agent",
        instruction="""
You are an intelligent orchestrator agent that uses a planning and execution pattern for dynamic agent discovery and routing.

**YOUR ROLE:**
You discover available agents, create execution plans, and then execute those plans using the appropriate tools.

**AVAILABLE TOOLS:**

**Planning Tools:**
- `create_execution_plan(user_query)`: Analyze user query and create execution plan with agent selection
- `list_available_agents()`: Get all registered agents and their capabilities
- `get_registry_status()`: Check registry health and statistics

**Execution Tools:**
- Weather tools (MCP): For weather forecasts, alerts, and conditions
- Cocktail tools (MCP): For cocktail recipes and ingredient information

**WORKFLOW:**

1. **Create Plan**: Use `create_execution_plan(user_query)` to:
   - Analyze the user's intent
   - Discover available agents from the registry
   - Score agents by relevance
   - Select the best agent and create execution plan

2. **Execute Plan**: Based on the plan's tool recommendation:
   - For weather queries: Use weather MCP tools directly
   - For cocktail queries: Use cocktail MCP tools directly

3. **Return Results**: Provide the final results to the user

**EXAMPLE WORKFLOW:**

User asks: "What's the weather in San Francisco?"

1. Call: create_execution_plan("What's the weather in San Francisco?")
   Response: {"success": true, "plan": {"selected_agent": {"name": "Weather Agent"}, "tool_name": "weather_tools", "user_query": "What's the weather in San Francisco?"}}

2. Since plan recommends "weather_tools", use weather MCP tools with the query
3. Return weather results to user

**IMPORTANT GUIDELINES:**
- Always create a plan first before executing
- Follow the plan's tool recommendation
- Log your reasoning for transparency
- If no suitable agents are found, inform the user
- Handle errors gracefully and suggest alternatives

**DISCOVERY EXAMPLES:**
- Weather queries → Weather Agent → weather MCP tools
- Cocktail queries → Cocktail Agent → cocktail MCP tools
- Unknown queries → List available agents and suggest alternatives

Your goal is to seamlessly connect users with the right specialized tools based on dynamic agent discovery while providing full visibility into the planning and execution process.
        """,
        tools=[
            create_execution_plan_tool,
            list_available_agents_tool,
            get_registry_status_tool,
            weather_toolset,
            cocktail_toolset
        ],
    )

    return orchestrator_agent