#!/usr/bin/env python3
"""Start script for Planning Orchestrator."""

if __name__ == "__main__":
    import logging
    import os

    import uvicorn

    # Configure logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print("🚀 Starting Planning-Based Dynamic Orchestrator on http://localhost:8000")
    print("Make sure the following are running:")
    print(
        "  1. FastAPI registry: uv run python -m registry_service.fastapi_registry    # port 8080"
    )
    print("  2. Weather agent: uv run python -m weather_agent.start     # port 8001")
    print("  3. Cocktail agent: uv run python -m cocktail_agent.start   # port 8002")

    from .run_planning_orchestrator import app

    uvicorn.run(app, host="0.0.0.0", port=8000)
