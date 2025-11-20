from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine
from app.models import Base
import logging

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
from app.api.v1.templates import router as templates_router
from app.api.v1.property_tables import router as property_tables_router
from app.api.v1.property_table_templates import router as property_table_templates_router
from app.api.v1.property_tables_enhanced import router as property_tables_enhanced_router
from app.api.v1.linear import router as linear_router
from app.api.v1.constants import router as constants_router
# from app.api.v1.formulas import router as formulas_router

app = FastAPI(
    title="DRIP Team Portal API",
    description="Internal validation tracking portal for DRIP project",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        if settings.DATABASE_URL:
            # Import all models to register them with Base
            from app.models.audit import AuditLog
            from app.models.component import Component
            from app.models.material import Material, MaterialProperty, MaterialPropertyTemplate
            from app.models.resources import PropertyTableTemplate, PropertyTable, SystemConstant, CalculationTemplate
            from app.models.user import User
            from app.models.test import Test, TestResult
            from app.models.property import PropertyDefinition, ComponentProperty, UnitSystem
            from app.models.formula_isolated import PropertyFormula, PropertyReference, FormulaValidationRule, CalculationHistory, FormulaTemplate
            
            # Create all tables
            logging.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logging.info("Database tables created successfully!")
        else:
            logging.warning("DATABASE_URL not set - skipping table creation")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        # Don't crash the app, just log the error
        pass

# Custom middleware to handle Railway's HTTP->HTTPS forwarding  
@app.middleware("http")
async def handle_railway_forwarding(request: Request, call_next):
    """
    Railway terminates HTTPS at the edge and forwards HTTP to containers.
    This middleware fixes FastAPI trailing slash redirects that lose HTTPS.
    """
    # Log the request for debugging
    logging.info(f"🌐 Request: {request.method} {request.url.scheme}://{request.url.netloc}{request.url.path}")
    
    response = await call_next(request)
    
    # Fix FastAPI 307 redirects that lose HTTPS scheme
    if response.status_code == 307 and "location" in response.headers:
        location = response.headers["location"]
        if location.startswith("http://") and "railway.app" in location:
            # Fix the redirect to use HTTPS
            https_location = location.replace("http://", "https://")
            response.headers["location"] = https_location
            logging.info(f"🔧 Fixed 307 redirect: {location} -> {https_location}")
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

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
app.include_router(templates_router, tags=["templates"])
app.include_router(property_tables_router, tags=["property-tables"])
app.include_router(property_table_templates_router, prefix="/api/v1/property-table-templates", tags=["property-table-templates"])
app.include_router(property_tables_enhanced_router, prefix="/api/v1/enhanced/property-tables", tags=["property-tables-enhanced"])
app.include_router(linear_router, tags=["linear"])
# app.include_router(formulas_router, tags=["formulas"])

@app.get("/")
async def root():
    return {"message": "DRIP Team Portal API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3A-formula-fields", "updated": "2025-11-20"}