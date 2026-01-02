# Resources Page Upgrade

## 1. GOAL

### What We're Building
Expand the existing Resources page with two new sections:

**Current Sections:**
- Lookup Tables
- Constants

**New Sections:**
- **Documents** - Google Drive integration with tagged, searchable documents linked to components and Linear issues
- **Contacts** - Internal team and external contacts (researchers, suppliers) with structured metadata

### Why
- **Quick knowledge transfer** - New team members can find relevant docs and experts fast
- **Team extension** - External contacts (researchers, suppliers) are discoverable with context
- **Elite onboarding** - Reduces ramp-up time by centralizing tribal knowledge

### Document Features
- Google Drive integration
- Tagging system
- Full-text search
- Linked to components/assemblies
- Linked to Linear issues

### Contact Features
- Internal team directory
- External contacts (researchers, suppliers, consultants)
- Fields: Name, Organization, Expertise/Role, Contact Info, Notes
- Searchable by expertise/domain

---

## 2. DISCOVERY LOG

### Backend Findings
- **Resource model exists** - can extend for Documents
- **Contact model missing** - needs new table
- Existing patterns: CRUD routes, SQLAlchemy models, Pydantic schemas

### Frontend Findings
- **Tab pattern ready** - Resources page uses tab navigation
- **Custom table components** - reusable for new sections
- Existing patterns match proposed UI structure

### Auth Findings
- **Auth0 configured** with Google OAuth connection
- **Google OAuth Client ID** already set up in Auth0
- **All Drive scopes enabled** on the connection
- **Post Login Action deployed**: "Inject Google Token"

---

## 3. ARCHITECTURE DECISIONS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Google Auth | Auth0 Token Vault + Post Login Action | Leverages existing Auth0 setup, tokens flow through JWT |
| Token Storage | JWT claims (`https://drip-3d.com/google_access_token`) | No additional DB storage needed, tokens refresh with login |
| Drive API Calls | Backend (not frontend) | Security - tokens stay server-side, CORS avoided |
| Contact Storage | New `contacts` table | Clean separation, purpose-built schema |
| Document Storage | Extend Resource model with `google_drive_file_id` | Reuse existing tagging/linking infrastructure |

### Endpoint Architecture

```
/api/v1/drive/files   → Browse Google Drive (read-only, live from Drive)
/api/v1/resources     → Store/retrieve saved documents (DB records)
```

- **Documents are Resource model entries** - not a separate table
- `google_drive_file_id` field links Resource record to actual Drive file
- `/drive/files` = browsing Drive, `/resources` = persistence layer

---

## 4. IMPLEMENTATION PLAN

### Instance A: Backend
- [ ] Create Contact model + migration
- [ ] Contact CRUD routes (`/api/v1/contacts`)
- [ ] Extract Google token from JWT claims
- [ ] Document routes with Drive file metadata

### Instance B: Frontend
- [ ] `Documents.tsx` tab component
- [ ] `Contacts.tsx` tab component
- [ ] Drive file picker/browser UI
- [ ] Contact search/filter UI

### Instance C: Drive Integration
- [ ] Google Drive service (`drive_service.py`)
- [ ] List files, get metadata, search
- [ ] File preview/download URLs
- [ ] Folder navigation

---

## 5. OPEN QUESTIONS

- [x] ~~Google Drive auth approach~~ → Auth0 Token Vault
- [x] ~~Contact data storage~~ → New table in same DB
- [ ] Tag taxonomy - freeform or predefined categories?
- [ ] Search implementation - in-app or leverage external service?
- [ ] Linear integration - one-way link or bidirectional sync?
