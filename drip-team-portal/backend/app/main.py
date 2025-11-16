from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine
from app.models import Base

# Import after models are loaded
from app.api.v1 import components, tests, auth, webhooks, reports, properties, materials, materials_project, alloy_enhancements

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

app.include_router(auth.router, tags=["auth"])
app.include_router(components.router, tags=["components"])
app.include_router(tests.router, tags=["tests"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(reports.router, tags=["reports"])
app.include_router(properties.router, tags=["properties"])
app.include_router(materials.router, tags=["materials"])
app.include_router(materials_project.router, tags=["materials-project"])
app.include_router(alloy_enhancements.router, prefix="/api/v1", tags=["alloy-enhancements"])

@app.get("/")
async def root():
    return {"message": "DRIP Team Portal API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}