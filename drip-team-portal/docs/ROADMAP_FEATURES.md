# Team Portal Roadmap - Feature Planning

## Current State (December 2025)

### Completed Features
- Component Registry (CRUD, properties, relationships)
- Value System with parametric expressions (`#FRAME.Height + 1m`)
- Dependency graph with cascade recalculation
- Materials Database (Materials Project API integration)
- Material property inheritance to components (with SI conversion)
- Unit system (35+ quantities, SI storage, user display preferences)
- Imperial/metric expressions (`#FRAME.Height - 2ft`)
- Cross-component references
- Keyboard-first UX (Cmd+K command palette)
- **Physics Models System (December 26-27, 2025)** - see details below

### Known Blockers
- Tables not yet working (prerequisite for several features below)

---

## Recently Completed

### Physics Models System (SimEngine Phase 1)
**Completed:** December 26-27, 2025
**Implementation:** 30-minute parallel build across 6 Claude instances

**What was built:**
- **Database Models**: PhysicsModel, PhysicsModelVersion, ModelInstance, ModelInput
- **Equation Engine**: Parser, evaluator, LaTeX generator (SymPy-based)
- **Dimensional Analysis**: 32 predefined dimensions, 197 unit mappings, validation
- **Model Evaluation**: Resolves inputs, evaluates equations, creates output ValueNodes
- **API Endpoints**: 7 endpoints for model CRUD, validation, instantiation
- **Model Builder**: 4-step wizard for creating physics models
- **Instance Creator**: 4-step wizard for instantiating models with bindings
- **Integration Tests**: 105 automated tests

**Capabilities:**
- Create reusable physics model templates (e.g., thermal expansion, stress)
- Define typed inputs/outputs with units
- Write equations with math functions: `sqrt()`, `sin()`, `cos()`, `exp()`, `ln()`
- Dimensional analysis catches physics errors before runtime
- Bind model inputs to component properties, constants, or literals
- Outputs integrate with Value System (can be referenced as `#COMPONENT.expansion`)
- LaTeX rendering for equation display

**Documentation:** See `docs/PHYSICS_MODELS.md` for comprehensive reference.

---

## Planned Features (Priority Order)

### 1. SimEngine Phase 2 (Enhancements)
**What it is:** Extend the completed Physics Models system

**Features:**
- Temperature-dependent property curves (not just static values)
- "What-if" scenario mode (change inputs, see cascading effects)
- LOOKUP bindings (execute table lookups as model inputs)
- Model library browser (pre-built templates)
- Version comparison UI

**Implementation notes:**
- Phase 1 complete - foundation exists
- Temperature curves need new data structure (array of {temp, value} pairs)
- LOOKUP binding requires table system completion

---

### 2. CostPredict (BOM Cost Tracking)
**What it is:** Cost estimation and tracking integrated with BOM

**Features:**
- Cost field per component (manual entry initially)
- BOM cost rollup (automatic sum)
- Quantity × unit cost calculations
- Scenario comparison ("What if we use aluminum instead of steel?")
- Track estimates vs actuals
- Manufacturing cost estimation (labor, tooling, etc.)
- Break-even calculations

**Implementation notes:**
- Add `unit_cost`, `quantity`, `cost_notes` to Component model
- BOM endpoint calculates rollup
- Scenario mode = clone component tree, modify materials, compare

---

### 3. TestBench (V&V Integration)
**What it is:** Requirements → Tests → Verification pipeline

**Features:**
- Requirements tracking (linked to components)
- Test definitions (procedure, expected results)
- Test execution logging (pass/fail, data)
- Requirement → Test traceability matrix
- DAQ integration (STM32/ESP32 sensor data) - future
- Automated test execution - future
- Test report generation

**Implementation notes:**
- New models: Requirement, TestDefinition, TestResult
- Link Requirements to Components
- Link Tests to Requirements
- Status tracking: not_tested → in_progress → passed/failed

---

### 4. DocGen (Report Generation)
**What it is:** Auto-generate documentation from component data

**Features:**
- Component spec sheets (PDF export)
- BOM export (Excel, PDF)
- Test reports from TestBench data
- Design documentation templates
- Requirement traceability reports
- Version history snapshots

**Implementation notes:**
- Use libraries: reportlab (PDF), openpyxl (Excel)
- Template system for customization
- Export endpoints: `/api/v1/export/component/{id}/pdf`

---

## Later Additions (Year 2+)

### 5. SourceLink/Scout (Supplier Integration)
- Vendor database
- Component sourcing (Digi-Key, Mouser, McMaster scraping)
- Quote comparison
- Lead time tracking
- Auto-populate from datasheets

### 6. CAD-Connect
- Pull dimensions from Onshape/SolidWorks
- Sync CAD → Component properties
- Alert on CAD changes

### 7. IP Tracker
- Prior art search
- Patent tracking
- NDA management
- Innovation capture

---

## Database Schema Additions Needed

```sql
-- For CostPredict
ALTER TABLE components ADD COLUMN unit_cost DECIMAL(12,2);
ALTER TABLE components ADD COLUMN quantity INTEGER DEFAULT 1;
ALTER TABLE components ADD COLUMN cost_notes TEXT;

-- For TestBench
CREATE TABLE requirements (
  id SERIAL PRIMARY KEY,
  component_id INTEGER REFERENCES components(id),
  title TEXT NOT NULL,
  description TEXT,
  priority TEXT, -- critical, high, medium, low
  status TEXT DEFAULT 'open', -- open, in_progress, verified, failed
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE test_definitions (
  id SERIAL PRIMARY KEY,
  requirement_id INTEGER REFERENCES requirements(id),
  name TEXT NOT NULL,
  procedure TEXT,
  expected_result TEXT,
  acceptance_criteria TEXT
);

CREATE TABLE test_results (
  id SERIAL PRIMARY KEY,
  test_definition_id INTEGER REFERENCES test_definitions(id),
  status TEXT, -- passed, failed, blocked
  actual_result TEXT,
  data JSONB, -- sensor data, measurements
  tested_by TEXT,
  tested_at TIMESTAMP DEFAULT NOW()
);
```

---

## Integration Architecture

```
Team Portal (hub)
    │
    ├── SimEngine (modeling) ──► Value System expressions
    │
    ├── CostPredict ──► BOM + component costs
    │
    ├── TestBench ──► Requirements + Tests + Results
    │
    └── DocGen ──► Export endpoints (PDF, Excel)
```

All features share:
- Same component registry (single source of truth)
- Same authentication
- Same unit system
- Real-time updates via query invalidation

---

## Success Metrics

- [x] **SimEngine Phase 1**: Physics models system complete (December 27, 2025)
  - Can create model templates with equations
  - Can instantiate with bound inputs
  - Dimensional analysis validates physics
  - Outputs integrate with Value System
- [ ] SimEngine Phase 2: Temperature curves, LOOKUP bindings
- [ ] CostPredict: BOM shows accurate cost rollup
- [ ] TestBench: Requirements linked to tests with pass/fail status
- [ ] DocGen: Can export component spec sheet as PDF

---

## Notes

- **SimEngine Phase 1 complete** - Physics models foundation built
- **Tables must work first** - many features depend on tabular data display
- **LOOKUP bindings blocked on tables** - can't lookup table values without working tables
- **CostPredict is quick win** - just add cost fields to existing BOM
- **TestBench is larger scope** - new models, new UI, new workflows
- **DocGen can be incremental** - start with simple exports, add templates later

---

*Last Updated: December 27, 2025*
