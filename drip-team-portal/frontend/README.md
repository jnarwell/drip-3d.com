# DRIP Team Portal Frontend

React + TypeScript + Vite frontend for the DRIP engineering platform.

## Project Structure

```
frontend/src/
├── pages/
│   ├── company/                # Public site (www.drip-3d.com)
│   │   ├── HomePage.tsx
│   │   ├── ProgressPage.tsx
│   │   └── TeamPage.tsx
│   ├── resources/              # Engineering resources
│   │   ├── Constants.tsx       # System constants browser
│   │   └── PropertyTables.tsx  # Engineering tables viewer
│   ├── ModelBuilder/           # Physics model creation wizard
│   │   ├── index.tsx           # 4-step wizard container
│   │   ├── StepDefineModel.tsx
│   │   ├── StepInputsOutputs.tsx
│   │   ├── StepEquations.tsx
│   │   ├── StepValidate.tsx
│   │   └── types.ts
│   ├── InstanceCreator/        # Model instantiation wizard
│   │   ├── index.tsx
│   │   ├── StepSelectModel.tsx
│   │   ├── StepBindInputs.tsx
│   │   ├── StepAttachComponent.tsx
│   │   └── StepReview.tsx
│   ├── analysis/               # Analysis dashboard (named instances)
│   │   ├── Analysis.tsx        # Dashboard with WebSocket updates
│   │   └── AnalysisCreator.tsx # 3-step wizard for new analyses
│   ├── ModelsList.tsx          # Physics models list
│   ├── Dashboard.tsx           # Team portal home
│   ├── ComponentRegistry.tsx   # Component list
│   ├── ComponentDetailPage.tsx # Component editor
│   ├── TestCampaign.tsx        # Test management
│   ├── Resources.tsx           # Resources hub
│   ├── Reports.tsx             # Report generation
│   ├── Settings.tsx            # User preferences
│   └── Login.tsx               # Auth0 login
├── components/                 # Shared components
│   ├── ComponentDetailModal.tsx
│   ├── PropertyValue.tsx       # Expression input
│   ├── Layout.tsx              # App layout wrapper
│   └── ...
├── hooks/                      # Custom hooks
│   ├── useDomain.ts            # Domain detection (www vs team)
│   ├── useUnitPreferences.ts   # User unit preferences
│   ├── useLinearData.tsx       # Linear API hooks
│   └── useAnalysisWebSocket.ts # Real-time analysis updates
├── contexts/
│   └── UnitContext.tsx         # Unit system context
├── utils/
│   └── unitConversion.ts       # Unit conversion functions
├── services/
│   ├── api.ts                  # Axios API client
│   └── auth-domain.tsx         # Domain-aware auth
└── types/                      # TypeScript types
```

## Routing

### Public Site (www.drip-3d.com)
| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | HomePage | Landing page |
| `/progress` | ProgressPage | Project progress (Linear) |
| `/team` | TeamPage | About the team |

### Team Portal (team.drip-3d.com)
| Route | Component | Purpose |
|-------|-----------|---------|
| `/dashboard` | Dashboard | Portal home |
| `/components` | ComponentRegistry | Component list |
| `/components/:id` | ComponentDetailPage | Component editor |
| `/models` | ModelsList | Physics models list |
| `/models/new` | ModelBuilder | Create physics model |
| `/instances/new` | InstanceCreator | Instantiate model |
| `/instances/new/:modelId` | InstanceCreator | Pre-selected model |
| `/analysis` | Analysis | Analysis dashboard |
| `/analysis/new` | AnalysisCreator | Create named analysis |
| `/analysis/:id/edit` | AnalysisCreator | Edit existing analysis |
| `/tests` | TestCampaign | Test management |
| `/resources` | Resources | Engineering resources |
| `/settings` | Settings | User preferences |
| `/login` | Login | Auth0 login |

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000  # Backend URL
```

### Build
```bash
npm run build     # Production build to dist/
npm run preview   # Preview production build
```

## Key Features

### Domain-Based Routing
The app serves two domains from one codebase:
```typescript
// hooks/useDomain.ts
if (hostname.includes('team.')) return 'team';
if (hostname === 'localhost')   return 'team';
return 'company';
```

### Unit System
User preferences for display units, with SI base storage:
```typescript
// UnitContext.tsx
<UnitProvider>
  <App />
</UnitProvider>

// Usage
const { getDisplayValue, formatWithUnit } = useUnitContext();
```

### Expression Input
Ghost text autocomplete for property references:
```
#FRAME.Height + 2 * #PLATE.Width
```

### Physics Models
4-step wizards for model creation and instantiation:
- ModelBuilder: Define → Inputs/Outputs → Equations → Validate
- InstanceCreator: Select → Bind → Attach → Review

## State Management

- **React Query** - Server state, caching, invalidation
- **React Context** - Global state (units, auth)
- **Local state** - Component-specific UI state

## Styling

- **Tailwind CSS** - Utility classes
- **Color scheme**:
  - Primary: `indigo-600`
  - Success: `green-500`
  - Error: `red-500`
  - Neutral: Gray shades

## Testing

```bash
npm run lint      # ESLint
npm run typecheck # TypeScript
```

## Documentation

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - System architecture
- [PHYSICS_MODELS.md](../docs/PHYSICS_MODELS.md) - Physics models system
- [VALUE_SYSTEM.md](../docs/VALUE_SYSTEM.md) - Expression engine

---

*Last Updated: December 27, 2025*
