"""
Contacts API - CRUD endpoints for team and external contacts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from pydantic import BaseModel
import os

from app.db.database import get_db
from app.models.contact import Contact

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ContactCreateRequest(BaseModel):
    name: str
    organization: Optional[str] = None
    expertise: Optional[List[str]] = None
    email: str  # Required primary email
    secondary_email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_internal: bool = False
    user_id: Optional[int] = None


class ContactUpdateRequest(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None
    expertise: Optional[List[str]] = None
    email: Optional[str] = None
    secondary_email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_internal: Optional[bool] = None
    user_id: Optional[int] = None


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================

@router.get("")
async def list_contacts(
    is_internal: Optional[bool] = Query(None, description="Filter by internal/external"),
    search: Optional[str] = Query(None, description="Search in name, organization, expertise"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List contacts with optional filters.

    Returns contacts sorted by name alphabetically.
    """
    query = db.query(Contact)

    # Apply filters
    if is_internal is not None:
        query = query.filter(Contact.is_internal == is_internal)

    if search:
        search_pattern = f"%{search}%"
        # Search in name, organization, email, and expertise (JSON array as text)
        query = query.filter(
            or_(
                Contact.name.ilike(search_pattern),
                Contact.organization.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
                Contact.expertise.cast(String).ilike(search_pattern)
            )
        )

    # Get total count
    total = query.count()

    # Get paginated results
    contacts = query.order_by(Contact.name).offset(offset).limit(limit).all()

    return {
        "contacts": [c.to_dict() for c in contacts],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("")
async def create_contact(
    data: ContactCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new contact.

    - Set is_internal=True and provide user_id to link to an existing user
    - Set is_internal=False for external contacts (vendors, suppliers, etc.)
    """
    user_email = current_user["email"]

    # Create contact
    contact = Contact(
        name=data.name,
        organization=data.organization,
        expertise=data.expertise,
        email=data.email,
        secondary_email=data.secondary_email,
        phone=data.phone,
        notes=data.notes,
        is_internal=data.is_internal,
        user_id=data.user_id if data.is_internal else None,
        created_by=user_email
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact.to_dict()


@router.get("/{contact_id}")
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single contact by ID."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact.to_dict()


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: int,
    data: ContactUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Update fields
    if data.name is not None:
        contact.name = data.name

    if data.organization is not None:
        contact.organization = data.organization

    if data.expertise is not None:
        contact.expertise = data.expertise

    if data.email is not None:
        contact.email = data.email

    if data.secondary_email is not None:
        contact.secondary_email = data.secondary_email

    if data.phone is not None:
        contact.phone = data.phone

    if data.notes is not None:
        contact.notes = data.notes

    if data.is_internal is not None:
        contact.is_internal = data.is_internal
        # Clear user_id if switching to external
        if not data.is_internal:
            contact.user_id = None

    if data.user_id is not None and contact.is_internal:
        contact.user_id = data.user_id

    db.commit()
    db.refresh(contact)

    return contact.to_dict()


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a contact."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()

    return {"deleted": True, "id": contact_id}


# Import String for cast operation
from sqlalchemy import String
