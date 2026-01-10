---
title: "Test Execution"
description: "Recording measurements"
---

# Test Execution

**Route:** `/testing/runs/:runId/execute`

## Execution Features

- Setup checklist (must complete 100% before measurements)
- Input values display
- Measurement recording per output parameter
- Real-time validation feedback
- Procedure display
- Notes field (auto-saves on blur)
- Complete/Abort buttons

## Setup Phase

Setup checklist must be **100% complete** before starting measurements.

## Measurement Recording

For each output parameter:
1. Enter measured value
2. See real-time validation
3. Add optional notes
4. Click "Record Measurement"

## Validation Logic

| Condition | Status | Color |
|-----------|--------|-------|
| Within tolerance | PASS | Green |
| Within 1.5× tolerance | WARNING | Yellow |
| Beyond 1.5× tolerance | FAIL | Red |

## Completing a Run

Result suggestion based on measurements:
- **PASS**: All measurements OK
- **PARTIAL**: Some WARNING status
- **FAIL**: Any ERROR status

User can override the suggested result.

## Gotchas

- Setup checklist must be 100% complete before starting measurements
- Measurements cannot be edited after recording
- Validations only created on run completion
- Notes auto-save on blur
