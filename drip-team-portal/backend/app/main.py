from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine
from app.models import Base

# Import routers directly from modules
from app.api.v1.components import router as components_router
from app.api.v1.tests import router as tests_router
from app.api.v1.auth import router as auth_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.reports import router as reports_router
from app.api.v1.properties import router as properties_router
from app.api.v1.materials import router as materials_router
from app.api.v1.materials_project import router as materials_project_router
from app.api.v1.alloy_enhancements import router as alloy_enhancements_router
# from app.api.v1.templates import router as templates_router  # Temporarily disabled
from app.api.v1.property_tables import router as property_tables_router
from app.api.v1.property_table_templates import router as property_table_templates_router
from app.api.v1.property_tables_enhanced import router as property_tables_enhanced_router
from app.api.v1.linear import router as linear_router
from app.api.v1.constants import router as constants_router

app = FastAPI(
    title="DRIP Team Portal API",
    description="Internal validation tracking portal for DRIP project",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["auth"])
app.include_router(components_router, tags=["components"])
app.include_router(tests_router, tags=["tests"])
app.include_router(webhooks_router, tags=["webhooks"])
app.include_router(reports_router, tags=["reports"])
app.include_router(properties_router, tags=["properties"])
app.include_router(materials_router, tags=["materials"])
app.include_router(materials_project_router, tags=["materials-project"])
app.include_router(alloy_enhancements_router, prefix="/api/v1", tags=["alloy-enhancements"])
app.include_router(constants_router, tags=["constants"])
# app.include_router(templates_router, tags=["templates"])  # Temporarily disabled
app.include_router(property_tables_router, tags=["property-tables"])
app.include_router(property_table_templates_router, prefix="/api/v1/property-table-templates", tags=["property-table-templates"])
app.include_router(property_tables_enhanced_router, prefix="/api/v1/enhanced/property-tables", tags=["property-tables-enhanced"])
app.include_router(linear_router, tags=["linear"])

@app.get("/")
async def root():
    return {"message": "DRIP Team Portal API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}