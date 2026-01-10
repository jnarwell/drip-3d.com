---
title: "Test Results"
description: "Viewing test results"
---

# Test Results

**Route:** `/testing/runs/:runId`

## Run Detail View

### Summary
- Protocol name, category, version
- Linked component (if any)
- Timing (created, started, completed, duration)
- Result badge (PASS/PARTIAL/FAIL)

### Configuration
All input parameter values used for the run.

### Measurements Table
- Parameter name
- Measured value with unit
- Target value
- Error percentage
- Status (PASS/WARNING/FAIL)
- Timestamp
- Notes

### Validation Results
Color-coded validation display:
- **Green**: Within tolerance
- **Yellow**: Within 1.5× tolerance
- **Red**: Outside tolerance

## Result Interpretation

| Result | Meaning |
|--------|---------|
| PASS | All within tolerance |
| PARTIAL | Some marginal/failed |
| FAIL | Critical failures |

## Actions

- **Run Again**: Start new run with same protocol
- **Continue Execution**: Return to execution (if IN_PROGRESS)

## Aborted Runs

Display:
- ABORTED status
- Abort reason (if provided)
- Measurements recorded before abort
- No validation results
