---
title: "Testing"
description: "Overview of the testing system"
---

# Testing

**Routes:**
- `/testing` - Protocol list
- `/testing/protocols/new` - Create protocol
- `/testing/protocols/:protocolId` - View protocol
- `/testing/protocols/:protocolId/edit` - Edit protocol
- `/testing/protocols/:protocolId/run` - Create run
- `/testing/runs/:runId` - View run
- `/testing/runs/:runId/execute` - Execute run

## Protocol List

Table with:
- Protocol name
- Category
- Status (active/inactive)
- Run count

### Filtering
- Category filtering
- Active/Inactive filtering

## Run Statuses

| Status | Description |
|--------|-------------|
| Setup | Initial state, completing checklist |
| In Progress | Recording measurements |
| Completed | Test finished with result |
| Aborted | Test cancelled |

## Validation Logic

| Condition | Status | Color |
|-----------|--------|-------|
| Within tolerance | PASS | Green |
| Within 1.5× tolerance | WARNING | Yellow |
| Beyond 1.5× tolerance | FAIL | Red |

## Related Topics

- [Protocols](protocols.md) - Creating test protocols
- [Runs](runs.md) - Starting test runs
- [Execution](execution.md) - Recording measurements
- [Results](results.md) - Viewing results
