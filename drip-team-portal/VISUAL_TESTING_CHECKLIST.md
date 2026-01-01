# Visual Testing Checklist - Physics Models System

## Prerequisites

Before testing, ensure:

1. **Backend running:**
   ```bash
   cd drip-team-portal/backend
   uvicorn app.main:app --reload
   ```

2. **Frontend running:**
   ```bash
   cd drip-team-portal/frontend
   npm start
   ```

3. **Database migrated:**
   ```bash
   cd drip-team-portal/backend
   alembic upgrade head
   ```

4. **Navigate to:** http://localhost:3000 (or team.drip-3d.com if deployed)

---

## Test 1: Model Builder Wizard

### Step 1: Navigate to Model Builder
- [ ] Click "Models" in sidebar navigation
- [ ] Click "New Model" button on `/models` page
- [ ] **Expected:** Redirects to `/models/new`
- [ ] **Expected:** 4-step progress stepper appears at top

### Step 2: Define Model (Step 1)
- [ ] Form shows: Name, Description, Category fields
- [ ] Enter name: `Thermal Expansion`
- [ ] Enter description: `Calculates thermal expansion for materials`
- [ ] Select category: `Thermal`
- [ ] **Expected:** "Next" button becomes enabled
- [ ] Click "Next"
- [ ] **Expected:** Progress stepper shows Step 2 active

### Step 3: Inputs & Outputs (Step 2)
- [ ] Section shows "Inputs" with "Add Input" button
- [ ] Section shows "Outputs" with "Add Output" button

**Add Input 1:**
- [ ] Click "Add Input"
- [ ] Enter name: `length`
- [ ] Enter unit: `m`
- [ ] Enter description: `Initial length`
- [ ] **Expected:** Input appears in list

**Add Input 2:**
- [ ] Click "Add Input"
- [ ] Enter name: `CTE`
- [ ] Enter unit: `1/K`
- [ ] Enter description: `Coefficient of thermal expansion`

**Add Input 3:**
- [ ] Click "Add Input"
- [ ] Enter name: `delta_T`
- [ ] Enter unit: `K`
- [ ] Enter description: `Temperature change`

**Add Output:**
- [ ] Click "Add Output"
- [ ] Enter name: `expansion`
- [ ] Enter unit: `m`
- [ ] Enter description: `Calculated expansion`

- [ ] **Expected:** Can edit/delete any input/output
- [ ] Click "Next"

### Step 4: Equations (Step 3)
- [ ] Textarea appears labeled "expansion ="
- [ ] Variable buttons appear for inputs: `length`, `CTE`, `delta_T`
- [ ] Enter equation: `length * CTE * delta_T`
- [ ] **Expected:** Variable buttons insert text when clicked
- [ ] Click "Next"

### Step 5: Validate & Create (Step 4)
- [ ] Shows "Validating..." spinner briefly
- [ ] **Expected:** Shows "✓ Dimensions valid" with green checkmark
- [ ] **Expected:** Shows LaTeX preview of equation (rendered, not raw code)
- [ ] **Expected:** Equation displays as: L · α · ΔT (or similar formatted math)
- [ ] Click "Create Model"
- [ ] **Expected:** Redirects to `/models`
- [ ] **Expected:** Success message "Model 'Thermal Expansion' created!"

### Verification
- [ ] New model appears in models list
- [ ] Model shows correct category badge
- [ ] Can click model to see details

---

## Test 2: Instance Creator Wizard

### Prerequisite
Complete Test 1 (need a model to instantiate)

### Step 1: Navigate to Instance Creator
- [ ] From `/models`, click "Instantiate" button
- [ ] OR navigate directly to `/instances/new`
- [ ] **Expected:** 4-step wizard appears

### Step 2: Select Model (Step 1)
- [ ] List of available models appears
- [ ] Can filter by category
- [ ] Click "Thermal Expansion" model
- [ ] **Expected:** Model card highlights as selected
- [ ] **Expected:** Preview shows inputs/outputs
- [ ] Click "Next"

### Step 3: Bind Inputs (Step 2)
- [ ] Each input appears with binding selector
- [ ] Tabs show: [Component Property] [LOOKUP] [Constant] [Literal]

**Bind length:**
- [ ] Click "Literal" tab
- [ ] Enter value: `0.003` (or `3`)
- [ ] Select/enter unit: `m` (or `mm`)

**Bind CTE:**
- [ ] Click "Literal" tab
- [ ] Enter value: `8.1e-6`
- [ ] Unit shown: `1/K`

**Bind delta_T:**
- [ ] Click "Literal" tab
- [ ] Enter value: `500`
- [ ] Unit shown: `K`

- [ ] **Expected:** All required inputs show green checkmark
- [ ] Click "Next"

### Step 4: Attach to Component (Step 3) - Optional
- [ ] Component selector dropdown appears
- [ ] Shows info: "Attaching to a component will create properties like #COMPONENT.expansion"
- [ ] Can skip (optional step)
- [ ] OR select "SYSTEM" component if available
- [ ] Click "Next"

### Step 5: Review & Create (Step 4)
- [ ] Shows summary:
  - Model: Thermal Expansion
  - Bindings: length=0.003m, CTE=8.1e-6/K, delta_T=500K
  - Target: (none or selected component)
- [ ] Instance name field appears with default value
- [ ] Can edit instance name
- [ ] Click "Create Instance"
- [ ] **Expected:** Success message appears
- [ ] **Expected:** Redirects to component page (if attached) or models list

---

## Test 3: Validation Error Handling

### Test: Invalid Equation
- [ ] Start new model creation at `/models/new`
- [ ] Enter name, category (Step 1)
- [ ] Add one input: `x`, unit: `m`
- [ ] Add one output: `result`, unit: `m`
- [ ] In equations (Step 3), enter: `x + undefined_var`
- [ ] Go to Step 4 (Validate)
- [ ] **Expected:** Error message about undefined variable
- [ ] **Expected:** "Create Model" button disabled

### Test: Dimension Mismatch
- [ ] Start new model
- [ ] Add input: `length`, unit: `m`
- [ ] Add input: `time`, unit: `s`
- [ ] Add output: `result`, unit: `m`
- [ ] Enter equation: `length + time` (can't add meters and seconds)
- [ ] Go to Validate step
- [ ] **Expected:** Dimension error shown
- [ ] **Expected:** Clear error message about incompatible dimensions

---

## Test 4: Browser DevTools Checks

While performing above tests, keep DevTools open (F12):

### Console Tab
- [ ] No JavaScript errors (red text)
- [ ] No failed API calls in console

### Network Tab
- [ ] API calls return 200 status
- [ ] `/api/v1/physics-models/validate` called before creation
- [ ] `/api/v1/physics-models` POST called on create
- [ ] Response contains `id`, `name`, `current_version`

---

## Test 5: Models List Display

- [ ] Navigate to `/models`
- [ ] Created models appear in list
- [ ] Each model shows:
  - Name
  - Category badge
  - Description (truncated if long)
  - Created date
- [ ] "New Model" button present
- [ ] "Instantiate" button present
- [ ] Models can be filtered by category (if filter exists)

---

## Expected API Responses

### POST /api/v1/physics-models/validate
```json
{
  "valid": true,
  "errors": [],
  "dimensional_analysis": {
    "expansion": {
      "valid": true,
      "message": "Dimensions valid"
    }
  },
  "latex_preview": {
    "expansion": "L \\cdot \\alpha \\cdot \\Delta T"
  }
}
```

### POST /api/v1/physics-models
```json
{
  "id": 1,
  "name": "Thermal Expansion",
  "category": "thermal",
  "current_version": {
    "id": 1,
    "version": 1,
    "equation_latex": {"expansion": "L \\cdot \\alpha \\cdot \\Delta T"}
  }
}
```

---

## Issue Reporting Format

If any test fails, report using this format:

```
## Issue: [Brief description]

**Test:** [Which test step]
**Expected:** [What should happen]
**Actual:** [What actually happened]
**Screenshot:** [Attach if possible]
**Console errors:** [Copy any JS errors]
**API Response:** [Copy response body if relevant]
```

---

## Summary Checklist

| Feature | Status |
|---------|--------|
| Model Builder navigable | ⬜ |
| Step 1: Define model | ⬜ |
| Step 2: Add inputs/outputs | ⬜ |
| Step 3: Enter equations | ⬜ |
| Step 4: Validation works | ⬜ |
| Model creation succeeds | ⬜ |
| LaTeX renders correctly | ⬜ |
| Instance Creator navigable | ⬜ |
| Model selection works | ⬜ |
| Input binding works | ⬜ |
| Instance creation succeeds | ⬜ |
| Error handling works | ⬜ |
| No console errors | ⬜ |
| API calls succeed | ⬜ |

**Overall Status:** ⬜ PASS / ⬜ FAIL

**Tested by:** _______________
**Date:** _______________
