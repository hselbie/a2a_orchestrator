#!/usr/bin/env python3
"""
System test script for the A2A Dynamic Orchestrator.

This script performs basic health checks and functionality tests
to verify the system is working correctly.
"""

import asyncio
import json
import logging
import os
import sys
import aiohttp
import websockets

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SystemTester:
    """Test suite for the A2A Dynamic Orchestrator system."""

    def __init__(self):
        self.registry_url = "http://localhost:8080"
        self.orchestrator_ws = "ws://localhost:8000/ws/test_session"
        self.test_results = []

    async def test_component(self, name: str, test_func):
        """Run a test component and track results."""
        logger.info(f"🧪 Testing {name}...")
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {name}: PASSED")
                self.test_results.append((name, True, None))
            else:
                logger.error(f"❌ {name}: FAILED")
                self.test_results.append((name, False, "Test returned False"))
        except Exception as e:
            logger.error(f"❌ {name}: ERROR - {e}")
            self.test_results.append((name, False, str(e)))

    async def test_registry_health(self) -> bool:
        """Test registry health endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
                return False

    async def test_registry_agents(self) -> bool:
        """Test that agents are registered."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/registry/agents") as response:
                if response.status == 200:
                    agents = await response.json()
                    # Should have at least weather and cocktail agents
                    agent_names = [agent.get("name", "") for agent in agents]
                    has_weather = any("weather" in name.lower() for name in agent_names)
                    has_cocktail = any("cocktail" in name.lower() for name in agent_names)
                    logger.info(f"📋 Found {len(agents)} agents: {agent_names}")
                    return has_weather and has_cocktail
                return False

    async def test_registry_status(self) -> bool:
        """Test registry status endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/registry/status") as response:
                if response.status == 200:
                    status = await response.json()
                    total_agents = status.get("total_agents", 0)
                    active_agents = status.get("active_agents", 0)
                    logger.info(f"📊 Registry status: {total_agents} total, {active_agents} active agents")
                    return total_agents >= 2 and active_agents >= 2
                return False

    async def test_orchestrator_websocket(self) -> bool:
        """Test orchestrator WebSocket connection."""
        try:
            async with websockets.connect(self.orchestrator_ws) as websocket:
                # Test connection
                logger.info("🔌 WebSocket connected successfully")
                return True
        except Exception as e:
            logger.error(f"🔌 WebSocket connection failed: {e}")
            return False

    async def test_weather_query(self) -> bool:
        """Test weather query through orchestrator."""
        try:
            async with websockets.connect(self.orchestrator_ws) as websocket:
                # Send weather query
                test_query = "What's the weather in San Francisco?"
                await websocket.send(test_query)
                logger.info(f"📤 Sent: {test_query}")

                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                message = data.get("message", "")

                logger.info(f"📥 Received response ({len(message)} chars)")
                # Check if response contains weather-related content
                weather_keywords = ["weather", "temperature", "forecast", "conditions"]
                has_weather_content = any(keyword in message.lower() for keyword in weather_keywords)

                return has_weather_content and len(message) > 50

        except asyncio.TimeoutError:
            logger.error("⏰ Weather query timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Weather query failed: {e}")
            return False

    async def test_cocktail_query(self) -> bool:
        """Test cocktail query through orchestrator."""
        try:
            async with websockets.connect(self.orchestrator_ws) as websocket:
                # Send cocktail query
                test_query = "How do I make a margarita?"
                await websocket.send(test_query)
                logger.info(f"📤 Sent: {test_query}")

                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                message = data.get("message", "")

                logger.info(f"📥 Received response ({len(message)} chars)")
                # Check if response contains cocktail-related content
                cocktail_keywords = ["margarita", "cocktail", "drink", "recipe", "ingredient"]
                has_cocktail_content = any(keyword in message.lower() for keyword in cocktail_keywords)

                return has_cocktail_content and len(message) > 50

        except asyncio.TimeoutError:
            logger.error("⏰ Cocktail query timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Cocktail query failed: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all system tests."""
        logger.info("🚀 Starting A2A Dynamic Orchestrator System Tests")
        logger.info("=" * 60)

        # Registry tests
        await self.test_component("Registry Health", self.test_registry_health)
        await self.test_component("Agent Registration", self.test_registry_agents)
        await self.test_component("Registry Status", self.test_registry_status)

        # Orchestrator tests
        await self.test_component("WebSocket Connection", self.test_orchestrator_websocket)
        await self.test_component("Weather Query", self.test_weather_query)
        await self.test_component("Cocktail Query", self.test_cocktail_query)

        # Summary
        logger.info("=" * 60)
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        logger.info(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All tests PASSED! System is working correctly.")
            return True
        else:
            logger.error("❌ Some tests FAILED:")
            for name, success, error in self.test_results:
                if not success:
                    logger.error(f"   • {name}: {error}")
            return False

async def main():
    """Main test execution."""
    tester = SystemTester()

    try:
        success = await tester.run_all_tests()
        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("🔄 Tests interrupted")
        return 1
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)