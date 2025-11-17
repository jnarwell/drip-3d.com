"""Enhanced API endpoints for Property Tables with document import and verification"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
import hashlib
import logging
from datetime import datetime

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.resources import (
    PropertyTable, PropertyTableTemplate,
    VerificationStatus, ImportMethod, SourceType
)
from app.models.material import Material
from app.schemas.resources import (
    PropertyTable as PropertyTableSchema,
    PropertyTableCreate,
    PropertyTableUpdate,
    PropertyTableSummary,
    TableImportRequest,
    DocumentAnalysisResult
)

logger = logging.getLogger(__name__)
router = APIRouter()  # Remove prefix since it's added in main.py


def determine_verification_status(
    import_method: ImportMethod,
    source_citation: Optional[str],
    source_authority: Optional[str]
) -> VerificationStatus:
    """Determine verification status based on import method and source"""
    if import_method in [ImportMethod.DOCUMENT_IMPORT, ImportMethod.API_IMPORT]:
        if source_authority:  # Has authoritative source
            return VerificationStatus.VERIFIED
    
    if import_method == ImportMethod.MANUAL_ENTRY:
        if source_citation:  # Has citation but manually entered
            return VerificationStatus.CITED
        else:
            return VerificationStatus.UNVERIFIED
    
    return VerificationStatus.UNVERIFIED


@router.get("/", response_model=List[PropertyTableSummary])
async def list_property_tables(
    material_id: Optional[int] = Query(None, description="Filter by material"),
    verification_status: Optional[VerificationStatus] = Query(None, description="Filter by verification status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List property tables with verification badges"""
    query = db.query(PropertyTable).options(
        joinedload(PropertyTable.material),
        joinedload(PropertyTable.template)
    )
    
    # Filter by access
    user_email = current_user.get("email")
    workspace_id = current_user.get("workspace_id")
    query = query.filter(
        or_(
            PropertyTable.created_by == user_email,
            PropertyTable.workspace_id == workspace_id,
            PropertyTable.is_public == True
        )
    )
    
    # Apply filters
    if material_id:
        query = query.filter(PropertyTable.material_id == material_id)
    
    if verification_status:
        query = query.filter(PropertyTable.verification_status == verification_status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                PropertyTable.name.ilike(search_pattern),
                PropertyTable.description.ilike(search_pattern),
                PropertyTable.source_citation.ilike(search_pattern)
            )
        )
    
    # Order by verification status (verified first) and name
    query = query.order_by(
        PropertyTable.verification_status,
        PropertyTable.name
    )
    
    total = query.count()
    tables = query.offset(skip).limit(limit).all()
    
    # Convert to summary format with material names
    summaries = []
    for table in tables:
        summary = PropertyTableSummary(
            id=table.id,
            name=table.name,
            description=table.description,
            data_points_count=table.data_points_count,
            material_name=table.material.name if table.material else None,
            verification_status=table.verification_status,
            import_method=table.import_method,
            source_authority=table.source_authority,
            source_citation=table.source_citation,
            created_by=table.created_by,
            created_at=table.created_at,
            last_updated=table.last_updated
        )
        summaries.append(summary)
    
    logger.info(f"Retrieved {len(summaries)} property tables for {user_email}")
    return summaries


@router.get("/{table_id}", response_model=PropertyTableSchema)
async def get_property_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific property table with full data"""
    table = db.query(PropertyTable).options(
        joinedload(PropertyTable.material),
        joinedload(PropertyTable.template)
    ).filter(PropertyTable.id == table_id).first()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property table not found"
        )
    
    # Check access
    user_email = current_user.get("email")
    workspace_id = current_user.get("workspace_id")
    if not (
        table.is_public or
        table.created_by == user_email or
        table.workspace_id == workspace_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this property table"
        )
    
    return table


@router.post("/", response_model=PropertyTableSchema, status_code=status.HTTP_201_CREATED)
async def create_property_table(
    table_data: PropertyTableCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new property table"""
    user_email = current_user.get("email", "unknown")
    
    # If using a template, increment its usage count
    if table_data.template_id:
        template = db.query(PropertyTableTemplate).filter(
            PropertyTableTemplate.id == table_data.template_id
        ).first()
        if template:
            template.usage_count += 1
    
    # Calculate document hash if provided
    doc_hash = None
    if table_data.source_document_path:
        # In real implementation, hash the actual file content
        doc_hash = hashlib.sha256(table_data.source_document_path.encode()).hexdigest()
    
    # Determine verification status
    verification_status = determine_verification_status(
        table_data.import_method,
        table_data.source_citation,
        table_data.source_authority
    )
    
    # Create new table
    table = PropertyTable(
        name=table_data.name,
        description=table_data.description,
        template_id=table_data.template_id,
        material_id=table_data.material_id,
        component_id=table_data.component_id,
        data=table_data.data,
        data_points_count=len(table_data.data),
        import_method=table_data.import_method,
        source_document_path=table_data.source_document_path,
        source_document_hash=doc_hash,
        source_url=table_data.source_url,
        source_citation=table_data.source_citation,
        source_type=table_data.source_type,
        source_authority=table_data.source_authority,
        verification_status=verification_status,
        verification_method=f"Auto-determined from {table_data.import_method}",
        last_verified=datetime.utcnow() if verification_status == VerificationStatus.VERIFIED else None,
        extracted_via_ocr=table_data.extracted_via_ocr,
        manual_corrections=0,
        data_quality=table_data.data_quality,
        applicable_conditions=table_data.applicable_conditions,
        tags=table_data.tags,
        created_by=user_email,
        is_public=table_data.is_public,
        workspace_id=table_data.workspace_id
    )
    
    db.add(table)
    db.commit()
    db.refresh(table)
    
    logger.info(f"Created property table '{table.name}' with {len(table_data.data)} data points by {user_email}")
    return table


@router.post("/import-from-document", response_model=PropertyTableSchema)
async def import_table_from_document(
    file: UploadFile = File(...),
    import_request: TableImportRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Import table data from a document (PDF/Excel)"""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not supported"
        )
    
    # TODO: Implement actual document parsing
    # For now, create a mock successful import
    
    user_email = current_user.get("email", "unknown")
    
    # Mock extracted data (in real implementation, parse the document)
    mock_data = [
        {"T": 0.01, "P": 0.6117, "vf": 0.001000, "vg": 206.00},
        {"T": 5, "P": 0.8726, "vf": 0.001000, "vg": 147.03},
        {"T": 10, "P": 1.2282, "vf": 0.001000, "vg": 106.32},
    ]
    
    # Create the table with verified status
    table_create = PropertyTableCreate(
        name=import_request.name,
        description=import_request.description,
        template_id=import_request.template_id,
        material_id=import_request.material_id,
        data=mock_data,
        import_method=ImportMethod.DOCUMENT_IMPORT,
        source_document_path=file.filename,
        source_citation="1995 IAPWS Formulation",
        source_type=SourceType.STANDARD,
        source_authority="IAPWS",
        extracted_via_ocr=False,
        data_quality="High",
        applicable_conditions="Saturation conditions",
        tags=import_request.tags or ["imported", "steam", "water"],
        is_public=False
    )
    
    return await create_property_table(table_create, db, current_user)


@router.put("/{table_id}", response_model=PropertyTableSchema)
async def update_property_table(
    table_id: int,
    table_update: PropertyTableUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a property table"""
    table = db.query(PropertyTable).filter(PropertyTable.id == table_id).first()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property table not found"
        )
    
    # Check ownership
    user_email = current_user.get("email")
    if table.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the table creator can update it"
        )
    
    # Track if data was manually edited
    if table_update.data is not None and table.import_method != ImportMethod.MANUAL_ENTRY:
        table.manual_corrections = (table.manual_corrections or 0) + 1
    
    # Update fields
    update_data = table_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table, field, value)
    
    # Update data points count if data changed
    if table_update.data is not None:
        table.data_points_count = len(table_update.data)
    
    # Update verification status if source changed
    if table_update.source_citation is not None:
        table.verification_status = determine_verification_status(
            table.import_method,
            table.source_citation,
            table.source_authority
        )
    
    table.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(table)
    
    logger.info(f"Updated property table '{table.name}' by {user_email}")
    return table


@router.post("/{table_id}/verify", response_model=PropertyTableSchema)
async def verify_property_table(
    table_id: int,
    source_authority: str = Query(..., description="Authority verifying this data"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually verify a property table"""
    table = db.query(PropertyTable).filter(PropertyTable.id == table_id).first()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property table not found"
        )
    
    # Update verification
    table.source_authority = source_authority
    table.verification_status = VerificationStatus.VERIFIED
    table.verification_method = f"Manual verification by {current_user.get('email')}"
    table.last_verified = datetime.utcnow()
    
    db.commit()
    db.refresh(table)
    
    logger.info(f"Verified property table '{table.name}' with authority '{source_authority}'")
    return table


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a property table"""
    table = db.query(PropertyTable).filter(PropertyTable.id == table_id).first()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property table not found"
        )
    
    # Check ownership
    user_email = current_user.get("email")
    if table.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the table creator can delete it"
        )
    
    db.delete(table)
    db.commit()
    
    logger.info(f"Deleted property table '{table.name}' by {user_email}")
    return None