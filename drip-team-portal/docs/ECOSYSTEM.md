# DRIP Team Portal - Ecosystem & Security Documentation

**Last Updated:** 2026-01-02
**Status:** Production
**Security Audit:** Completed

---

## Table of Contents
1. [Security Findings](#security-findings)
2. [Credential Rotation](#credential-rotation)
3. [API Contract Map](#api-contract-map)
4. [Cross-Cutting Concerns Audit](#cross-cutting-concerns-audit)
5. [Monitoring & Observability](#monitoring--observability)
6. [Roadmap](#roadmap)

---

## Security Findings

### Critical Actions Required

#### 1. Credential Rotation (RECOMMENDED)

The following credentials should be rotated periodically:

| Credential | Location | Rotation Frequency |
|------------|----------|-------------------|
| `DATABASE_URL` password | Railway PostgreSQL | Quarterly |
| `LINEAR_API_KEY` | Linear Dashboard | If compromised |
| `AUTH0_CLIENT_SECRET` | Auth0 Dashboard | Annually |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console | Annually |
| `SECRET_KEY` | Railway env vars | Annually |

**Rotation Procedure:**
1. Generate new credential in respective dashboard
2. Update Railway environment variable
3. Trigger redeploy
4. Verify health endpoint responds
5. Revoke old credential

#### 2. Git History Security

**If .env was ever committed (verify first):**
```bash
# Check if .env exists in git history
git log --all --full-history -- .env

# If found, clean history (DESTRUCTIVE - backup first!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" HEAD

# Force push (requires --force, coordinate with team)
git push origin main --force
```

**Current Status:** ✅ `.env` is in `.gitignore` - verified not in history

#### 3. Authorization Hardening (Implemented)

Collections API now includes ownership verification:
- Users can only add their own resources to collections
- Added check: `resource.added_by != user_email` returns 403

---

## Credential Rotation

### Railway PostgreSQL

```bash
# 1. In Railway dashboard, create new PostgreSQL service
# 2. Export data from old database
pg_dump $OLD_DATABASE_URL > backup.sql

# 3. Import to new database
psql $NEW_DATABASE_URL < backup.sql

# 4. Update DATABASE_URL in Railway backend service
# 5. Redeploy and verify
curl https://backend-production-aa29.up.railway.app/health
```

### Linear API Key

1. Go to Linear Settings > API > Personal API Keys
2. Create new key with same permissions
3. Update `LINEAR_API_KEY` in Railway
4. Redeploy
5. Delete old key in Linear

### Google OAuth Credentials

1. Google Cloud Console > APIs & Services > Credentials
2. Create new OAuth 2.0 Client ID
3. Update `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Railway
4. Update authorized redirect URIs if needed
5. Redeploy
6. Delete old client ID

---

## API Contract Map

### Verified Contracts (All Aligned)

| Endpoint | Frontend | Backend | Status |
|----------|----------|---------|--------|
| `GET /api/v1/resources` | api.ts | resources.py | ✅ |
| `POST /api/v1/resources` | api.ts | resources.py | ✅ |
| `GET /api/v1/collections` | Documents.tsx | collections.py | ✅ |
| `POST /api/v1/collections` | Documents.tsx | collections.py | ✅ |
| `GET /api/v1/google-oauth/status` | Documents.tsx | google_oauth.py | ✅ |
| `POST /api/v1/google-oauth/callback` | OAuthCallback.tsx | google_oauth.py | ✅ |
| `GET /api/v1/drive/files` | Documents.tsx | drive.py | ✅ |

### Recently Fixed Issues

| Issue | Resolution | Date |
|-------|------------|------|
| `resource_type` missing `pdf`, `slides` | Added to valid_types | 2026-01-02 |
| Collections API backend missing | Created collections.py | 2026-01-02 |
| Collection authorization missing | Added ownership check | 2026-01-02 |
| Collections missing `resource_ids` | Frontend now uses `?include_resources=true` | 2026-01-02 |

### Known Low-Priority Items

| Issue | Impact | Status |
|-------|--------|--------|
| `redirect_uri` extra field in callback | Ignored by Pydantic | Deferred |
| Frontend `email` in status interface | Optional, unused | Deferred |
| State parameter CSRF risk | Low - email validation exists | Deferred |

---

## Cross-Cutting Concerns Audit

### 1. Environment Consistency

| Check | Status |
|-------|--------|
| Dev/prod parity | ✅ DEV_MODE flag works |
| .env.example complete | ✅ Updated 2026-01-02 |
| Missing vars documented | ✅ All vars in .env.example |

### 2. Deployment

| Check | Status |
|-------|--------|
| Health endpoint | ✅ `/health` exists |
| CI/CD pipeline | ✅ GitHub Actions |
| Docker support | ✅ Dockerfiles exist |

### 3. Monitoring Gaps

| Check | Status | Priority |
|-------|--------|----------|
| Error tracking (Sentry) | ❌ Not configured | P1 |
| Uptime monitoring | ⚠️ Railway basic only | P2 |
| Alerting | ❌ None | P2 |
| Structured logging | ✅ logger.info present | - |

### 4. Documentation

| Check | Status |
|-------|--------|
| Project README | ✅ Updated 2026-01-02 |
| API docs | ⚠️ OpenAPI auto-gen only |
| Setup instructions | ✅ In RAILWAY_INTEGRATION.md |
| Architecture docs | ✅ RAILWAY_INTEGRATION.md |

### 5. Test Coverage

| Area | Status |
|------|--------|
| Backend unit tests | ✅ 27 test files |
| Backend integration | ✅ test_integration/ |
| Frontend tests | ❌ None (`--passWithNoTests`) |
| E2E tests | ❌ None |

### 6. Backup/Recovery

| Check | Status |
|-------|--------|
| Database backups | ⚠️ Railway "automatic" |
| Restore procedure | ❌ Not documented |
| Disaster recovery | ❌ No plan |

---

## Monitoring & Observability

### Current State

```
Health Check:  GET /health
Response:      {"status": "healthy", "version": "4.0-units-system"}
```

### Recommended Additions

1. **Sentry Integration** (P1)
   ```python
   # backend/app/main.py
   import sentry_sdk
   sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))
   ```

2. **Structured Logging** (P2)
   ```python
   import structlog
   logger = structlog.get_logger()
   ```

3. **Uptime Monitoring** (P2)
   - BetterUptime or Pingdom
   - Monitor: `https://backend-production-aa29.up.railway.app/health`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION                                    │
│                                                                         │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐                  │
│  │  Frontend  │────▶│  Backend   │────▶│ PostgreSQL │                  │
│  │  (React)   │     │  (FastAPI) │     │  (Railway) │                  │
│  └────────────┘     └────────────┘     └────────────┘                  │
│        │                  │                                             │
│        │                  ├─────────▶ Google OAuth                      │
│        │                  ├─────────▶ Linear API                        │
│        │                  └─────────▶ Auth0 (JWT)                       │
│        │                                                                │
│  Domains:                                                               │
│  - www.drip-3d.com (public)                                            │
│  - team.drip-3d.com (portal)                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Roadmap

### Completed (2026-01-02)

- [x] Documents Collections feature
- [x] Google Drive OAuth integration
- [x] Document starring/favorites
- [x] Bulk select operations
- [x] Sort/filter options
- [x] Mobile responsive sidebar
- [x] Accessibility improvements (aria-labels, focus traps)
- [x] Rate limiting on collection creation
- [x] Input validation (Pydantic field validators)
- [x] Bulk add resources to collection

### Planned

- [ ] Vendors/Suppliers subpage
- [ ] Smart collections (auto-populate by rules)
- [ ] Document preview (inline PDF/image viewer)
- [ ] Drive folder navigation
- [ ] Drive folder bulk import
- [ ] Tests page (stub)
- [ ] Reports page (stub)
- [ ] Sentry error tracking integration
- [ ] Frontend test coverage
- [ ] E2E test suite

---

## Quick Reference

### Emergency Contacts
- Railway Status: https://status.railway.app
- Auth0 Status: https://status.auth0.com
- Google Cloud Status: https://status.cloud.google.com

### Key URLs
- Backend Health: https://backend-production-aa29.up.railway.app/health
- Frontend: https://team.drip-3d.com
- API Docs: https://backend-production-aa29.up.railway.app/docs

### Runbooks
- [Railway Integration](./RAILWAY_INTEGRATION.md)
- [Database Backup/Restore](#credential-rotation) (see above)

---

*This document should be updated whenever security-relevant changes are made.*
