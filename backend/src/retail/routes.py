"""Stateless retail preview endpoints; proposals must pass geometric checks."""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from .layout import RetailLayout, export_dxf, validate_layout
from .generation import SpaceUnavailable, propose_layout

router = APIRouter(prefix="/api/v1/retail", tags=["retail"])

class GenerateRequest(BaseModel):
    layout: RetailLayout
    instructions: str = Field(min_length=1, max_length=4000)

@router.post("/validate")
def validate(layout: RetailLayout):
    issues = validate_layout(layout)
    return {"valid": not issues, "issues": issues, "scope": "declared_geometry_only"}

@router.post("/export.dxf")
def export(layout: RetailLayout):
    issues = validate_layout(layout)
    if issues:
        raise HTTPException(status_code=422, detail=issues)
    return Response(content=export_dxf(layout), media_type="application/dxf", headers={"Content-Disposition": 'attachment; filename="retail-layout.dxf"'})

@router.post("/generate")
def generate(request: GenerateRequest):
    try:
        proposal = propose_layout(request.layout, request.instructions)
    except SpaceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"layout": proposal.model_dump(), "valid": True, "provider": "huggingface-gradio-space"}
