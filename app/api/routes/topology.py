"""Topology dashboard route.

Renders the committed Azure topology diagram. The Mermaid source is shipped
to the browser and rendered client-side; the SVG export (if present) is
embedded directly for faster first paint.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from app.core.auth import User, get_current_user
from app.core.personas import can_view_page
from app.core.templates import templates
from app.core.tenant_context import get_brand_context_for_request

router = APIRouter(tags=["pages"], dependencies=[Depends(get_current_user)])

_DIAGRAMS_DIR = Path(__file__).resolve().parents[3] / "docs" / "diagrams"


@router.get("/topology", response_class=HTMLResponse)
async def topology_page(request: Request, user: User = Depends(get_current_user)):
    """Azure infrastructure topology visualisation."""
    if not can_view_page(user, "topology"):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Persona does not grant access to 'topology'",
        )
    brand_context = get_brand_context_for_request(request)
    svg_path = _DIAGRAMS_DIR / "topology.svg"
    has_svg = svg_path.exists()
    return templates.TemplateResponse(
        request,
        "pages/topology.html",
        {
            **brand_context,
            "visible_pages": {"*"},
            "page_key": "topology",
            "has_svg": has_svg,
        },
    )


@router.get("/topology/mermaid", response_class=PlainTextResponse)
async def topology_mermaid() -> Response:
    """Serve the raw Mermaid source for client-side rendering."""
    path = _DIAGRAMS_DIR / "topology.mmd"
    if not path.exists():
        return PlainTextResponse('%% topology not generated yet\nflowchart TB\n  n["no data"]\n')
    return PlainTextResponse(path.read_text(encoding="utf-8"))


@router.get("/topology/svg")
async def topology_svg() -> Response:
    """Serve the SVG export when the weekly workflow has generated it."""
    path = _DIAGRAMS_DIR / "topology.svg"
    if not path.exists():
        return Response(status_code=404)
    return Response(content=path.read_bytes(), media_type="image/svg+xml")
