# Environment Variables

Required and optional environment variables for the DRIP Team Portal.

## Backend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **Yes** | - | PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/dbname`) |
| `SECRET_KEY` | **Yes** (prod) | - | Secret key for JWT encoding |
| `LINEAR_API_KEY` | No | - | Linear API key for issue integration. If missing, issue dropdown shows empty list gracefully. |
| `AUTH0_DOMAIN` | **Yes** (prod) | - | Auth0 tenant domain (e.g., `your-tenant.auth0.com`) |
| `AUTH0_CLIENT_ID` | **Yes** (prod) | - | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | **Yes** (prod) | - | Auth0 application client secret |
| `AUTH0_API_AUDIENCE` | **Yes** (prod) | - | Auth0 API audience identifier |
| `ALLOWED_EMAIL_DOMAIN` | No | `drip-3d.com` | Email domain restriction for users |
| `DEV_MODE` | No | `false` | Set to `"true"` to bypass auth (local development only) |
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins (comma-separated for multiple) |

## Frontend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | **Yes** | - | Backend API URL (e.g., `http://localhost:8000` or Railway URL) |
| `VITE_AUTH0_DOMAIN` | **Yes** (prod) | - | Auth0 tenant domain |
| `VITE_AUTH0_CLIENT_ID` | **Yes** (prod) | - | Auth0 SPA client ID |
| `VITE_AUTH0_AUDIENCE` | **Yes** (prod) | - | Auth0 API audience |

## Local Development

Create a `.env` file in `backend/` based on `.env.example`:

```bash
# Required
DATABASE_URL=postgresql://postgres:password@localhost:5432/drip_portal

# Development mode - bypasses Auth0
DEV_MODE=true

# Optional - for Linear integration
LINEAR_API_KEY=lin_api_xxxxx
```

## Railway Deployment

Set these in Railway dashboard under Variables:

1. `DATABASE_URL` - Auto-provisioned by Railway PostgreSQL plugin
2. `LINEAR_API_KEY` - From Linear Settings > API > Personal API Keys
3. `SECRET_KEY` - Generate with `openssl rand -hex 32`
4. Auth0 variables - From Auth0 dashboard

## Feature Degradation

The app handles missing optional variables gracefully:

| Missing Variable | Behavior |
|-----------------|----------|
| `LINEAR_API_KEY` | Issue dropdown shows "No issues found", no errors |
| `DEV_MODE=true` | Auth bypassed, test user `test@drip-3d.com` used |
| `ALLOWED_ORIGINS` | CORS allows all origins (fine for dev) |
