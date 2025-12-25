"""API endpoints for Engineering Properties lookups."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.properties import (
    lookup,
    list_sources,
    list_views,
    get_source,
    generate_view
)
from app.services.properties.router import (
    LookupError,
    get_available_outputs,
    get_required_inputs
)

router = APIRouter(prefix="/api/v1/eng-properties", tags=["engineering-properties"])


# Request/Response schemas

class LookupRequest(BaseModel):
    """Request for a property lookup."""
    source_id: str
    output: str
    inputs: Dict[str, Any]


class LookupResponse(BaseModel):
    """Response from a property lookup."""
    value: float
    source_id: str
    output: str
    inputs: Dict[str, Any]


class SourceSummary(BaseModel):
    """Summary info about a property source."""
    id: str
    name: str
    category: str
    description: Optional[str]
    type: str
    source: str
    inputs: List[dict]
    outputs: List[dict]
    view_count: int
    column_count: int
    lookup_source_id: Optional[str] = None


class ViewSummary(BaseModel):
    """Summary info about a view."""
    id: str
    name: str
    description: Optional[str]
    layout: str
    column_count: int


# Endpoints

@router.get("/sources", response_model=List[SourceSummary])
async def get_sources(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List all available property sources.

    Returns summary information about each source including
    available inputs and outputs.
    """
    sources = list_sources()

    if category:
        sources = [s for s in sources if s['category'] == category]

    return sources


@router.get("/sources/{source_id}")
async def get_source_detail(source_id: str):
    """
    Get detailed information about a property source.

    Includes full input/output definitions and available views.
    """
    try:
        source = get_source(source_id)
        return {
            'id': source.id,
            'name': source.name,
            'category': source.category,
            'description': source.description,
            'type': source.type,
            'source': source.source,
            'source_url': source.source_url,
            'version': source.version,
            'inputs': [i.model_dump() for i in source.inputs],
            'outputs': [o.model_dump() for o in source.outputs],
            'views': [
                {
                    'id': v.id,
                    'name': v.name,
                    'description': v.description,
                    'layout': v.layout
                }
                for v in source.views
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sources/{source_id}/inputs")
async def get_source_inputs(source_id: str):
    """Get the required inputs for a property source."""
    try:
        return get_required_inputs(source_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sources/{source_id}/outputs")
async def get_source_outputs(source_id: str):
    """Get the available outputs for a property source."""
    try:
        return get_available_outputs(source_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sources/{source_id}/views", response_model=List[ViewSummary])
async def get_source_views(source_id: str):
    """List available views for a property source."""
    try:
        return list_views(source_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sources/{source_id}/views/{view_id}")
async def get_view_data(source_id: str, view_id: str):
    """
    Generate and return a table view.

    Returns a structured table with headers and rows that can be
    displayed directly in the UI.
    """
    try:
        return generate_view(source_id, view_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lookup", response_model=LookupResponse)
async def lookup_property(request: LookupRequest):
    """
    Look up a property value.

    This is the main lookup endpoint. Provide a source ID, output name,
    and input values to get a property value back.

    Example request:
    ```json
    {
        "source_id": "steam",
        "output": "h",
        "inputs": {"T": 373.15, "P": 101325}
    }
    ```
    """
    try:
        value = lookup(request.source_id, request.output, **request.inputs)
        return LookupResponse(
            value=value,
            source_id=request.source_id,
            output=request.output,
            inputs=request.inputs
        )
    except LookupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")


@router.get("/fluids")
async def get_coolprop_fluids():
    """
    List all available CoolProp fluids.

    These can be used with library-type property sources.
    """
    try:
        from app.services.properties.backends.coolprop import list_coolprop_fluids, CoolPropError
        fluids = list_coolprop_fluids()
        return {"fluids": fluids, "count": len(fluids)}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"CoolProp not available: {str(e)}"
        )


@router.get("/categories")
async def get_categories():
    """Get list of property source categories."""
    return {
        "categories": [
            {"id": "structural", "name": "Structural", "description": "Steel shapes, sections"},
            {"id": "material", "name": "Materials", "description": "Material properties"},
            {"id": "process", "name": "Process/Fluids", "description": "Thermodynamic properties"},
            {"id": "mechanical", "name": "Mechanical", "description": "Keyways, O-rings, etc."},
            {"id": "electrical", "name": "Electrical", "description": "Wire gauges, resistivity"},
            {"id": "fasteners", "name": "Fasteners", "description": "Bolts, nuts, threads"},
            {"id": "tolerances", "name": "Tolerances", "description": "ISO tolerances, fits"},
            {"id": "finishes", "name": "Surface Finishes", "description": "Roughness values"},
            {"id": "standards", "name": "Standards", "description": "Code requirements"}
        ]
    }


@router.post("/reload")
async def reload_sources():
    """
    Reload all property sources from disk.

    Useful during development when YAML files are modified.
    """
    from app.services.properties.registry import reload_sources as do_reload
    do_reload()
    sources = list_sources()
    return {"message": "Reloaded", "source_count": len(sources)}
