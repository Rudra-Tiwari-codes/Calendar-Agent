from __future__ import annotations

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import JSONResponse, Response, FileResponse

from ..infra.db import db_ping
from .oauth import router as oauth_router
from ..infra.logging import get_logger
from ..infra.metrics import registry
import structlog


logger = get_logger().bind(service="http")


# metrics provided by infra.metrics


def create_app() -> FastAPI:
    app = FastAPI(title="Events Agent")

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or request.scope.get("trace_id") or str(id(request))
        structlog.contextvars.bind_contextvars(request_id=request_id, service="http")
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        return response

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True})

    @app.get("/readyz")
    async def readyz() -> JSONResponse:
        ready = await db_ping()
        status = 200 if ready else 503
        return JSONResponse({"db": ready, "ok": ready}, status_code=status)

    @app.get("/metrics")
    async def metrics() -> Response:
        content = generate_latest(registry)
        return Response(content=content, media_type=CONTENT_TYPE_LATEST)

    @app.get("/auth/success")
    async def auth_success() -> FileResponse:
        """Serve the auth success page for handling OAuth tokens"""
        # Get the path to the auth_success.html file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to the events-agent directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        auth_page_path = os.path.join(base_dir, "auth_success.html")
        
        if not os.path.exists(auth_page_path):
            logger.error("auth_success_page_not_found", path=auth_page_path)
            raise HTTPException(status_code=404, detail="Auth success page not found")
        
        return FileResponse(auth_page_path, media_type="text/html")

    app.include_router(oauth_router)

    return app


