# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Dynamic Agent-to-Agent (A2A) Orchestrator** system that demonstrates advanced agent discovery and routing using Google's Agent Development Kit (ADK) and Model Control Protocol (MCP). The system consists of specialized agents (weather, cocktail) that auto-register with a discovery registry, and a dynamic orchestrator that intelligently routes user queries to appropriate agents.

## Running the System

### Quick Start
```bash
# Start the entire system (recommended)
python start_system.py

# Or start components individually:
# 1. Start registry server first
python mcp_server/agent_registry.py

# 2. Start agent servers (they auto-register)
python weather_a2a_server.py  # port 8001
python cocktail_a2a_server.py # port 8002

# 3. Start orchestrator
python run_dynamic_orchestrator.py # port 8000
```

### Testing
- **Web Interface**: http://localhost:8000 (WebSocket-based chat)
- **Test Queries**: "weather in San Francisco", "how to make a mojito", "cocktails with vodka"
- **Agent Health**: Check individual agent endpoints at their respective ports

## Architecture

### Core Components

**Dynamic Orchestrator (`dynamic_orchestrator_agent.py`)**
- Analyzes user queries and discovers appropriate agents via MCP registry
- Routes requests using `RemoteA2aAgent` connections
- Provides intelligent agent selection with scoring and reasoning
- Runs on port 8000 with WebSocket interface

**Agent Registry (`mcp_server/agent_registry.py`)**
- FastAPI-based registration service for agent discovery
- Maintains agent metadata (capabilities, skills, descriptions)
- Handles agent heartbeats and automatic cleanup of stale agents
- Exposes discovery tools via MCP protocol

**Specialized Agents**
- `weather_agent.py` + `weather_a2a_server.py` - National Weather Service integration (port 8001)
- `cocktail_agent.py` + `cocktail_a2a_server.py` - TheCocktailDB integration (port 8002)
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
- `Agent` (not `LlmAgent`) for orchestrator with discovery logic
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
python mcp_server/agent_registry.py    # Registry only
python weather_a2a_server.py          # Weather agent only
python cocktail_a2a_server.py         # Cocktail agent only
python run_dynamic_orchestrator.py    # Orchestrator only

# Test MCP servers directly
python -c "from mcp_server.weather import main; import asyncio; asyncio.run(main())"

# Test agent registration
python example_agent_with_registry.py
```

## System Management

- **Startup Order**: Registry → Agents → Orchestrator (handled by `start_system.py`)
- **Health Monitoring**: Registry tracks agent heartbeats, removes stale agents after 30s
- **Process Management**: `start_system.py` handles graceful startup/shutdown of all components
- **Logging**: Comprehensive logging across all components for debugging agent discovery and routing

## Extension Points

To add new specialized agents:
1. Create agent definition (e.g., `my_agent.py`) with `LlmAgent` + MCP toolset
2. Create A2A server (e.g., `my_a2a_server.py`) with `AgentSkill` metadata
3. Add MCP server for tools in `mcp_server/my_tools.py` if needed
4. Update `start_system.py` to include the new agent in startup sequence

The orchestrator will automatically discover and route to new agents based on their registered skills and capabilities.