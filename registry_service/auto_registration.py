"""
Auto-registration component for A2A agent servers.

This module provides utilities for agents to automatically register themselves
with the agent registry on startup and maintain heartbeats.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import aiohttp
from pydantic import BaseModel

# Configure logging with structured format
import os
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Information needed to register an agent."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: Dict[str, Any] = None
    skills: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = {}
        if self.skills is None:
            self.skills = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": self.capabilities,
            "skills": self.skills
        }


class RegistrationError(Exception):
    """Exception raised when agent registration fails."""
    pass


class AutoRegistration:
    """
    Auto-registration manager for A2A agent servers.

    Handles:
    - Initial registration with the registry
    - Periodic heartbeat maintenance
    - Automatic re-registration on registry restart
    - Graceful shutdown and unregistration
    """

    def __init__(
        self,
        agent_info: AgentInfo,
        registry_url: str = "http://localhost:8080",
        heartbeat_interval: int = 15,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the auto-registration manager.

        Args:
            agent_info: Information about the agent to register
            registry_url: URL of the registry server
            heartbeat_interval: Seconds between heartbeat requests
            max_retries: Maximum number of retry attempts for registration
            retry_delay: Seconds to wait between retry attempts
        """
        self.agent_info = agent_info
        self.registry_url = registry_url.rstrip("/")
        self.heartbeat_interval = heartbeat_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.is_registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the auto-registration process."""
        self.session = aiohttp.ClientSession()

        # Register with the registry
        await self.register()

        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"🚀 Auto-registration started for agent: {self.agent_info.name}")

    async def stop(self):
        """Stop the auto-registration process and cleanup."""
        # Signal shutdown
        self.shutdown_event.set()

        # Stop heartbeat task
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Unregister from registry
        if self.is_registered:
            await self.unregister()

        # Close HTTP session
        if self.session:
            await self.session.close()

        logger.info(f"🛑 Auto-registration stopped for agent: {self.agent_info.name}")

    async def register(self) -> bool:
        """Register the agent with the registry."""
        url = f"{self.registry_url}/registry/register"

        for attempt in range(self.max_retries):
            try:
                async with self.session.post(url, json=self.agent_info.to_dict()) as response:
                    if response.status in (200, 201):
                        self.is_registered = True
                        logger.info(f"✅ Successfully registered agent: {self.agent_info.name} at {self.agent_info.url}")
                        return True
                    else:
                        text = await response.text()
                        logger.warning(f"⚠️ Registration failed (attempt {attempt + 1}): {response.status} - {text}")

            except Exception as e:
                logger.warning(f"⚠️ Registration attempt {attempt + 1} failed: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)

        logger.error(f"❌ Failed to register agent after {self.max_retries} attempts")
        raise RegistrationError(f"Failed to register agent: {self.agent_info.name}")

    async def unregister(self) -> bool:
        """Unregister the agent from the registry."""
        if not self.is_registered:
            return True

        url = f"{self.registry_url}/registry/unregister/{self.agent_info.url}"

        try:
            async with self.session.delete(url) as response:
                if response.status == 200:
                    self.is_registered = False
                    logger.info(f"✅ Successfully unregistered agent: {self.agent_info.name}")
                    return True
                else:
                    text = await response.text()
                    logger.warning(f"⚠️ Unregistration failed: {response.status} - {text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error during unregistration: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Send a heartbeat to the registry."""
        if not self.is_registered:
            return False

        url = f"{self.registry_url}/registry/heartbeat"
        payload = {"url": self.agent_info.url}

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.debug(f"Heartbeat sent for agent: {self.agent_info.name}")
                    return True
                elif response.status == 404:
                    # Agent not found in registry - need to re-register
                    logger.warning(f"⚠️ Agent not found in registry, re-registering: {self.agent_info.name}")
                    self.is_registered = False
                    await self.register()
                    return self.is_registered
                else:
                    text = await response.text()
                    logger.warning(f"💔 Heartbeat failed: {response.status} - {text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error sending heartbeat: {e}")
            return False

    async def _heartbeat_loop(self):
        """Background task for sending periodic heartbeats."""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=self.heartbeat_interval
                )
                # If we reach here, shutdown was requested
                break
            except asyncio.TimeoutError:
                # Normal timeout - send heartbeat
                await self.send_heartbeat()

    async def check_registry_health(self) -> bool:
        """Check if the registry is healthy and reachable."""
        url = f"{self.registry_url}/health"

        try:
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Registry health check failed: {e}")
            return False


# Convenience function for simple usage
async def register_agent_on_startup(
    agent_info: AgentInfo,
    registry_url: str = "http://localhost:8080",
    heartbeat_interval: int = 15
) -> AutoRegistration:
    """
    Convenience function to register an agent and start heartbeats.

    Args:
        agent_info: Agent information for registration
        registry_url: URL of the registry server
        heartbeat_interval: Seconds between heartbeats

    Returns:
        AutoRegistration instance (use as async context manager)
    """
    auto_reg = AutoRegistration(
        agent_info=agent_info,
        registry_url=registry_url,
        heartbeat_interval=heartbeat_interval
    )
    await auto_reg.start()
    return auto_reg


# Example usage helper
def create_agent_info_from_a2a_server(
    name: str,
    description: str,
    server_url: str,
    skills: List[Dict[str, Any]] = None,
    capabilities: Dict[str, Any] = None
) -> AgentInfo:
    """
    Create AgentInfo from A2A server parameters.

    Args:
        name: Agent name
        description: Agent description
        server_url: URL where the agent server is running
        skills: List of agent skills
        capabilities: Agent capabilities

    Returns:
        AgentInfo instance ready for registration
    """
    return AgentInfo(
        name=name,
        description=description,
        url=server_url,
        skills=skills or [],
        capabilities=capabilities or {}
    )