"""FraudIntel API Server — Main FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles

from agent.config import settings
from agent.database import (
    check_connection,
    close_connection,
    ensure_indexes,
    get_collection_stats,
)
from agent.mcp_client import mcp_client
from api.routes.dashboard import router as dashboard_router
from api.routes.investigations import router as investigations_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.log_level))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("🛡️ FraudIntel API starting up...")
    connected = await check_connection()
    if connected:
        logger.info("✅ MongoDB connected")
        await ensure_indexes()
        stats = await get_collection_stats()
        logger.info(f"📊 Collections: {stats}")
    else:
        logger.warning("⚠️ MongoDB not connected — some features will be unavailable")
        
    try:
        await mcp_client.connect()
        logger.info("✅ MongoDB MCP Server connected — all database "
                     "operations will be routed through MCP")
    except Exception as e:
        logger.warning("⚠️ MCP client unavailable: %s — using pymongo "
                       "fallback", e)
        
    yield
    # Shutdown
    await mcp_client.disconnect()
    await close_connection()
    logger.info("👋 FraudIntel API shut down")


app = FastAPI(
    title="FraudIntel API",
    description=(
        "AI Fraud Investigation Agent — Multi-agent system for financial "
        "fraud investigation powered by Gemini and MongoDB"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    # print(f"DEBUG: Headers: {request.headers}, api_key: {api_key}")
    expected_key = os.environ.get("API_KEY", "fi-hackathon-2026-secret")
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

# API Routes (register BEFORE static files)
app.include_router(investigations_router, dependencies=[Depends(verify_api_key)])
app.include_router(dashboard_router, dependencies=[Depends(verify_api_key)])


@app.get("/api", tags=["Root"])
async def api_root():
    """API information and available endpoints."""
    return {
        "name": "FraudIntel API",
        "version": "1.0.0",
        "description": "AI Fraud Investigation Agent",
        "endpoints": {
            "investigate": "POST /api/investigate",
            "cases": "GET /api/cases",
            "alerts": "GET /api/alerts",
            "network": "GET /api/network/{entity_id}",
            "dashboard_stats": "GET /api/dashboard/stats",
            "health": "GET /api/health",
        },
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    connected = await check_connection()
    stats = await get_collection_stats() if connected else {}
    return {
        "status": "ok" if connected else "degraded",
        "mongodb_connected": connected,
        "collections": stats,
        "version": "1.0.0",
    }


# Static files — Mount LAST so API routes take priority
local_dev_dir = Path(__file__).parent.parent.parent / "frontend"
docker_dir = Path(__file__).parent.parent / "frontend"

if local_dev_dir.exists():
    app.mount("/", StaticFiles(directory=str(local_dev_dir), html=True), name="dashboard")
elif docker_dir.exists():
    app.mount("/", StaticFiles(directory=str(docker_dir), html=True), name="dashboard")
else:
    logger.warning("Frontend directory not found. Static files will not be served.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.server:app", host=settings.app_host, port=settings.app_port, reload=True)
