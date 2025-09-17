"""
FastAPI-based in-memory agent registry for A2A agent discovery.

This module provides a lightweight registry server using FastAPI with in-memory storage.
The registry maintains agent-url → agent-card mappings and supports heartbeat monitoring.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging with structured format
import os
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AgentCard(BaseModel):
    """Agent card model for registration."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: Dict = Field(default_factory=dict)
    skills: List[Dict] = Field(default_factory=list)


class AgentRegistration(BaseModel):
    """Request model for agent registration."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: Dict = Field(default_factory=dict)
    skills: List[Dict] = Field(default_factory=list)


class HeartbeatRequest(BaseModel):
    """Request model for agent heartbeat."""
    url: str


class RegistryStatus(BaseModel):
    """Response model for registry status."""
    total_agents: int
    active_agents: int
    registry_uptime: float


class InMemoryAgentRegistry:
    """
    In-memory agent registry with heartbeat monitoring.

    This registry maintains agent state in memory only - all data is lost on restart.
    Agents must re-register when the registry restarts.
    """

    def __init__(self, heartbeat_timeout: int = 30, cleanup_interval: int = 10):
        """
        Initialize the registry.

        Args:
            heartbeat_timeout: Seconds after which an agent is considered stale
            cleanup_interval: Seconds between cleanup runs
        """
        self.agents: Dict[str, AgentCard] = {}  # agent-url → agent-card
        self.last_seen: Dict[str, float] = {}   # agent-url → timestamp
        self.heartbeat_timeout = heartbeat_timeout
        self.cleanup_interval = cleanup_interval
        self.start_time = time.time()
        self.cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"🚀 Started cleanup task (timeout={self.heartbeat_timeout}s, interval={self.cleanup_interval}s)")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("🛑 Stopped cleanup task")

    async def _cleanup_loop(self):
        """Background task to remove stale agents."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_stale_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")

    async def cleanup_stale_agents(self) -> int:
        """Remove agents that haven't sent heartbeats recently."""
        current_time = time.time()
        stale_agents = []

        for url, last_seen in self.last_seen.items():
            if current_time - last_seen > self.heartbeat_timeout:
                stale_agents.append(url)

        for url in stale_agents:
            agent_name = self.agents.get(url, {}).name if url in self.agents else "unknown"
            self.unregister_agent(url)
            logger.warning(f"🗑️ Removed stale agent: {agent_name} at {url}")

        return len(stale_agents)

    def register_agent(self, registration: AgentRegistration) -> AgentCard:
        """Register an agent in the registry."""
        agent_card = AgentCard(**registration.dict())
        self.agents[registration.url] = agent_card
        self.last_seen[registration.url] = time.time()

        logger.info(f"✅ Registered agent: {registration.name} at {registration.url}")
        return agent_card

    def unregister_agent(self, url: str) -> bool:
        """Unregister an agent from the registry."""
        if url in self.agents:
            agent_name = self.agents[url].name
            del self.agents[url]
            self.last_seen.pop(url, None)
            logger.info(f"🚫 Unregistered agent: {agent_name} at {url}")
            return True
        return False

    def update_heartbeat(self, url: str) -> bool:
        """Update the heartbeat timestamp for an agent."""
        if url in self.agents:
            self.last_seen[url] = time.time()
            logger.debug(f"Updated heartbeat for agent at {url}")
            return True
        return False

    def get_all_agents(self) -> List[AgentCard]:
        """Get all registered agents."""
        return list(self.agents.values())

    def get_agent(self, url: str) -> Optional[AgentCard]:
        """Get a specific agent by URL."""
        return self.agents.get(url)

    def get_status(self) -> RegistryStatus:
        """Get registry status information."""
        current_time = time.time()
        active_agents = sum(
            1 for last_seen in self.last_seen.values()
            if current_time - last_seen <= self.heartbeat_timeout
        )

        return RegistryStatus(
            total_agents=len(self.agents),
            active_agents=active_agents,
            registry_uptime=current_time - self.start_time
        )


# Global registry instance
registry = InMemoryAgentRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the FastAPI application."""
    # Startup
    await registry.start_cleanup_task()
    logger.info("FastAPI Agent Registry started")

    yield

    # Shutdown
    await registry.stop_cleanup_task()
    logger.info("FastAPI Agent Registry stopped")


# Create FastAPI app
app = FastAPI(
    title="A2A Agent Registry",
    description="In-memory agent registry for A2A agent discovery",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/registry/register", response_model=AgentCard, status_code=201)
async def register_agent(registration: AgentRegistration):
    """Register a new agent with the registry."""
    try:
        agent_card = registry.register_agent(registration)
        return agent_card
    except Exception as e:
        logger.error(f"❌ Error registering agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/registry/register", response_model=AgentCard)
async def reregister_agent(registration: AgentRegistration):
    """Re-register an existing agent or register a new one."""
    try:
        agent_card = registry.register_agent(registration)
        return agent_card
    except Exception as e:
        logger.error(f"❌ Error re-registering agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/registry/agents", response_model=List[AgentCard])
async def list_agents():
    """List all registered agents."""
    return registry.get_all_agents()


@app.get("/registry/agents/{url:path}", response_model=AgentCard)
async def get_agent(url: str):
    """Get a specific agent by URL."""
    agent = registry.get_agent(url)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with URL '{url}' not found")
    return agent


@app.post("/registry/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """Handle agent heartbeat."""
    if registry.update_heartbeat(request.url):
        return {"success": True, "message": "Heartbeat updated"}
    else:
        raise HTTPException(status_code=404, detail="Agent not registered")


@app.delete("/registry/unregister/{url:path}")
async def unregister_agent(url: str):
    """Unregister an agent by URL."""
    if registry.unregister_agent(url):
        return {"success": True, "message": f"Agent {url} unregistered"}
    else:
        raise HTTPException(status_code=404, detail=f"Agent with URL '{url}' not found")


@app.get("/registry/status", response_model=RegistryStatus)
async def get_registry_status():
    """Get registry status and statistics."""
    return registry.get_status()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "registry": "running"}


if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI Agent Registry on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)