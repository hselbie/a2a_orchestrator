# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Dynamic Agent-to-Agent (A2A) Orchestrator** system that demonstrates advanced agent discovery and routing using Google's Agent Development Kit (ADK) and Model Control Protocol (MCP). The system consists of specialized agents (weather, cocktail) that auto-register with a discovery registry, and a dynamic orchestrator that intelligently routes user queries to appropriate agents.

## Running the System

### Quick Start
```bash
# Start components individually (no combined start script available):

# 1. Start registry server first
python registry_service/start.py  # port 8080

# 2. Start agent servers (they auto-register) - either method works:
python weather_agent/start.py     # port 8001
# OR: python -m weather_agent.start

python cocktail_agent/start.py    # port 8002
# OR: python -m cocktail_agent.start

# 3. Start orchestrator
python -m planning_orchestrator.start # port 8000
```

### Testing
- **Web Interface**: http://localhost:8000 (WebSocket-based chat)
- **Test Queries**: "weather in San Francisco", "how to make a mojito", "cocktails with vodka"
- **Agent Health**: Check individual agent endpoints at their respective ports

## Architecture

### Core Components

**Planning Orchestrator (`planning_orchestrator/`)**
- `planning_orchestrator_agent.py` - Core orchestrator with planning capabilities
- `run_planning_orchestrator.py` - Main runner script with WebSocket interface
- `planning_tools.py` - Planning and execution tools
- Analyzes user queries and discovers appropriate agents via MCP registry
- Routes requests using intelligent agent selection with scoring and reasoning
- Runs on port 8000 with WebSocket interface

**Agent Registry (`registry_service/`)**
- `fastapi_registry.py` - FastAPI-based registration service for agent discovery
- `auto_registration.py` - Auto-registration utilities for agents
- `start.py` - Registry startup script
- Maintains agent metadata (capabilities, skills, descriptions)
- Handles agent heartbeats and automatic cleanup of stale agents
- Runs on port 8080

**Specialized Agents**
- `weather_agent/` - National Weather Service integration (port 8001)
  - `weather_agent.py` - Agent definition with weather capabilities
  - `weather_a2a_server.py` - A2A server implementation
  - `start.py` - Weather agent startup script
- `cocktail_agent/` - TheCocktailDB integration (port 8002)
  - `cocktail_agent.py` - Agent definition with cocktail capabilities
  - `cocktail_a2a_server.py` - A2A server implementation
  - `start.py` - Cocktail agent startup script
- Each agent auto-registers with registry on startup

### Key Patterns

**MCP Integration**: All tools are exposed via MCP servers (`mcp_server/` directory)
- `weather.py` - Weather tool MCP server
- `cocktail.py` - Cocktail tool MCP server
- `registry_client.py` - Registry interaction utilities

**A2A Communication**: Agents communicate via HTTP using the a2a-sdk
- Agents expose AgentCard metadata for discovery
- AgentSkill definitions enable intelligent routing
- Heartbeat mechanism ensures registry freshness

**ADK Architecture**: Built on Google ADK primitives
- `LlmAgent` with MCP toolsets for specialized agents
- Planning-based orchestrator for discovery and routing logic
- `Runner` for execution with session/artifact management

## Discovery and Routing Flow

1. **User Query** → Orchestrator (port 8000)
2. **Intent Analysis** → `discover_agents` tool via MCP registry
3. **Agent Selection** → Highest scoring agent based on capabilities/skills
4. **Request Routing** → `RemoteA2aAgent` creates A2A connection
5. **Response Handling** → Formats and returns specialized agent response

## Dependencies

This project inherits dependencies from the parent `pyproject.toml`:
- `google-adk>=1.13.0` - Core ADK framework
- `a2a-sdk>=0.3.2` - Agent-to-agent communication
- `fastapi>=0.115.13` - Registry server
- `uvicorn>=0.34.3` - ASGI server

## Development Commands

```bash
# Start individual components for debugging
python registry_service/start.py                            # Registry only (port 8080)
python weather_agent/start.py                              # Weather agent only (port 8001)
python cocktail_agent/start.py                             # Cocktail agent only (port 8002)
python planning_orchestrator/run_planning_orchestrator.py  # Orchestrator only (port 8000)

# Test MCP servers directly
python -c "from mcp_server.weather import main; import asyncio; asyncio.run(main())"
python -c "from mcp_server.cocktail import main; import asyncio; asyncio.run(main())"

# Test registry service
python -c "from registry_service.fastapi_registry import app; import uvicorn; uvicorn.run(app, port=8080)"
```

## System Management

- **Startup Order**: Registry → Agents → Orchestrator (manual startup required)
- **Health Monitoring**: Registry tracks agent heartbeats, removes stale agents after 30s
- **Process Management**: Each component must be started individually using their respective start scripts
- **Logging**: Comprehensive logging across all components for debugging agent discovery and routing

## Extension Points

To add new specialized agents:
1. Create agent directory (e.g., `my_agent/`)
2. Create agent definition (`my_agent/my_agent.py`) with `LlmAgent` + MCP toolset
3. Create A2A server (`my_agent/my_a2a_server.py`) with `AgentSkill` metadata
4. Create startup script (`my_agent/start.py`) following the pattern of existing agents
5. Add MCP server for tools in `mcp_server/my_tools.py` if needed
6. Start the new agent manually: `python my_agent/start.py`

The orchestrator will automatically discover and route to new agents based on their registered skills and capabilities.