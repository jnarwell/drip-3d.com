from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.rate_limit import limiter
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
from app.api.v1.linear import router as linear_router
from app.api.v1.linear_enhanced import router as linear_enhanced_router
from app.api.v1.constants import router as constants_router
from app.api.v1.units import router as units_router
from app.api.v1.values import router as values_router
from app.api.v1.search import router as search_router
from app.api.v1.user_preferences import router as user_preferences_router
from app.api.v1.engineering_properties import router as eng_properties_router
from app.api.v1.physics_models import router as physics_models_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.time import router as time_router
from app.api.v1.time_import import router as time_import_router
from app.api.v1.resources import router as resources_router
from app.api.v1.collections import router as collections_router
from app.api.v1.users import router as users_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.drive import router as drive_router
from app.api.v1.google_oauth import router as google_oauth_router
from app.api.v1.test_protocols import router as test_protocols_router
from app.api.v1.feedback import router as feedback_router

app = FastAPI(
    title="DRIP Team Portal API",
    description="Internal validation tracking portal for DRIP project",
    version="1.0.0",
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler to ensure CORS headers are added to error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper CORS headers."""
    origin = request.headers.get("origin", "")

    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

    # Add CORS headers for known origins
    if origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with proper CORS headers."""
    origin = request.headers.get("origin", "")
    logging.error(f"Unexpected error: {exc}", exc_info=True)

    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

    # Add CORS headers for known origins
    if origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        # Run Alembic migrations on startup
        import subprocess
        import os
        logging.info("=== Running Alembic migrations ===")
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(__file__)),  # backend directory
            capture_output=True,
            text=True
        )
        logging.info(f"Migration stdout: {migration_result.stdout}")
        if migration_result.stderr:
            logging.warning(f"Migration stderr: {migration_result.stderr}")
        if migration_result.returncode != 0:
            logging.error(f"Migration failed with code {migration_result.returncode}")
        else:
            logging.info("=== Migrations complete ===")
        
        if settings.DATABASE_URL:
            from sqlalchemy import text

            # Import all models to register them with Base
            from app.models.audit import AuditLog
            from app.models.component import Component
            from app.models.material import Material, MaterialProperty, MaterialPropertyTemplate
            from app.models.resources import SystemConstant, Resource
            from app.models.time_entry import TimeEntry
            from app.models.time_break import TimeBreak
            from app.models.user import User
            from app.models.test import Test, TestResult
            from app.models.property import PropertyDefinition, ComponentProperty, UnitSystem
            from app.models.units import Unit, UnitConversion, UnitAlias
            from app.models.values import ValueNode, ValueDependency, PropertyValueLink
            from app.models.user_preferences import UserUnitPreference
            from app.models.physics_model import PhysicsModel, PhysicsModelVersion, ModelInstance, ModelInput
            from app.models.contact import Contact
            from app.models.google_token import GoogleToken
            from app.models.test_protocol import TestProtocol, TestRun, TestMeasurement, TestValidation
            from app.models.feedback import FeedbackSubmission

            # Create all tables (safe - won't modify existing tables)
            logging.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logging.info("Database tables created successfully!")

            # Migrate existing tables: add new columns that create_all() won't add
            logging.info("Running schema migrations...")
            with engine.connect() as conn:
                # Add owner_id to components table if it doesn't exist
                try:
                    conn.execute(text("ALTER TABLE components ADD COLUMN IF NOT EXISTS owner_id VARCHAR"))
                    conn.commit()
                    logging.info("Migration: components.owner_id column ensured")
                except Exception as e:
                    logging.debug(f"Migration skipped (may already exist): {e}")

                # Add edit_history to time_entries table if it doesn't exist
                try:
                    conn.execute(text("ALTER TABLE time_entries ADD COLUMN IF NOT EXISTS edit_history JSON"))
                    conn.commit()
                    logging.info("Migration: time_entries.edit_history column ensured")
                except Exception as e:
                    logging.debug(f"Migration skipped (may already exist): {e}")

                # Add setup_checklist to test_protocols table if it doesn't exist
                try:
                    conn.execute(text("ALTER TABLE test_protocols ADD COLUMN IF NOT EXISTS setup_checklist JSON"))
                    conn.commit()
                    logging.info("Migration: test_protocols.setup_checklist column ensured")
                except Exception as e:
                    logging.debug(f"Migration skipped (may already exist): {e}")

                # Data wipe removed - was causing entries to be deleted on every restart

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
app.include_router(constants_router, tags=["constants"])
app.include_router(linear_router, tags=["linear"])
app.include_router(linear_enhanced_router, tags=["linear-enhanced"])
app.include_router(units_router, tags=["units"])
app.include_router(values_router, tags=["values"])
app.include_router(search_router, tags=["search"])
app.include_router(user_preferences_router, tags=["user-preferences"])
app.include_router(eng_properties_router, tags=["engineering-properties"])
app.include_router(physics_models_router, tags=["physics-models"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(time_router, tags=["time"])
app.include_router(time_import_router, tags=["time-import"])
app.include_router(resources_router, tags=["resources"])
app.include_router(collections_router, tags=["collections"])
app.include_router(users_router, tags=["users"])
app.include_router(contacts_router, tags=["contacts"])
app.include_router(drive_router, tags=["drive"])
app.include_router(google_oauth_router, tags=["google-oauth"])
app.include_router(test_protocols_router, tags=["test-protocols"])
app.include_router(feedback_router, tags=["feedback"])

@app.get("/")
async def root():
    return {"message": "DRIP Team Portal API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0-units-system", "updated": "2025-12-15"}

# Redirect company site routes to the frontend if they hit the backend
@app.get("/team")
async def redirect_team():
    return RedirectResponse(url="https://www.drip-3d.com/team", status_code=302)

@app.get("/progress")
async def redirect_progress():
    return RedirectResponse(url="https://www.drip-3d.com/progress", status_code=302)
