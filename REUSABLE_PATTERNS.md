# Reusable Backend Infrastructure Patterns
## Extracted from drip-3d.com for 141-Tool Suite

**Source Project:** drip-3d.com (drip-team-portal)
**Stack:** FastAPI + React + PostgreSQL + Auth0
**Analysis Date:** 2025-12-20

---

## Quick Reference: New Tool Creation Path

```
1. Copy backend/app structure (models, api, schemas, services)
2. Copy frontend/src structure (pages, components, services, hooks)
3. Configure .env with database + auth
4. Define your models in /app/models/
5. Create schemas in /app/schemas/
6. Add routes in /app/api/v1/
7. Build React components for UI
8. Deploy to Railway
```

**Time to MVP:** ~2 hours for simple CRUD tool (with templates)

---

## 1. DATABASE LAYER PATTERNS

### Pattern 1.1: SQLAlchemy Base Model

**Location:** `backend/app/models/base.py`

```python
# PATTERN: Base Model with Common Fields
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimestampMixin:
    """Add to any model that needs audit timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# USAGE: class MyModel(Base, TimestampMixin):
```

### Pattern 1.2: Standard Entity Model

**Template:**

```python
# PATTERN: Standard Entity Model
# FILE: backend/app/models/your_entity.py

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum

class EntityStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class YourEntity(Base, TimestampMixin):
    __tablename__ = "your_entities"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Human-readable ID (for display)
    entity_id = Column(String(50), unique=True, index=True)

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(EntityStatus), default=EntityStatus.DRAFT)

    # Optional: Category/type classification
    category = Column(String(100))

    # Optional: Owner/creator tracking
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    # items = relationship("ChildItem", back_populates="parent")

# VARIATIONS:
# - Add unique constraints: __table_args__ = (UniqueConstraint('field1', 'field2'),)
# - Add composite indexes: Index('ix_combo', 'field1', 'field2')
# - Add JSON fields: Column(JSONB) for flexible data
```

### Pattern 1.3: Database Connection

**Location:** `backend/app/db/database.py`

```python
# PATTERN: Database Connection with Session Management
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Handle Railway's postgres:// vs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for scripts/services"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# USAGE IN ROUTES:
# @router.get("/items")
# def get_items(db: Session = Depends(get_db)):
#     return db.query(Item).all()
```

### Pattern 1.4: Many-to-Many Relationship

```python
# PATTERN: Association Table for M2M
from sqlalchemy import Table, Column, Integer, ForeignKey

# Association table (no ORM class needed for simple M2M)
entity_tags = Table(
    "entity_tags",
    Base.metadata,
    Column("entity_id", Integer, ForeignKey("entities.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)

# In Entity model:
# tags = relationship("Tag", secondary=entity_tags, back_populates="entities")
```

### Pattern 1.5: Audit Log Model

```python
# PATTERN: Universal Audit Log
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(100), nullable=False)  # "Component", "Test", etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # "CREATE", "UPDATE", "DELETE"
    changed_by = Column(String(255))  # User email
    changes = Column(JSONB)  # {"field": {"old": x, "new": y}}
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
    )
```

---

## 2. API ROUTE PATTERNS

### Pattern 2.1: Standard CRUD Router

**Template:**

```python
# PATTERN: Complete CRUD Router
# FILE: backend/app/api/v1/your_entities.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.your_entity import YourEntity, EntityStatus
from app.schemas.your_entity import (
    EntityCreate, EntityUpdate, EntityResponse, EntityListResponse
)
from app.core.security import get_current_user

router = APIRouter(prefix="/your-entities", tags=["your-entities"])

# LIST - GET /your-entities
@router.get("/", response_model=List[EntityListResponse])
def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[EntityStatus] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Remove if public
):
    query = db.query(YourEntity)

    # Filtering
    if status:
        query = query.filter(YourEntity.status == status)
    if category:
        query = query.filter(YourEntity.category == category)
    if search:
        query = query.filter(YourEntity.name.ilike(f"%{search}%"))

    # Pagination
    return query.order_by(YourEntity.created_at.desc()).offset(skip).limit(limit).all()

# GET ONE - GET /your-entities/{id}
@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

# CREATE - POST /your-entities
@router.post("/", response_model=EntityResponse, status_code=201)
def create_entity(
    entity_data: EntityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Generate unique entity_id if needed
    entity_id = generate_entity_id(db)  # Implement this helper

    entity = YourEntity(
        entity_id=entity_id,
        **entity_data.model_dump(),
        created_by=current_user.id
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity

# UPDATE - PATCH /your-entities/{id}
@router.patch("/{entity_id}", response_model=EntityResponse)
def update_entity(
    entity_id: int,
    entity_data: EntityUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Only update provided fields
    update_data = entity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    db.commit()
    db.refresh(entity)
    return entity

# DELETE - DELETE /your-entities/{id}
@router.delete("/{entity_id}", status_code=204)
def delete_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    entity = db.query(YourEntity).filter(YourEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db.delete(entity)
    db.commit()
    return None

# VARIATIONS:
# - Soft delete: entity.status = EntityStatus.ARCHIVED instead of db.delete()
# - Batch operations: POST /your-entities/batch with List[EntityCreate]
# - Status transitions: PATCH /your-entities/{id}/status with validation
```

### Pattern 2.2: Pydantic Schemas

```python
# PATTERN: Request/Response Schemas
# FILE: backend/app/schemas/your_entity.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EntityStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

# Base fields shared across schemas
class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None

# Create request (excludes auto-generated fields)
class EntityCreate(EntityBase):
    status: EntityStatus = EntityStatus.DRAFT

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

# Update request (all fields optional)
class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[EntityStatus] = None

# List response (minimal fields for performance)
class EntityListResponse(BaseModel):
    id: int
    entity_id: str
    name: str
    status: EntityStatus
    category: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

# Detail response (full fields + relationships)
class EntityResponse(EntityListResponse):
    description: Optional[str]
    updated_at: datetime
    # Add nested objects here
    # items: List[ItemResponse] = []
```

### Pattern 2.3: Authentication Middleware

```python
# PATTERN: Auth0 JWT Verification
# FILE: backend/app/core/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
import os

security = HTTPBearer()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
ALGORITHMS = ["RS256"]

# Cache JWKS keys
_jwks_cache = None

async def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
            _jwks_cache = response.json()
    return _jwks_cache

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)

        # Find matching key
        rsa_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )

        return {
            "sub": payload.get("sub"),
            "email": payload.get("email", payload.get(f"{AUTH0_API_AUDIENCE}/email")),
        }

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# DEV MODE BYPASS (for testing)
# FILE: backend/app/core/security_dev.py
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

async def get_current_user_dev():
    """Bypass auth for development"""
    return {"sub": "dev|123", "email": "test@drip-3d.com"}

# In main.py, conditionally use:
# if DEV_MODE:
#     app.dependency_overrides[get_current_user] = get_current_user_dev
```

### Pattern 2.4: FastAPI Main App Setup

```python
# PATTERN: FastAPI Application Entry Point
# FILE: backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.api.v1 import your_entities, other_routes
from app.db.database import engine
from app.models.base import Base

# Startup/shutdown lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if needed
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: Cleanup if needed

app = FastAPI(
    title="Your Tool API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(your_entities.router, prefix="/api/v1")
# app.include_router(other_routes.router, prefix="/api/v1")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

---

## 3. FRONTEND PATTERNS

### Pattern 3.1: API Service

```typescript
// PATTERN: Axios API Client
// FILE: frontend/src/services/api.ts

import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with defaults
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Entity-specific API functions
export const entityApi = {
  list: (params?: { status?: string; category?: string; search?: string }) =>
    api.get('/api/v1/your-entities', { params }),

  get: (id: number) =>
    api.get(`/api/v1/your-entities/${id}`),

  create: (data: EntityCreate) =>
    api.post('/api/v1/your-entities', data),

  update: (id: number, data: Partial<EntityCreate>) =>
    api.patch(`/api/v1/your-entities/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/v1/your-entities/${id}`),
};

export default api;
```

### Pattern 3.2: React Query Data Fetching

```typescript
// PATTERN: React Query Hooks
// FILE: frontend/src/hooks/useEntities.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { entityApi } from '@/services/api';
import { Entity, EntityCreate } from '@/types';

// List entities with filtering
export function useEntities(filters?: { status?: string; search?: string }) {
  return useQuery<Entity[]>({
    queryKey: ['entities', filters],
    queryFn: async () => {
      const { data } = await entityApi.list(filters);
      return data;
    },
    staleTime: 30000, // Consider data fresh for 30s
  });
}

// Get single entity
export function useEntity(id: number | undefined) {
  return useQuery<Entity>({
    queryKey: ['entity', id],
    queryFn: async () => {
      const { data } = await entityApi.get(id!);
      return data;
    },
    enabled: !!id, // Only fetch if id is provided
  });
}

// Create mutation
export function useCreateEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EntityCreate) => entityApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
    },
  });
}

// Update mutation
export function useUpdateEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<EntityCreate> }) =>
      entityApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
      queryClient.invalidateQueries({ queryKey: ['entity', id] });
    },
  });
}

// Delete mutation
export function useDeleteEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => entityApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
    },
  });
}
```

### Pattern 3.3: Page Component Structure

```tsx
// PATTERN: Standard List Page
// FILE: frontend/src/pages/Entities.tsx

import { useState } from 'react';
import { useEntities, useDeleteEntity } from '@/hooks/useEntities';
import { EntityForm } from '@/components/EntityForm';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorMessage } from '@/components/ErrorMessage';

export function EntitiesPage() {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [filters, setFilters] = useState({ status: '', search: '' });

  const { data: entities, isLoading, error } = useEntities(filters);
  const deleteEntity = useDeleteEntity();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message="Failed to load entities" />;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Entities</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Add Entity
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Search..."
          value={filters.search}
          onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
          className="px-3 py-2 border rounded"
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
          className="px-3 py-2 border rounded"
        >
          <option value="">All Status</option>
          <option value="DRAFT">Draft</option>
          <option value="ACTIVE">Active</option>
          <option value="ARCHIVED">Archived</option>
        </select>
      </div>

      {/* Table */}
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-3 text-left">ID</th>
            <th className="p-3 text-left">Name</th>
            <th className="p-3 text-left">Status</th>
            <th className="p-3 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {entities?.map((entity) => (
            <tr key={entity.id} className="border-b hover:bg-gray-50">
              <td className="p-3">{entity.entity_id}</td>
              <td className="p-3">{entity.name}</td>
              <td className="p-3">
                <StatusBadge status={entity.status} />
              </td>
              <td className="p-3">
                <button
                  onClick={() => setEditingId(entity.id)}
                  className="text-blue-600 hover:underline mr-2"
                >
                  Edit
                </button>
                <button
                  onClick={() => deleteEntity.mutate(entity.id)}
                  className="text-red-600 hover:underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Modal Form */}
      {(showForm || editingId) && (
        <EntityForm
          entityId={editingId}
          onClose={() => {
            setShowForm(false);
            setEditingId(null);
          }}
        />
      )}
    </div>
  );
}
```

### Pattern 3.4: Form Component with React Hook Form + Zod

```tsx
// PATTERN: Form with Validation
// FILE: frontend/src/components/EntityForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useEntity, useCreateEntity, useUpdateEntity } from '@/hooks/useEntities';

// Validation schema
const entitySchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().optional(),
  category: z.string().optional(),
  status: z.enum(['DRAFT', 'ACTIVE', 'ARCHIVED']),
});

type EntityFormData = z.infer<typeof entitySchema>;

interface EntityFormProps {
  entityId?: number | null;
  onClose: () => void;
}

export function EntityForm({ entityId, onClose }: EntityFormProps) {
  const { data: entity } = useEntity(entityId ?? undefined);
  const createEntity = useCreateEntity();
  const updateEntity = useUpdateEntity();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EntityFormData>({
    resolver: zodResolver(entitySchema),
    defaultValues: entity || {
      name: '',
      description: '',
      category: '',
      status: 'DRAFT',
    },
  });

  const onSubmit = async (data: EntityFormData) => {
    try {
      if (entityId) {
        await updateEntity.mutateAsync({ id: entityId, data });
      } else {
        await createEntity.mutateAsync(data);
      }
      onClose();
    } catch (error) {
      console.error('Failed to save entity:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">
          {entityId ? 'Edit Entity' : 'New Entity'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Name field */}
          <div>
            <label className="block text-sm font-medium mb-1">Name *</label>
            <input
              {...register('name')}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          {/* Description field */}
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              {...register('description')}
              rows={3}
              className="w-full px-3 py-2 border rounded"
            />
          </div>

          {/* Status field */}
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select {...register('status')} className="w-full px-3 py-2 border rounded">
              <option value="DRAFT">Draft</option>
              <option value="ACTIVE">Active</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### Pattern 3.5: Auth0 Provider Setup

```tsx
// PATTERN: Auth0 React Integration
// FILE: frontend/src/services/auth.tsx

import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { ReactNode } from 'react';

const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN;
const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID;
const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE;

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <Auth0Provider
      domain={AUTH0_DOMAIN}
      clientId={AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: AUTH0_AUDIENCE,
        scope: 'openid profile email',
      }}
    >
      {children}
    </Auth0Provider>
  );
}

// Hook for authenticated API calls
export function useAuthenticatedApi() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const getToken = async () => {
    if (!isAuthenticated) return null;
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Failed to get token:', error);
      return null;
    }
  };

  return { getToken, isAuthenticated };
}
```

### Pattern 3.6: TypeScript Types

```typescript
// PATTERN: TypeScript Type Definitions
// FILE: frontend/src/types/index.ts

export type EntityStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';

export interface Entity {
  id: number;
  entity_id: string;
  name: string;
  description?: string;
  category?: string;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface EntityCreate {
  name: string;
  description?: string;
  category?: string;
  status?: EntityStatus;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
```

---

## 4. INTEGRATION PATTERNS

### Pattern 4.1: External API Service (Materials Project Example)

```python
# PATTERN: External API Integration Service
# FILE: backend/app/services/external_api.py

import httpx
from typing import Optional, Dict, Any
import os

class ExternalAPIService:
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.api_key = os.getenv("EXTERNAL_API_KEY")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-KEY": self.api_key},
            timeout=30.0
        )

    async def search(self, query: str) -> Dict[str, Any]:
        response = await self.client.get("/search", params={"q": query})
        response.raise_for_status()
        return response.json()

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/items/{item_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def close(self):
        await self.client.aclose()

# Singleton instance
external_api = ExternalAPIService()

# In routes:
# @router.get("/external/{id}")
# async def get_external(id: str):
#     return await external_api.get_item(id)
```

### Pattern 4.2: Linear.com GraphQL Integration

```python
# PATTERN: GraphQL API Client
# FILE: backend/app/services/linear.py

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
TEAM_ID = os.getenv("LINEAR_TEAM_ID")
PROJECT_ID = os.getenv("LINEAR_PROJECT_ID")

transport = AIOHTTPTransport(
    url="https://api.linear.app/graphql",
    headers={"Authorization": LINEAR_API_KEY}
)

client = Client(transport=transport, fetch_schema_from_transport=True)

async def create_issue(title: str, description: str, priority: int = 2):
    mutation = gql("""
        mutation CreateIssue($title: String!, $description: String!, $teamId: String!, $priority: Int) {
            issueCreate(input: {
                title: $title
                description: $description
                teamId: $teamId
                priority: $priority
            }) {
                success
                issue {
                    id
                    identifier
                    url
                }
            }
        }
    """)

    result = await client.execute_async(
        mutation,
        variable_values={
            "title": title,
            "description": description,
            "teamId": TEAM_ID,
            "priority": priority
        }
    )
    return result["issueCreate"]["issue"]
```

### Pattern 4.3: Webhook Handler

```python
# PATTERN: Webhook Endpoint
# FILE: backend/app/api/v1/webhooks.py

from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import os

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").encode()

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@router.post("/linear")
async def linear_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Linear-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    action = payload.get("action")
    data = payload.get("data", {})

    if action == "update" and data.get("type") == "Issue":
        # Handle issue update
        issue_id = data.get("id")
        status = data.get("state", {}).get("name")
        # Update local database...

    return {"status": "ok"}
```

---

## 5. DEPLOYMENT PATTERNS

### Pattern 5.1: Docker Compose (Local Dev)

```yaml
# PATTERN: Local Development Environment
# FILE: docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: your_tool
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dev:devpassword@postgres/your_tool
      DEV_MODE: "true"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
```

### Pattern 5.2: Backend Dockerfile

```dockerfile
# PATTERN: Python Backend Container
# FILE: backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 5.3: Frontend Dockerfile

```dockerfile
# PATTERN: React Frontend Container
# FILE: frontend/Dockerfile

# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

### Pattern 5.4: Railway Configuration

```json
// PATTERN: Railway Deployment Config
// FILE: railway.json

{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Pattern 5.5: Environment Variables Template

```bash
# PATTERN: Environment Configuration
# FILE: .env.example

# Database
DATABASE_URL=postgresql://user:pass@host/dbname

# Authentication
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_API_AUDIENCE=https://api.your-tool.com

# Frontend (prefix with VITE_ for Vite)
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=https://api.your-tool.com
VITE_API_URL=https://your-backend-url

# Integrations (as needed)
LINEAR_API_KEY=lin_api_xxx
LINEAR_WEBHOOK_SECRET=xxx
EXTERNAL_API_KEY=xxx

# Development
DEV_MODE=false
SECRET_KEY=minimum-32-char-secret-key-here
```

---

## 6. UTILITY PATTERNS

### Pattern 6.1: ID Generator

```python
# PATTERN: Unique ID Generator
# FILE: backend/app/services/id_generator.py

from sqlalchemy.orm import Session

def generate_entity_id(db: Session, prefix: str = "ENT") -> str:
    """Generate next sequential ID like ENT-001, ENT-002, etc."""
    from app.models.your_entity import YourEntity

    last = db.query(YourEntity).order_by(YourEntity.id.desc()).first()
    next_num = 1 if not last else int(last.entity_id.split("-")[1]) + 1
    return f"{prefix}-{next_num:03d}"
```

### Pattern 6.2: Date Formatters

```typescript
// PATTERN: Date Formatting Utilities
// FILE: frontend/src/utils/formatters.ts

import { format, formatDistanceToNow, parseISO } from 'date-fns';

export const formatDate = (date: string) =>
  format(parseISO(date), 'MMM d, yyyy');

export const formatDateTime = (date: string) =>
  format(parseISO(date), 'MMM d, yyyy h:mm a');

export const formatRelative = (date: string) =>
  formatDistanceToNow(parseISO(date), { addSuffix: true });
```

### Pattern 6.3: Status Badge Component

```tsx
// PATTERN: Reusable Status Badge
// FILE: frontend/src/components/StatusBadge.tsx

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  ACTIVE: 'bg-green-100 text-green-800',
  ARCHIVED: 'bg-red-100 text-red-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  PASS: 'bg-green-100 text-green-800',
  FAIL: 'bg-red-100 text-red-800',
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100'}`}>
      {status}
    </span>
  );
}
```

---

## 7. PROJECT STRUCTURE TEMPLATE

```
your-new-tool/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── your_entities.py    # CRUD routes
│   │   ├── core/
│   │   │   ├── config.py               # Settings
│   │   │   └── security.py             # Auth
│   │   ├── db/
│   │   │   └── database.py             # DB connection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── your_entity.py          # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── your_entity.py          # Pydantic schemas
│   │   ├── services/
│   │   │   └── your_service.py         # Business logic
│   │   └── main.py                     # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/                 # Reusable UI
│   │   ├── hooks/                      # React hooks
│   │   ├── pages/                      # Page components
│   │   ├── services/
│   │   │   └── api.ts                  # API client
│   │   ├── types/
│   │   │   └── index.ts                # TypeScript types
│   │   ├── utils/                      # Helpers
│   │   ├── App.tsx                     # Router
│   │   └── main.tsx                    # Entry point
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── railway.json
└── README.md
```

---

## 8. DEPENDENCIES (requirements.txt / package.json)

### Backend (requirements.txt)
```
fastapi==0.108.0
uvicorn[standard]==0.25.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.2
python-jose[cryptography]==3.3.0
httpx==0.26.0
python-dotenv==1.0.0
alembic==1.13.1
```

### Frontend (package.json essentials)
```json
{
  "dependencies": {
    "react": "^19.1.0",
    "@tanstack/react-query": "^5.0.0",
    "react-router-dom": "^7.0.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.50.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0",
    "@auth0/auth0-react": "^2.2.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "@types/react": "^18.2.0"
  }
}
```

---

## 9. CHECKLIST: New Tool Creation

- [ ] Copy project structure template
- [ ] Update `docker-compose.yml` with tool-specific DB name
- [ ] Create SQLAlchemy models in `backend/app/models/`
- [ ] Create Pydantic schemas in `backend/app/schemas/`
- [ ] Create API routes in `backend/app/api/v1/`
- [ ] Register routes in `backend/app/main.py`
- [ ] Update TypeScript types in `frontend/src/types/`
- [ ] Create API service functions in `frontend/src/services/api.ts`
- [ ] Create React Query hooks in `frontend/src/hooks/`
- [ ] Build page components in `frontend/src/pages/`
- [ ] Configure `.env` files for both frontend and backend
- [ ] Test locally with `docker-compose up`
- [ ] Deploy to Railway
- [ ] Configure custom domain if needed

---

## 10. WHAT'S UNIQUE TO DRIP-3D (Not Reusable)

These patterns are **specific to drip-team-portal** and should be adapted, not copied directly:

1. **Value Engine** - Expression parsing with SymPy (only if you need formula evaluation)
2. **Unit System** - 170+ units with SI dimensions (only if you need unit conversion)
3. **Materials Project Integration** - Only for materials science tools
4. **Physics Validation** - DRIP-specific acoustic physics
5. **Linear.com Integration** - Only if using Linear for project management
6. **Domain-aware routing** - www vs team subdomain (only for dual-purpose sites)

---

*Document generated from drip-3d.com codebase analysis*
*Ready for 141-tool suite development*
