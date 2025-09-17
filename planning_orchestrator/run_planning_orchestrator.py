"""
Run script for the planning-based dynamic orchestrator.

This version uses the planning/execution pattern instead of trying to
directly call RemoteA2aAgent.run_async().
"""

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from starlette.websockets import WebSocketDisconnect
import json

from .planning_orchestrator_agent import create_planning_orchestrator_agent

load_dotenv()

APP_NAME = "ADK Planning-Based Dynamic Orchestrator"
STATIC_DIR = Path("../static")

session_service = InMemorySessionService()
artifacts_service = InMemoryArtifactService()

async def process_message_with_runner(runner: Runner, session_id: str, question: str):
    """Processes a single message using the provided runner."""
    logging.info(f"🎯 PLANNING ORCHESTRATOR PROCESSING: User query received")
    logging.info(f"   Session: {session_id}")
    logging.info(f"   Query: {question}")

    content = types.Content(role="user", parts=[types.Part(text=question)])
    events_async = runner.run_async(
        session_id=session_id, user_id=session_id, new_message=content
    )

    response_parts = []
    event_count = 0
    async for event in events_async:
        event_count += 1
        if event.content.role == "model" and event.content.parts[0].text:
            event_text = event.content.parts[0].text
            print(f"[planning-orchestrator-event-{event_count}]:", event_text)
            logging.info(f"📢 PLANNING ORCHESTRATOR EVENT #{event_count}: {event_text[:100]}...")
            response_parts.append(event_text)

    logging.info(f"✅ PLANNING ORCHESTRATOR COMPLETE: Generated {len(response_parts)} response parts from {event_count} events")
    return response_parts

async def run_planning_orchestrator_session(websocket: WebSocket, session_id: str):
    """Handles client-to-orchestrator communication over WebSocket for a session."""
    logging.info(f"🚀 PLANNING ORCHESTRATOR SESSION: Starting planning orchestrator for session {session_id}")

    root_agent = create_planning_orchestrator_agent()
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        artifact_service=artifacts_service,
        session_service=session_service,
    )
    logging.info(f"✅ PLANNING ORCHESTRATOR SETUP: Runner and agent initialized for {session_id}")

    try:
        while True:
            logging.info(f"⏳ WEBSOCKET: Waiting for message from client {session_id}")
            text = await websocket.receive_text()
            logging.info(f"📨 WEBSOCKET: Received from {session_id}: '{text}'")

            response_parts = await process_message_with_runner(runner, session_id, text)
            if not response_parts:
                logging.warning(f"⚠️  PLANNING ORCHESTRATOR: No response generated for session {session_id}")
                continue

            # Send the text to the client
            ai_message = "\n".join(response_parts)
            logging.info(f"📤 WEBSOCKET: Sending response to {session_id}")
            logging.info(f"   Response length: {len(ai_message)} characters")
            logging.info(f"   Response preview: {ai_message[:100]}...")

            await websocket.send_text(json.dumps({"message": ai_message}))
            logging.info(f"✅ WEBSOCKET: Response sent successfully to {session_id}")

    except WebSocketDisconnect:
        logging.info(f"🔌 WEBSOCKET: Client {session_id} disconnected")
    finally:
        logging.info(f"🧹 CLEANUP: Closing runner for session {session_id}...")
        await runner.close()
        logging.info(f"✅ CLEANUP: Runner closed for session {session_id}. Planning orchestrator session ending.")

# FastAPI web app
app = FastAPI()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Client websocket endpoint"""
    await websocket.accept()
    logging.info(f"Client #{session_id} connected and WebSocket accepted.")

    try:
        # Create session
        await session_service.create_session(
            app_name=APP_NAME, user_id=session_id, session_id=session_id, state={}
        )
        logging.info(f"ADK Session created for {session_id}.")

        # Start planning orchestrator communication task
        await run_planning_orchestrator_session(websocket, session_id)

    except WebSocketDisconnect:
        logging.info(f"WebSocket endpoint for {session_id} detected disconnect.")
    finally:
        logging.info(f"WebSocket endpoint for session {session_id} is concluding.")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import os

    # Configure logging with structured format
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    print("Starting Planning-Based Dynamic Orchestrator on http://localhost:8000")
    print("Make sure the following are running:")
    print("  1. FastAPI registry: python fastapi_registry.py    # port 8080")
    print("  2. Weather agent: python weather_a2a_server.py     # port 8001")
    print("  3. Cocktail agent: python cocktail_a2a_server.py   # port 8002")
    print("")
    print("This orchestrator uses:")
    print("  - Planning tools to discover and select agents")
    print("  - Direct MCP tool execution (no A2A routing)")
    print("  - Registry-based dynamic discovery")
    uvicorn.run(app, host="0.0.0.0", port=8000)