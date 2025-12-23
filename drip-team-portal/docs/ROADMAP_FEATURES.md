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

### Known Blockers
- Tables not yet working (prerequisite for several features below)

---

## Planned Features (Priority Order)

### 1. SimEngine (Modeling Page Enhancement)
**What it is:** Extend the Value System with physics-based formulas

**Features:**
- Pre-built formula templates:
  - Thermal resistance: `R = L / (k * A)`
  - Heat transfer: `Q = k * A * ΔT / L`
  - Pressure drop (Darcy-Weisbach)
  - Stress/strain calculations
  - Fluid flow (Reynolds, etc.)
- Temperature-dependent property curves (not just static values)
- "What-if" scenario mode (change inputs, see cascading effects)
- Formula library browser

**Implementation notes:**
- Builds on existing Value System
- Add formula templates as pre-defined expressions
- Temperature curves need new data structure (array of {temp, value} pairs)

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

- [ ] SimEngine: Can calculate thermal resistance across assembly
- [ ] CostPredict: BOM shows accurate cost rollup
- [ ] TestBench: Requirements linked to tests with pass/fail status
- [ ] DocGen: Can export component spec sheet as PDF

---

## Notes

- **Tables must work first** - many features depend on tabular data display
- **SimEngine is highest leverage** - extends what's already built
- **CostPredict is quick win** - just add cost fields to existing BOM
- **TestBench is larger scope** - new models, new UI, new workflows
- **DocGen can be incremental** - start with simple exports, add templates later
