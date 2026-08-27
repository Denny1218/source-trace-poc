"""Frontend dist path resolution and static file serving."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import PROJECT_ROOT
from app.core.logging import get_logger

logger = get_logger()

# Windows/Python 3.14 may map .js to text/plain via the registry.
# Browsers (especially type="module") need a JavaScript MIME type.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")


def get_frontend_dist_dir() -> Path:
    """Project-root-relative frontend/dist (independent of process cwd)."""
    return (PROJECT_ROOT / "frontend" / "dist").resolve()


def configure_frontend_static(app: FastAPI, dist_dir: Path | None = None) -> bool:
    """
    Mount Vite build assets and serve index.html at /.

    API routers must be registered before calling this function.
    Returns True when dist is available and static routes were added.
    """
    dist = (dist_dir if dist_dir is not None else get_frontend_dist_dir()).resolve()
    index_file = dist / "index.html"

    if not index_file.is_file():
        logger.warning("Frontend dist not found path=%s", dist)
        return False

    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="frontend-assets",
        )
    else:
        logger.warning("Frontend assets directory not found path=%s", assets_dir)

    # Offline brand assets (logo / favicon) — never CDN.
    brand_dir = dist / "brand"
    if brand_dir.is_dir():
        app.mount(
            "/static/brand",
            StaticFiles(directory=str(brand_dir)),
            name="brand-assets",
        )
    else:
        logger.warning("Frontend brand directory not found path=%s", brand_dir)

    favicon_ico = brand_dir / "favicon.ico"

    @app.get("/favicon.ico", include_in_schema=False)
    async def serve_favicon_ico() -> FileResponse:
        if not favicon_ico.is_file():
            raise HTTPException(status_code=404, detail="favicon not found")
        return FileResponse(favicon_ico, media_type="image/x-icon")

    @app.get("/", include_in_schema=False)
    async def serve_frontend_index() -> FileResponse:
        return FileResponse(index_file, media_type="text/html")

    logger.info("Frontend static files enabled path=%s", dist)
    return True
