---
title: "Test Protocols"
description: "Creating test protocols"
---

# Test Protocols

**Routes:** `/testing/protocols/new`, `/testing/protocols/:protocolId/edit`

## Protocol Form Fields

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Protocol title |
| Description | No | Details |
| Category | Yes | Test category |
| Is Active | - | Toggle (default: active) |

## Input Parameters

Dynamic list with per-input fields:
- Name
- Unit
- Description
- Required toggle

## Output Parameters

Dynamic list with per-output fields:
- Name
- Unit
- Target Value
- Tolerance
- Description

## Setup Checklist

Dynamic list of checklist items:
- Each item: Description text

## Procedure

Rich text or markdown procedure steps.

## Equipment List

Dynamic list of required equipment.

## Protocol List

Table showing:
- Protocol name
- Category
- Status (active/inactive)
- Run count

### Filtering
- Category filtering
- Active/Inactive filtering
- Create new protocol button
