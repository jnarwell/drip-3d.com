"""API endpoints for Property Table Templates"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.resources import PropertyTableTemplate, TableType
from app.schemas.resources import (
    PropertyTableTemplate as PropertyTableTemplateSchema,
    PropertyTableTemplateCreate,
    PropertyTableTemplateUpdate,
    DocumentAnalysisResult
)

logger = logging.getLogger(__name__)
router = APIRouter()  # Remove prefix since it's added in main.py


@router.get("/", response_model=List[PropertyTableTemplateSchema])
async def list_templates(
    table_type: Optional[TableType] = Query(None, description="Filter by table type"),
    workspace_id: Optional[int] = Query(None, description="Filter by workspace"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List property table templates accessible to the current user"""
    query = db.query(PropertyTableTemplate)
    
    # Filter by access: user's own, workspace, or public
    user_email = current_user.get("email")
    if is_public is not None:
        query = query.filter(PropertyTableTemplate.is_public == is_public)
    else:
        # Show templates the user has access to
        query = query.filter(
            (PropertyTableTemplate.created_by == user_email) |
            (PropertyTableTemplate.workspace_id == workspace_id) |
            (PropertyTableTemplate.is_public == True)
        )
    
    if table_type:
        query = query.filter(PropertyTableTemplate.table_type == table_type)
    
    # Order by usage count (popular first) and name
    query = query.order_by(
        PropertyTableTemplate.usage_count.desc(),
        PropertyTableTemplate.name
    )
    
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(templates)} templates for {user_email}")
    return templates


@router.get("/{template_id}", response_model=PropertyTableTemplateSchema)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific property table template"""
    template = db.query(PropertyTableTemplate).filter(
        PropertyTableTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check access
    user_email = current_user.get("email")
    if not (
        template.is_public or 
        template.created_by == user_email or
        template.workspace_id == current_user.get("workspace_id")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this template"
        )
    
    return template


@router.post("/", response_model=PropertyTableTemplateSchema, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: PropertyTableTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new property table template"""
    user_email = current_user.get("email", "unknown")
    
    # Create new template
    template = PropertyTableTemplate(
        **template_data.dict(),
        created_by=user_email,
        usage_count=0
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info(f"Created new template '{template.name}' by {user_email}")
    return template


@router.post("/analyze-document", response_model=List[DocumentAnalysisResult])
async def analyze_document_for_templates(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a document (PDF/Excel) to extract table structures for template creation.
    This endpoint will parse the document and return detected table structures.
    """
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.ms-excel", 
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     "image/png", "image/jpeg"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not supported"
        )
    
    # TODO: Implement document parsing logic
    # For now, return mock data showing the expected structure
    
    # Example mock response for a steam table PDF
    mock_results = [
        DocumentAnalysisResult(
            table_name="Table B-1: Properties of Saturated Water (Temperature Table)",
            table_type=TableType.SINGLE_VAR_LOOKUP,
            independent_vars=[
                {"name": "Temperature", "symbol": "T", "unit": "°C", "description": "Temperature"}
            ],
            dependent_vars=[
                {"name": "Pressure", "symbol": "P", "unit": "kPa", "description": "Saturation pressure"},
                {"name": "Specific Volume (liquid)", "symbol": "vf", "unit": "m³/kg", "description": "Specific volume of saturated liquid"},
                {"name": "Specific Volume (vapor)", "symbol": "vg", "unit": "m³/kg", "description": "Specific volume of saturated vapor"},
                {"name": "Internal Energy (liquid)", "symbol": "uf", "unit": "kJ/kg", "description": "Specific internal energy of saturated liquid"},
                {"name": "Internal Energy (vapor)", "symbol": "ug", "unit": "kJ/kg", "description": "Specific internal energy of saturated vapor"},
            ],
            data_preview=[
                {"T": 0.01, "P": 0.6117, "vf": 0.001000, "vg": 206.00, "uf": 0.0, "ug": 2375.3},
                {"T": 5, "P": 0.8726, "vf": 0.001000, "vg": 147.03, "uf": 21.02, "ug": 2382.2},
            ],
            total_rows=53,
            source_info="Generated using EES with Steam_IAPWS (1995 IAPWS Formulation)",
            confidence_score=0.95,
            page_number=1,
            extraction_method="native_pdf"
        )
    ]
    
    logger.info(f"Document analysis requested by {current_user.get('email')}: {file.filename}")
    
    # In real implementation:
    # 1. Save uploaded file temporarily
    # 2. Use PDF parsing library (e.g., camelot, tabula-py) or Excel reader
    # 3. Extract table structures and data samples
    # 4. Detect source information from document text
    # 5. Return analysis results
    
    return mock_results


@router.put("/{template_id}", response_model=PropertyTableTemplateSchema)
async def update_template(
    template_id: int,
    template_update: PropertyTableTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a property table template"""
    template = db.query(PropertyTableTemplate).filter(
        PropertyTableTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check ownership
    user_email = current_user.get("email")
    if template.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the template creator can update it"
        )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    logger.info(f"Updated template '{template.name}' by {user_email}")
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a property table template"""
    template = db.query(PropertyTableTemplate).filter(
        PropertyTableTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check ownership
    user_email = current_user.get("email")
    if template.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the template creator can delete it"
        )
    
    # Check if template is in use
    if template.usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete template that has been used {template.usage_count} times"
        )
    
    db.delete(template)
    db.commit()
    
    logger.info(f"Deleted template '{template.name}' by {user_email}")
    return None


@router.post("/{template_id}/increment-usage", response_model=PropertyTableTemplateSchema)
async def increment_template_usage(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Increment the usage count of a template (called when creating a table from it)"""
    template = db.query(PropertyTableTemplate).filter(
        PropertyTableTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template.usage_count += 1
    db.commit()
    db.refresh(template)
    
    return template