# Railway Integration Documentation for DRIP Team Portal

## 🚀 **Overview**

The DRIP Team Portal is deployed on Railway using a 3-service architecture: Frontend (React), Backend (FastAPI), and PostgreSQL database. This document captures our integration experience, challenges, solutions, and current state.

## 🏗️ **Architecture**

### **Service Structure**
```
Railway Project: drip-3d.com
├── 📱 Frontend (React + TypeScript)
│   ├── Service: frontend-production-31b1.up.railway.app
│   ├── Build: Vite production build
│   └── Static hosting with SPA routing
├── 🔧 Backend (FastAPI + Python)
│   ├── Service: backend-production-aa29.up.railway.app
│   ├── SQLAlchemy ORM + Pydantic schemas
│   └── Auto-deployment from main branch
└── 🗄️ PostgreSQL Database
    ├── Railway managed PostgreSQL service
    ├── Auto-connection via DATABASE_URL
    └── Schema auto-creation via SQLAlchemy
```

### **Environment Variables**
```bash
# Backend
DATABASE_URL=postgresql://... (auto-provided by Railway)
DEV_MODE=false (for production auth)
ALLOWED_ORIGINS=["https://frontend-production-31b1.up.railway.app"]

# Frontend  
VITE_API_URL=https://backend-production-aa29.up.railway.app
```

## 🛠️ **Development Workflow**

### **Deployment Process**
1. **Code changes** pushed to `main` branch on GitHub
2. **Railway auto-detects** changes via GitHub integration
3. **Build process** runs automatically (separate for frontend/backend)
4. **Health checks** verify deployment success
5. **Live services** updated with zero-downtime

### **Database Management**
- **Schema creation**: Automatic via SQLAlchemy `Base.metadata.create_all()`
- **Migrations**: Currently handled by dropping/recreating database (test data only)
- **Connection**: Auto-managed through Railway's DATABASE_URL

## 🚨 **Critical Issues Encountered & Solutions**

### **1. CORS and HTTPS Mixed Content Issues**

**Problem**: 
- Railway terminates HTTPS at edge, forwards HTTP to containers
- FastAPI redirects (307) lose HTTPS scheme → Mixed Content errors
- CORS headers missing during errors

**Solution**: Custom middleware in `backend/app/main.py`
```python
@app.middleware("http")
async def handle_railway_forwarding(request: Request, call_next):
    """Railway HTTPS termination fix"""
    response = await call_next(request)
    
    # Fix FastAPI 307 redirects that lose HTTPS scheme
    if response.status_code == 307 and "location" in response.headers:
        location = response.headers["location"]
        if location.startswith("http://") and "railway.app" in location:
            https_location = location.replace("http://", "https://")
            response.headers["location"] = https_location
    
    return response
```

### **2. Pydantic Schema Field Conflicts**

**Problem**: POST endpoints returning 500 errors due to field conflicts
```python
# ❌ BROKEN: Schema with default that conflicts with API logic
class SystemConstantCreate(SystemConstantBase):  
    pass  # Inherits is_editable: bool = False

# API tries to override
constant = SystemConstant(**data.dict(), is_editable=True)  # Conflict!
```

**Solution**: Remove conflicting fields from Create schemas
```python
# ✅ FIXED: Exclude conflicting fields
class SystemConstantCreate(BaseModel):
    symbol: str
    name: str
    # ... other fields
    # DON'T include is_editable - API sets it
```

**Pattern**: When POST endpoints fail with 500 errors, check for schema field conflicts where Create schemas inherit defaults that conflict with API business logic.

### **3. Database Schema Migration Issues**

**Problem**: Adding new columns to existing tables
- SQLAlchemy `create_all()` only creates missing **tables**, not missing **columns**
- New fields (e.g., formula fields) don't appear in existing records
- Production database retains old schema

**Solutions**:
- **For test data**: Wipe database via Railway UI, redeploy to recreate schema
- **For production**: Use Alembic migrations or manual ALTER TABLE statements

### **4. Import/Dependency Circular Issues**

**Problem**: Circular imports between formula models
```python
# ❌ models/__init__.py importing formula.py with FK constraints
# ❌ main.py importing formula_isolated.py  
# Result: Startup failures, import conflicts
```

**Solution**: 
- Comment out problematic imports in `models/__init__.py`
- Use isolated models without FK constraints temporarily
- Import directly in `main.py` for table creation

### **5. Railway Deployment Lag**

**Problem**: Changes pushed to GitHub not reflected in Railway deployment
- Railway sometimes doesn't trigger auto-deployment
- Old builds cached or stuck in queue
- Free tier rate limiting during high traffic

**Solutions**:
- **Force deployment**: Make small change (like updating health endpoint) and push
- **Manual trigger**: Use Railway dashboard to manually redeploy
- **Verify deployment**: Check health endpoint for version/timestamp changes

## 📊 **Current State (November 2025)**

### **✅ Working Systems**
- **Authentication**: Dev mode bypass + JWT ready
- **CORS**: Full cross-origin support with HTTPS fixes
- **API Endpoints**: All CRUD operations for components, properties, materials, constants
- **Database**: PostgreSQL with auto-schema creation
- **File Structure**: Modular FastAPI with proper separation of concerns

### **🔧 In Progress**
- **Formula System**: Database models created, API integration pending
- **Variable Reference System**: `#prefix` UI pattern for formula variables
- **Property Calculations**: Formula-based property value calculation

### **🗂️ Database Schema Status**
```sql
-- Core tables (✅ Working)
components, materials, properties, property_definitions, 
system_constants, property_tables, users, tests

-- Formula tables (✅ Created, 🔧 Integration pending)  
property_formulas, property_references, formula_validation_rules,
calculation_history, formula_templates
```

## 🔄 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Test locally with development database
- [ ] Check for schema conflicts (Create vs Base schemas)
- [ ] Verify no circular imports
- [ ] Test CORS with frontend integration

### **Post-Deployment** 
- [ ] Health endpoint returns expected response
- [ ] Database schema created correctly (new tables/columns)
- [ ] API endpoints respond with proper CORS headers
- [ ] Frontend can communicate with backend
- [ ] Authentication working (dev mode or JWT)

## 🚫 **Common Pitfalls**

1. **Schema Conflicts**: Always check Create schemas don't conflict with API business logic
2. **HTTPS Redirects**: Railway's HTTPS termination requires custom middleware
3. **Database Wipes**: Only safe with test data - production needs proper migrations  
4. **Import Cycles**: Keep formula models isolated to avoid circular dependencies
5. **Deployment Lag**: Railway may not auto-deploy; force with small changes if needed

## 🛡️ **Security Considerations**

- **HTTPS**: Enforced at Railway edge with proper redirect handling
- **CORS**: Restricted to specific frontend origin
- **Auth**: JWT-ready, currently using dev bypass for testing
- **Environment Variables**: Sensitive data managed through Railway dashboard
- **Database**: Managed by Railway with automatic backups

## 📈 **Performance & Monitoring**

- **Health Checks**: `/health` endpoint for service monitoring
- **Logging**: Structured logging with request/response tracking  
- **Error Handling**: Proper HTTP status codes and error messages
- **Rate Limiting**: Railway free tier limits apply during high traffic

## 🔗 **Key Files for Railway Integration**

### **Backend Configuration**
- `backend/app/main.py` - FastAPI app setup, CORS middleware, Railway HTTPS fixes
- `backend/app/core/config.py` - Environment variable management
- `backend/app/db/database.py` - PostgreSQL connection via DATABASE_URL

### **Frontend Configuration**  
- `frontend/vite.config.ts` - Build configuration for Railway static hosting
- `frontend/.env.production` - Production API URL configuration

### **Database Models**
- `backend/app/models/` - SQLAlchemy models for auto-schema creation
- `backend/app/models/formula_isolated.py` - Formula system tables (isolated)

## 🚀 **Quick Commands for Railway Management**

### **Force Deployment**
```bash
# Make a small change to trigger deployment
git commit -am "Force Railway deployment"
git push origin main

# Check deployment status  
curl https://backend-production-aa29.up.railway.app/health
```

### **Database Reset (Test Data Only)**
1. Delete PostgreSQL service in Railway dashboard
2. Create new PostgreSQL service
3. Update DATABASE_URL environment variable
4. Redeploy backend service

### **Debug Deployment Issues**
```bash
# Check service health
curl https://backend-production-aa29.up.railway.app/health

# Test CORS
curl -H "Origin: https://frontend-production-31b1.up.railway.app" \
     https://backend-production-aa29.up.railway.app/api/v1/components/

# Verify database connection
curl https://backend-production-aa29.up.railway.app/api/v1/components/
```

---

**Last Updated**: November 20, 2025  
**Railway Services**: 3 (Frontend + Backend + PostgreSQL)  
**Deployment Status**: Active with formula system integration in progress  
**Next Priority**: Complete variable reference backbone system with `#prefix` UI pattern

**For Future Claude Instances**: This document should be consulted before making any Railway deployment changes. Pay special attention to the Common Pitfalls section and always test schema changes with a database wipe in the test environment first.