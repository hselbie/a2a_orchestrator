# A2A Dynamic Orchestrator

A sophisticated Agent-to-Agent (A2A) orchestration system built with Google's Agent Development Kit (ADK) that provides dynamic agent discovery, intelligent routing, and execution planning.

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.9 or higher
- **uv Package Manager**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Google Cloud**: Project with AI Platform API enabled
- **Authentication**: `gcloud auth application-default login`

### Installation

```bash
# Navigate to project
cd path/to/a2a_orchestrator

# Install dependencies
uv sync

# Optional: Create .env file
echo "LOG_LEVEL=INFO" > .env
```

### Running the System

The system requires **4 separate terminal windows** running simultaneously:

#### Terminal 1: Registry Service
```bash
uv run python -m registry_service.start
```
**Expected**: `🚀 Starting FastAPI Agent Registry on http://localhost:8080`

#### Terminal 2: Weather Agent
```bash
# Either method works:
uv run python weather_agent/start.py
# OR: uv run python -m weather_agent.start
```
**Expected**: `🌦️ Starting A2A Weather Agent Server with Auto-Registration...`
**Port**: 8001

#### Terminal 3: Cocktail Agent
```bash
# Either method works:
uv run python cocktail_agent/start.py
# OR: uv run python -m cocktail_agent.start
```
**Expected**: `🍹 Starting A2A Cocktail Agent Server with Auto-Registration...`
**Port**: 8002

#### Terminal 4: Planning Orchestrator
```bash
uv run python -m planning_orchestrator.start
```
**Expected**: `🚀 Starting Planning-Based Dynamic Orchestrator on http://localhost:8000`
**Port**: 8000

### Testing
1. **Web Interface**: http://localhost:8000
2. **Sample Queries**:
   - Weather: "What's the weather in San Francisco?"
   - Cocktails: "How do I make a margarita?"
   - Mixed: "What cocktails go well with cold weather?"
3. **System Tests**: `uv run python tests/test_system.py`

### ✅ Recent Fixes Applied
- **Import Issues**: Fixed relative import errors in all agent start scripts
- **Path Issues**: Corrected MCP server paths and static directory paths
- **Error Handling**: Added robust error handling for MCP session cleanup
- **WebSocket Stability**: Improved WebSocket error handling to prevent "connection closed" issues

## 🏗️ Architecture

### Core Components
- **Planning Orchestrator**: Intelligent agent discovery and execution planning
- **FastAPI Registry**: Central registry with health monitoring
- **Auto-Registration**: Automatic agent registration with heartbeats
- **MCP Tools**: Direct tool execution for weather and cocktail capabilities

### Agent Flow
```
User Query → Planning Orchestrator → Registry Discovery → Agent Selection → MCP Tool Execution → Response
```

### Key Features
- **Dynamic Discovery**: Agents register automatically and are discovered at runtime
- **Intelligent Routing**: Score-based agent selection using intent analysis
- **Health Monitoring**: Automatic heartbeat monitoring and cleanup of stale agents
- **Planning Pattern**: Separation of planning and execution for transparency
- **Real-time Communication**: WebSocket-based client communication

## 📁 Project Structure

```
a2a_orchestrator/
├── README.md                          # This file
├── requirements.txt                   # Dependencies
├── tests/                             # Testing
│   └── test_system.py                 # Automated system validation
├── docs/                              # Documentation
│   ├── api/API_REFERENCE.md          # Complete API documentation
│   └── testing/MANUAL_TESTING_GUIDE.md # Step-by-step testing
├── registry_service/                  # Central registry service
│   ├── fastapi_registry.py           # Registry implementation
│   ├── auto_registration.py          # Auto-registration logic
│   └── start.py                      # Startup script
├── planning_orchestrator/             # Planning & orchestration
│   ├── run_planning_orchestrator.py  # Web server
│   ├── planning_orchestrator_agent.py # Agent definition
│   ├── planning_tools.py             # Planning logic
│   └── start.py                      # Startup script
├── weather_agent/                     # Weather capabilities
│   ├── weather_a2a_server.py         # A2A server
│   ├── weather_agent.py              # Agent definition
│   └── start.py                      # Startup script
├── cocktail_agent/                    # Cocktail capabilities
│   ├── cocktail_a2a_server.py        # A2A server
│   ├── cocktail_agent.py             # Agent definition
│   └── start.py                      # Startup script
├── mcp_server/                        # MCP tool implementations
│   ├── weather.py                    # Weather tools
│   └── cocktail.py                   # Cocktail tools
└── static/                           # Web interface
    └── index.html                    # WebSocket client
```

## 🛠️ Development

### Adding New Agents
1. Create new agent folder: `mkdir my_agent`
2. Follow the pattern in `weather_agent/` or `cocktail_agent/`:
   - `my_agent.py` - Agent definition with LlmAgent
   - `my_a2a_server.py` - A2A server with auto-registration
   - `start.py` - Startup script (use absolute imports)
   - `__init__.py` - Package marker
3. Add auto-registration in your A2A server
4. Define appropriate skills and capabilities in AgentCard
5. Add corresponding MCP tools in `mcp_server/` if needed
6. Update startup instructions in this README

**Important**: Use absolute imports in all new agent files to avoid import errors.

### Configuration

**Environment Variables**:
- `LOG_LEVEL`: DEBUG, INFO (default), WARNING, ERROR
- `REGISTRY_URL`: Registry server URL (default: http://localhost:8080)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key

**Network Ports**:
- **8000**: Planning Orchestrator Web Interface
- **8001**: Weather Agent Server
- **8002**: Cocktail Agent Server
- **8080**: FastAPI Registry Server

## 🚨 Troubleshooting

### Common Issues

**Port already in use**:
```bash
lsof -i :8080    # Find process using port 8080
lsof -i :8000    # Find process using port 8000
kill -9 <PID>    # Kill process
```

**Import/Module errors**:
- Ensure you're in the correct directory (`a2a_orchestrator/`)
- Use the exact commands shown above (relative imports are fixed)
- Check that all dependencies are installed: `uv sync`

**Agent registration failures**:
- Start registry first and wait for "Uvicorn running" message
- Wait 3-5 seconds between starting each service
- Check registry logs in Terminal 1 for registration confirmations

**"Connection closed" in web interface**:
- Check all 4 services are running (registry, weather, cocktail, orchestrator)
- Look for error messages in Terminal 4 (orchestrator logs)
- Try refreshing the browser and reconnecting

**Google Cloud authentication**:
```bash
gcloud auth application-default login
gcloud auth list  # Verify authentication
gcloud config set project YOUR_PROJECT_ID
```

**MCP Server errors**:
- All MCP server paths are now absolute (fixed in recent updates)
- If you see "can't find weather.py" errors, restart the orchestrator

### Stopping the System
Stop in reverse order:
1. Terminal 4 (orchestrator) - Ctrl+C
2. Terminals 2-3 (agents) - Ctrl+C
3. Terminal 1 (registry) - Ctrl+C

## 📚 Documentation

- **[API Reference](docs/api/API_REFERENCE.md)**: Complete API documentation
- **[Testing Guide](docs/testing/MANUAL_TESTING_GUIDE.md)**: Manual testing procedures
- **Project Instructions**: See `CLAUDE.md` for development guidelines

## 🤝 Contributing

1. Follow existing code patterns and structure
2. Add comprehensive logging to new components
3. Update documentation for new features
4. Test using the manual testing guide

## 📄 License

Part of the Google ADK samples collection. See individual file headers for licensing information.