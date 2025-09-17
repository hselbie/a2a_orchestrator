#!/usr/bin/env python3
"""Start script for Registry Service."""

if __name__ == "__main__":
    import uvicorn
    import logging
    import os

    # Configure logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting FastAPI Agent Registry on http://localhost:8080")

    from .fastapi_registry import app
    uvicorn.run(app, host="0.0.0.0", port=8080)