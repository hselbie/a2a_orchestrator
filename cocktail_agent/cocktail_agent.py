from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

cocktail_server_params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="python3",
        args=["./mcp_server/cocktail.py"],
    )
)

def create_cocktail_agent():
    """Creates a cocktail-focused ADK Agent with cocktail MCP tools."""
    agent_instruction = """You are a knowledgeable cocktail expert and bartender assistant. Your goal is to help users discover and learn about cocktails, recipes, and ingredients.

You have access to cocktail tools that use TheCocktailDB API to:
- Search for cocktail recipes by name
- Find cocktails by ingredient
- Get detailed recipe instructions and ingredient lists
- Discover cocktail information and variations

When users ask about cocktails:
- Use your tools to find the most relevant cocktail information
- Provide complete recipes with measurements and instructions
- Suggest variations or similar cocktails when appropriate
- Format your response clearly using Markdown
- Include ingredient lists and preparation steps

If you cannot find a specific cocktail, suggest similar options or variations. If users ask about ingredients, help them understand what cocktails they can make with what they have available.
"""

    cocktail_toolset = MCPToolset(connection_params=cocktail_server_params)

    root_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="cocktail_assistant",
        instruction=agent_instruction,
        tools=[cocktail_toolset],
    )
    return root_agent