---
title: "Test Runs"
description: "Starting test runs"
---

# Test Runs

**Route:** `/testing/protocols/:protocolId/run`

## Run Creator (4-Step Wizard)

### Step 1: Select Protocol

Choose from available protocols.

### Step 2: Select Component (Optional)

Link run to a component for traceability.

### Step 3: Configure Run Parameters

Fill input values based on protocol's input schema.

### Step 4: Review and Create

Confirm selections and start the run.

## Run Statuses

| Status | Description |
|--------|-------------|
| Setup | Initial state, completing checklist |
| In Progress | Recording measurements |
| Completed | Test finished with result |
| Aborted | Test cancelled |

## Result Types

| Result | Meaning |
|--------|---------|
| PASS | All measurements within tolerance |
| PARTIAL | Some measurements outside tolerance |
| FAIL | Critical measurements failed |

Result is auto-calculated from measurements but user can override.
