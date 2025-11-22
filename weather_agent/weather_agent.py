from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

weather_server_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="python3",
        args=["./mcp_server/weather.py"],
    )
)


def create_weather_agent():
    """Creates a weather-focused ADK Agent with weather MCP tools."""
    agent_instruction = """You are a helpful weather assistant. Your goal is to provide accurate and current weather information for US locations.

You have access to weather tools that use the National Weather Service API to:
- Get weather forecasts for specific locations
- Retrieve weather alerts and warnings
- Provide detailed weather conditions

When users ask about weather:
- Use your tools to get the most current information
- Provide clear, accurate forecasts
- Include relevant alerts or warnings when applicable
- Format your response clearly using Markdown

If you cannot find weather information for a specific location, let the user know and suggest they try a nearby major city or provide more specific location details.
"""

    weather_toolset = MCPToolset(connection_params=weather_server_params)

    root_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="weather_assistant",
        instruction=agent_instruction,
        tools=[weather_toolset],
    )
    return root_agent
