import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .body_limit import BodyLimitMiddleware
from .models import PlanRequest
from .planner import plan_group
from .preview import PreviewProvider
from .qloo import QlooClient, QlooError


def create_app(qloo=None):
    app = FastAPI(title="Common Ground", version="0.1.0")
    app.state.qloo = qloo or QlooClient()
    app.state.live_validated = False
    preview = PreviewProvider()
    recent = defaultdict(deque)

    @app.middleware("http")
    async def request_budget(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            try:
                length = int(request.headers.get("content-length", "0"))
            except ValueError:
                return JSONResponse({"detail": "Invalid request length."}, status_code=400)
            if length > 16384:
                return JSONResponse({"detail": "Request too large."}, status_code=413)
            if request.url.path in ("/api/search", "/api/plan"):
                now = time.monotonic()
                # A global cap avoids unbounded address storage and protects the free API key.
                queue = recent["all"]
                while queue and queue[0] < now - 60:
                    queue.popleft()
                if len(queue) >= 30:
                    return JSONResponse(
                        {"detail": "Query limit reached. Retry in a minute."}, status_code=429
                    )
                queue.append(now)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https: data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    @app.exception_handler(QlooError)
    async def qloo_failure(_request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=503)

    @app.get("/api/status")
    async def status():
        return {
            "qloo_configured": app.state.qloo.configured,
            "live_validated": app.state.live_validated,
            "preview_label": "Fictional preview, not Qloo data",
        }

    @app.get("/api/search")
    async def search(
        query: str = Query(min_length=2, max_length=100),
        source: Literal["qloo", "synthetic"] = "qloo",
    ):
        provider = app.state.qloo if source == "qloo" else preview
        try:
            rows = await provider.search(query)
        except ValueError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)
        return {"source": source, "results": [row.model_dump() for row in rows]}

    @app.post("/api/plan")
    async def plan(request: PlanRequest):
        provider = app.state.qloo if request.source == "qloo" else preview
        try:
            result = await plan_group(request, provider)
            if request.source == "qloo":
                app.state.live_validated = True
            return result
        except ValueError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=422)

    frontend = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    app.add_middleware(BodyLimitMiddleware)
    hosts = ["127.0.0.1", "localhost", "testserver"]
    hosts.extend(
        host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()
    )
    render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if render_host and "*" not in render_host and "/" not in render_host:
        hosts.append(render_host)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    return app


app = create_app()
