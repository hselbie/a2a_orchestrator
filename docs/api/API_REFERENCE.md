# API Reference: A2A Dynamic Orchestrator

This document provides comprehensive API documentation for all components of the A2A Dynamic Orchestrator system.

## FastAPI Registry API

Base URL: `http://localhost:8080`

### Health and Status Endpoints

#### GET /health
Check registry health status.

**Response:**
```json
{
  "status": "healthy",
  "registry": "running"
}
```

**Status Codes:**
- `200`: Registry is healthy
- `500`: Registry has issues

#### GET /registry/status
Get detailed registry statistics.

**Response:**
```json
{
  "total_agents": 2,
  "active_agents": 2,
  "registry_uptime": 123.456789
}
```

**Fields:**
- `total_agents`: Total number of registered agents
- `active_agents`: Number of agents with recent heartbeats
- `registry_uptime`: Registry uptime in seconds

### Agent Management Endpoints

#### GET /registry/agents
List all registered agents.

**Response:**
```json
[
  {
    "name": "Weather Agent",
    "description": "A specialized agent for weather forecasts and alerts using National Weather Service API.",
    "url": "http://localhost:8001",
    "version": "1.0.0",
    "capabilities": {
      "weather_forecast": true,
      "nws_integration": true,
      "location_based": true,
      "supports_streaming": true
    },
    "skills": [
      {
        "id": "weather_forecast",
        "name": "Weather Forecast",
        "description": "Get weather forecasts and alerts for US locations using National Weather Service data.",
        "tags": ["weather", "forecast", "alerts", "nws", "temperature", "conditions"],
        "examples": [
          "what is the weather for san francisco",
          "weather forecast for new york",
          "any weather alerts for chicago"
        ]
      }
    ],
    "last_heartbeat": "2024-01-01T12:00:00.000Z",
    "registration_time": "2024-01-01T11:45:00.000Z"
  }
]
```

#### GET /registry/agents/{agent_url:path}
Get specific agent by URL.

**Parameters:**
- `agent_url`: URL-encoded agent URL

**Example:**
```bash
curl "http://localhost:8080/registry/agents/http://localhost:8001"
```

**Response:** Same format as single agent from list above

**Status Codes:**
- `200`: Agent found
- `404`: Agent not found

#### POST /registry/register
Register a new agent.

**Request Body:**
```json
{
  "name": "My Agent",
  "description": "Agent description",
  "url": "http://localhost:9000",
  "version": "1.0.0",
  "capabilities": {
    "feature1": true,
    "feature2": false
  },
  "skills": [
    {
      "id": "skill1",
      "name": "Skill Name",
      "description": "Skill description",
      "tags": ["tag1", "tag2"],
      "examples": ["example query 1", "example query 2"]
    }
  ]
}
```

**Required Fields:**
- `name`: Agent display name
- `description`: Agent description
- `url`: Agent endpoint URL

**Optional Fields:**
- `version`: Agent version (default: "1.0.0")
- `capabilities`: Key-value capability map
- `skills`: Array of skill definitions

**Response:** Echo of registered agent data with timestamps

**Status Codes:**
- `200`: Agent registered successfully
- `400`: Invalid request data
- `422`: Validation error

#### POST /registry/heartbeat
Send heartbeat for an agent.

**Request Body:**
```json
{
  "url": "http://localhost:8001"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Heartbeat updated"
}
```

**Status Codes:**
- `200`: Heartbeat recorded
- `404`: Agent not found

#### DELETE /registry/unregister/{agent_url:path}
Unregister an agent.

**Parameters:**
- `agent_url`: URL-encoded agent URL

**Response:**
```json
{
  "success": true,
  "message": "Agent http://localhost:8001 unregistered"
}
```

**Status Codes:**
- `200`: Agent unregistered
- `404`: Agent not found

## Planning Orchestrator WebSocket API

Base URL: `ws://localhost:8000`

### WebSocket Endpoint

#### WS /ws/{session_id}
Main client communication endpoint.

**Parameters:**
- `session_id`: Unique session identifier

**Connection Flow:**
1. Client connects to WebSocket
2. Server accepts connection and creates session
3. Client sends text messages
4. Server processes via planning orchestrator
5. Server sends JSON responses

**Client Message Format:**
```
"What's the weather in San Francisco?"
```

**Server Response Format:**
```json
{
  "message": "Based on the current weather data for San Francisco, CA:\n\n🌤️ **Current Conditions**: Partly cloudy, 65°F\n📊 **Today's Forecast**: High 72°F, Low 58°F\n🌧️ **Precipitation**: 10% chance of rain\n💨 **Wind**: 8 mph from the west\n\nToday looks like a great day with mild temperatures and mostly clear skies!"
}
```

**Connection Events:**
- Connection accepted: Session created automatically
- Message received: Processed by planning orchestrator
- Disconnect: Session cleaned up automatically

## Agent Server APIs

### Weather Agent Server

Base URL: `http://localhost:8001`

#### GET /.well-known/agent-card.json
Get agent card information.

**Response:**
```json
{
  "name": "Weather Agent",
  "description": "A specialized agent for weather forecasts and alerts using National Weather Service API.",
  "version": "1.0.0",
  "capabilities": {
    "weather_forecast": true,
    "nws_integration": true,
    "location_based": true,
    "supports_streaming": true
  },
  "skills": [...]
}
```

#### POST /run
Execute agent with user input (A2A protocol).

**Request Body:**
```json
{
  "user_input": "What's the weather in San Francisco?",
  "session_id": "session123"
}
```

**Response:** Streaming response with weather data

### Cocktail Agent Server

Base URL: `http://localhost:8002`

Similar API structure to Weather Agent, but focused on cocktail recipes and bartending information.

## MCP Server Tools

The orchestrator uses MCP (Model Control Protocol) servers for direct tool execution.

### Weather MCP Tools

Available through `weather_toolset` in the orchestrator:

- `get_weather_forecast`: Get weather forecast for a location
- `get_weather_alerts`: Get weather alerts for an area
- `get_current_conditions`: Get current weather conditions

### Cocktail MCP Tools

Available through `cocktail_toolset` in the orchestrator:

- `search_cocktails`: Search for cocktail recipes
- `get_cocktail_recipe`: Get detailed recipe for a specific cocktail
- `get_ingredient_info`: Get information about cocktail ingredients

## Planning Tools API

These tools are used internally by the planning orchestrator.

### create_execution_plan(user_query, tool_context)

Creates an execution plan based on user query and available agents.

**Parameters:**
- `user_query`: User's original query string
- `tool_context`: ADK tool context

**Returns:**
```json
{
  "success": true,
  "plan": {
    "user_query": "What's the weather in San Francisco?",
    "intent": "weather information",
    "selected_agent": {
      "name": "Weather Agent",
      "url": "http://localhost:8001",
      "score": 0.85,
      "reasoning": "Score 0.85: name matches intent, skill 'Weather Forecast' matches"
    },
    "execution_method": "mcp_tool",
    "tool_name": "weather_tools",
    "parameters": {
      "query": "What's the weather in San Francisco?"
    },
    "alternatives": [
      {
        "name": "Alternative Agent",
        "url": "http://localhost:8003",
        "score": 0.45
      }
    ]
  }
}
```

### list_available_agents(tool_context)

Get all registered agents from the registry.

**Returns:**
```json
{
  "total_agents": 2,
  "agents": [
    {
      "name": "Weather Agent",
      "description": "Weather forecasting agent",
      "url": "http://localhost:8001",
      "capabilities": ["weather_forecast", "nws_integration"],
      "skills": ["Weather Forecast"]
    }
  ]
}
```

### get_registry_status(tool_context)

Get current registry status.

**Returns:**
```
"Registry status: {'total_agents': 2, 'active_agents': 2, 'registry_uptime': 123.45}"
```

## Error Responses

### Common Error Formats

**Registry API Errors:**
```json
{
  "detail": "Agent not found"
}
```

**Planning Tool Errors:**
```json
{
  "error": "Failed to retrieve agents: HTTP 500",
  "plan": null
}
```

**WebSocket Errors:**
- Connection failures result in automatic reconnection attempts
- Processing errors are logged server-side and generic error messages sent to client

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request - Invalid input data
- `404`: Not Found - Resource doesn't exist
- `422`: Unprocessable Entity - Validation error
- `500`: Internal Server Error - Server-side error

## Rate Limiting and Timeouts

### Registry Configuration

- **Heartbeat Timeout**: 30 seconds (configurable)
- **Cleanup Interval**: 10 seconds (configurable)
- **Request Timeout**: No explicit limit (uses FastAPI defaults)

### Agent Server Configuration

- **Heartbeat Interval**: 15 seconds (configurable)
- **Registration Retry**: 3 attempts with exponential backoff
- **A2A Request Timeout**: ADK default timeouts

### WebSocket Configuration

- **Connection Timeout**: 60 seconds
- **Message Processing**: No explicit timeout (depends on agent response time)
- **Reconnection**: Automatic on disconnect

## Authentication and Security

### Current Implementation

- **No Authentication**: Development setup with no auth requirements
- **Local Network**: Designed for localhost/development use
- **HTTP Only**: No HTTPS/TLS encryption

### Production Considerations

For production deployment, consider adding:

- API key authentication for registry endpoints
- OAuth 2.0 for client authentication
- TLS/HTTPS encryption for all communications
- Rate limiting per client/session
- Input validation and sanitization
- CORS configuration for web clients

## SDK and Client Libraries

### Python Client Example

```python
import asyncio
import websockets
import json

async def chat_with_orchestrator():
    uri = "ws://localhost:8000/ws/my_session"
    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send("What's the weather in Paris?")

        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print(data["message"])

asyncio.run(chat_with_orchestrator())
```

### Registry Client Example

```python
import requests

# List agents
response = requests.get("http://localhost:8080/registry/agents")
agents = response.json()

# Register agent
agent_data = {
    "name": "My Agent",
    "description": "Test agent",
    "url": "http://localhost:9000"
}
response = requests.post("http://localhost:8080/registry/register", json=agent_data)
```

## Development and Testing

### Testing Endpoints

Use the manual testing guide for comprehensive testing procedures, or test individual endpoints:

```bash
# Test registry health
curl http://localhost:8080/health

# Test agent listing
curl http://localhost:8080/registry/agents

# Test WebSocket (requires wscat or similar)
wscat -c ws://localhost:8000/ws/test_session
```

### Monitoring and Debugging

- Check server logs for detailed execution traces
- Use browser developer tools for WebSocket debugging
- Monitor registry endpoints for agent health status
- Review agent server logs for registration and heartbeat status