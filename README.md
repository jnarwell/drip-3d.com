# DRIP-3D.com

Unified web platform for DRIP (Drop Resonance Induction Printing) acoustic manufacturing system at Stanford University.

## Overview

This repository contains a unified React application that serves both:
- **Public website** (www.drip-3d.com) - Marketing and information site
- **Team portal** (team.drip-3d.com) - Internal validation tracking system

Both sites are served from a single Railway deployment with domain-based routing.

## Architecture

### Frontend (React + TypeScript)
- Single React application with domain-aware routing
- Vite build system with TypeScript
- TailwindCSS for styling
- Deployed on Railway with custom domains

### Backend (FastAPI + Python)
- RESTful API for team portal functionality
- PostgreSQL database
- Authentication via Auth0 (dev mode available)
- Deployed on Railway

### Infrastructure
- **Railway**: 3 services (Frontend, Backend, PostgreSQL)
- **Custom domains**: 
  - www.drip-3d.com → Company site
  - team.drip-3d.com → Team portal
- **CORS**: Configured for cross-origin requests

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (optional)

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jnarwell/drip-3d.com.git
cd drip-3d.com
```

2. Frontend setup:
```bash
cd drip-team-portal/frontend
npm install
npm run dev
```

3. Backend setup:
```bash
cd drip-team-portal/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Access locally:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

## Deployment

Deployment is automated via Railway with GitHub integration. Pushing to the `main` branch triggers automatic deployment of all services.

### Environment Variables

See `drip-team-portal/.env.example` for required environment variables.

Key variables:
- `VITE_API_URL`: Backend API URL
- `DATABASE_URL`: PostgreSQL connection (auto-provided by Railway)
- `DEV_MODE`: Set to `false` for production

## Project Structure

```
drip-3d.com/
├── drip-team-portal/          # Main application
│   ├── frontend/              # React frontend
│   │   ├── src/
│   │   │   ├── pages/        # Page components
│   │   │   │   └── company/  # Public site pages
│   │   │   ├── components/   # Shared components
│   │   │   ├── services/     # API services
│   │   │   └── hooks/        # Custom React hooks
│   │   └── public/           # Static assets
│   ├── backend/              # FastAPI backend
│   │   └── app/
│   │       ├── api/          # API endpoints
│   │       ├── models/       # Database models
│   │       └── services/     # Business logic
│   └── railway.json          # Railway configuration
├── legacy/                   # Archived static site files
└── README.md                # This file
```

## Features

### Public Website (www.drip-3d.com)
- Project overview and specifications
- Team information and recruitment
- Progress tracking and milestones
- Interactive animations and responsive design

### Team Portal (team.drip-3d.com)
- Component registry with material selection
- Test campaign management
- Property calculations with formulas
- Reports and data export
- Linear integration for project management

## Contributing

1. Create a feature branch
2. Make your changes
3. Test locally
4. Submit a pull request

## License

© 2025 DRIP Acoustic Manufacturing. All rights reserved.

## Contact

- Project Lead: Jamie Marwell (jamie@drip-3d.com)
- GitHub: https://github.com/jnarwell/drip-3d.com
- Documentation: See `/drip-team-portal/README.md` for detailed portal documentation