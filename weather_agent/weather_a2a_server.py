import uvicorn
import logging
import asyncio
import os
from dotenv import load_dotenv

# Configure logging with structured format
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

from weather_agent.weather_agent import create_weather_agent
from registry_service.auto_registration import AutoRegistration, AgentInfo

load_dotenv()

async def main():
    logger.info("🌦️ Starting A2A Weather Agent Server with Auto-Registration...")

    # Create the weather agent
    root_agent = create_weather_agent()

    # Create ADK runner
    runner = Runner(
        app_name="weather_agent",
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
    )

    # Create A2A executor
    a2a_executor = A2aAgentExecutor(runner=runner)

    # Define agent skill with more detailed examples
    skill = AgentSkill(
        id='weather_forecast',
        name='Weather Forecast',
        description='Get weather forecasts and alerts for US locations using National Weather Service data.',
        tags=['weather', 'forecast', 'alerts', 'nws', 'temperature', 'conditions'],
        examples=[
            'what is the weather for san francisco',
            'weather forecast for new york',
            'any weather alerts for chicago',
            'temperature in seattle today',
            'will it rain in miami tomorrow',
            'weather conditions in denver'
        ],
    )

    # Create agent card
    public_agent_card = AgentCard(
        name='Weather Agent',
        description='A specialized agent for weather forecasts and alerts using National Weather Service API.',
        url='http://localhost:8001',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=False,
    )

    # Create auto-registration info
    agent_info = AgentInfo(
        name=public_agent_card.name,
        description=public_agent_card.description,
        url=public_agent_card.url,
        version=public_agent_card.version,
        capabilities={
            "weather_forecast": True,
            "nws_integration": True,
            "location_based": True,
            "supports_streaming": True
        },
        skills=[{
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "tags": skill.tags,
            "examples": skill.examples
        }]
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=a2a_executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    # Setup auto-registration
    auto_registration = AutoRegistration(
        agent_info=agent_info,
        registry_url="http://localhost:8080",
        heartbeat_interval=15
    )

    logger.info("⚙️ Weather Agent Server configured, starting auto-registration...")

    try:
        # Start auto-registration
        await auto_registration.start()
        logger.info("✅ Weather agent registered with FastAPI registry")

        # Start server
        config = uvicorn.Config(
            server.build(),
            host="0.0.0.0",
            port=8001,
            timeout_keep_alive=300,
            timeout_graceful_shutdown=300,
            access_log=True,
            log_level="info"
        )
        server_instance = uvicorn.Server(config)

        logger.info("🚀 Starting uvicorn server on http://localhost:8001")
        await server_instance.serve()

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down weather agent server...")
    finally:
        # Clean up auto-registration
        await auto_registration.stop()
        logger.info("✅ Weather agent unregistered and cleaned up")


if __name__ == '__main__':
    asyncio.run(main())