# Document Tagging Quick Reference

**Last Updated:** 2026-01-02

Quick reference card for consistent document tagging across the DRIP Team Portal.

---

## Phase Tags
```
phase-1  phase-2  l1-demo  l2  l4
```

## System Tags
```
acoustic  thermal  control  mechanical  electrical
```

## Component Tags
```
droplet  nozzle  chamber  transducer  heater
substrate  actuator  sensor  power-supply
```

## Document Type Tags
```
research  spec  datasheet  meeting-notes  decision  template
design-doc  test-plan  test-report  analysis  simulation
```

## Source Tags
```
vendor  internal  stanford  external  supplier
```

## Status Tags
```
active  archived  draft  approved  needs-review  outdated
```

## Priority Tags
```
critical  important  reference-only
```

---

## Guidelines

| Do | Don't |
|----|-------|
| `meeting-notes` | `Meeting Notes` |
| `aluminum-6061` | `material` |
| Max 5-7 tags | 15+ tags |
| Reuse existing tags | Create duplicates |

---

## Common Combinations

**Design Documents:**
`design-doc` + `[system]` + `[phase]` + `active`

**Vendor Datasheets:**
`datasheet` + `vendor` + `[component]` + `reference-only`

**Meeting Notes:**
`meeting-notes` + `[phase]` + `[date-tag]`

**Test Reports:**
`test-report` + `[system]` + `[phase]` + `[status]`

---

*See also: [RESOURCES.md](./RESOURCES.md) for full documentation*
