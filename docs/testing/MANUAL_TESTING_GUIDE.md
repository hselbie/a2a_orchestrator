# Manual Testing Guide: FastAPI Registry & Auto-Registration

This guide walks you through manually testing the FastAPI agent registry and auto-registration functionality.

## Prerequisites

Ensure you have the following dependencies installed:
```bash
pip install fastapi uvicorn aiohttp pydantic
```

## Step 1: Start the FastAPI Registry Server

Open a terminal and run:
```bash
python fastapi_registry.py
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Started cleanup task (timeout=30s, interval=10s)
INFO:     FastAPI Agent Registry started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

The registry is now running on **http://localhost:8080**

## Step 2: Test Registry Health

In a new terminal, test the registry health endpoint:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"healthy","registry":"running"}
```

## Step 3: Check Registry Status

Get the current registry status:

```bash
curl http://localhost:8080/registry/status
```

Expected response (no agents registered yet):
```json
{
  "total_agents": 0,
  "active_agents": 0,
  "registry_uptime": 5.123456
}
```

## Step 4: Test Manual Agent Registration

Register a test agent manually:

```bash
curl -X POST http://localhost:8080/registry/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "description": "A test agent for manual testing",
    "url": "http://localhost:9999",
    "version": "1.0.0",
    "capabilities": {"test": true},
    "skills": [{"id": "test_skill", "name": "Test Skill"}]
  }'
```

Expected response:
```json
{
  "name": "Test Agent",
  "description": "A test agent for manual testing",
  "url": "http://localhost:9999",
  "version": "1.0.0",
  "capabilities": {"test": true},
  "skills": [{"id": "test_skill", "name": "Test Skill"}]
}
```

## Step 5: List Registered Agents

Check that your test agent was registered:

```bash
curl http://localhost:8080/registry/agents
```

Expected response:
```json
[
  {
    "name": "Test Agent",
    "description": "A test agent for manual testing",
    "url": "http://localhost:9999",
    "version": "1.0.0",
    "capabilities": {"test": true},
    "skills": [{"id": "test_skill", "name": "Test Skill"}]
  }
]
```

## Step 6: Get Specific Agent

Retrieve the specific agent by URL:

```bash
curl "http://localhost:8080/registry/agents/http://localhost:9999"
```

Expected response: Same as above.

## Step 7: Test Heartbeat

Send a heartbeat for the test agent:

```bash
curl -X POST http://localhost:8080/registry/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:9999"}'
```

Expected response:
```json
{"success": true, "message": "Heartbeat updated"}
```

## Step 8: Test Auto-Registration with Weather Agent

Start the weather agent server in a new terminal:

```bash
python weather_a2a_server.py
```

You should see logs indicating:
```
INFO:Starting A2A Weather Agent Server with Auto-Registration...
INFO:Weather Agent Server configured, starting auto-registration...
INFO:Successfully registered agent: Weather Agent at http://localhost:8001
INFO:✅ Weather agent registered with FastAPI registry
INFO:🚀 Starting uvicorn server on http://localhost:8001
```

## Step 9: Verify Auto-Registration

Check that the weather agent auto-registered:

```bash
curl http://localhost:8080/registry/agents
```

You should now see both the test agent and weather agent:
```json
[
  {
    "name": "Test Agent",
    "description": "A test agent for manual testing",
    "url": "http://localhost:9999",
    "version": "1.0.0",
    "capabilities": {"test": true},
    "skills": [{"id": "test_skill", "name": "Test Skill"}]
  },
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
          "any weather alerts for chicago",
          "temperature in seattle today",
          "will it rain in miami tomorrow",
          "weather conditions in denver"
        ]
      }
    ]
  }
]
```

## Step 10: Test Auto-Registration with Cocktail Agent

Start the cocktail agent server in another terminal:

```bash
python cocktail_a2a_server.py
```

Similar logs should appear for the cocktail agent.

## Step 11: Verify Both Agents

List agents again to see all three (test + weather + cocktail):

```bash
curl http://localhost:8080/registry/agents
```

## Step 12: Check Registry Status

Check the updated registry status:

```bash
curl http://localhost:8080/registry/status
```

Expected response (with active agents):
```json
{
  "total_agents": 3,
  "active_agents": 3,
  "registry_uptime": 123.456789
}
```

## Step 13: Test Heartbeat Monitoring

Wait for heartbeats to be sent automatically (every 15 seconds). You should see logs in the agent terminals like:
```
DEBUG:Heartbeat sent for agent: Weather Agent
DEBUG:Heartbeat sent for agent: Cocktail Agent
```

## Step 14: Test Manual Unregistration

Remove the test agent:

```bash
curl -X DELETE "http://localhost:8080/registry/unregister/http://localhost:9999"
```

Expected response:
```json
{"success": true, "message": "Agent http://localhost:9999 unregistered"}
```

## Step 15: Test Auto-Cleanup (Optional)

To test stale agent cleanup:

1. Register a test agent (Step 4)
2. Don't send heartbeats for it
3. Wait 40+ seconds
4. Check the agent list - the test agent should be automatically removed

## Step 16: Test Agent Shutdown and Auto-Unregistration

Stop one of the agent servers (Ctrl+C in the weather agent terminal).

You should see cleanup logs:
```
INFO:🛑 Shutting down weather agent server...
INFO:Successfully unregistered agent: Weather Agent
INFO:✅ Weather agent unregistered and cleaned up
```

Then verify it's removed from the registry:

```bash
curl http://localhost:8080/registry/agents
```

## Step 17: Explore the FastAPI Documentation

Visit the auto-generated API docs:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

These provide interactive documentation for all endpoints.

## Common Testing Commands Summary

```bash
# Health check
curl http://localhost:8080/health

# Registry status
curl http://localhost:8080/registry/status

# List all agents
curl http://localhost:8080/registry/agents

# Get specific agent
curl "http://localhost:8080/registry/agents/http://localhost:8001"

# Manual registration
curl -X POST http://localhost:8080/registry/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Test agent","url":"http://localhost:9999"}'

# Send heartbeat
curl -X POST http://localhost:8080/registry/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"url":"http://localhost:9999"}'

# Unregister agent
curl -X DELETE "http://localhost:8080/registry/unregister/http://localhost:9999"
```

## Troubleshooting

**Registry won't start:**
- Check port 8080 is available: `lsof -i :8080`
- Install missing dependencies: `pip install fastapi uvicorn`

**Agent won't register:**
- Ensure registry is running first
- Check agent logs for error messages
- Verify network connectivity between agent and registry

**Heartbeats failing:**
- Check if agent is actually registered first
- Look for 404 responses (agent not found)
- Verify registry is still running

**Auto-cleanup too aggressive:**
- Increase `heartbeat_timeout` in `fastapi_registry.py`
- Decrease `heartbeat_interval` in agent auto-registration

This completes the manual testing of the FastAPI registry system!