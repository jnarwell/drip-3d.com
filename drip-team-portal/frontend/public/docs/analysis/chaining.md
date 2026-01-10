---
title: "Chaining Analyses"
description: "Linking analyses together"
---

# Chaining Analyses

Chain analyses by referencing outputs from one as inputs to another.

## Reference Syntax

```
#REF:{id}
#NODE:{id}
```

Where `{id}` is the output value node ID.

## Chain Topologies

### Linear
```
A → B → C → D
```

### Fan-out
```
    ┌→ B
A ──┼→ C
    └→ D
```

### Fan-in
```
A ──┐
B ──┼→ D
C ──┘
```

## Circular Reference Detection

The system prevents cycles:
```
A → B → C → A  ← ERROR
```

Error: "Circular reference detected"

## Real-Time Updates

With WebSocket connected:
1. Component property changes
2. Analysis A re-evaluates
3. Dependent analyses detect STALE
4. Cascade continues through chain

## Gotchas

- Circular dependency detection on #REF chains
- ValueNodes persist and update in-place to preserve FK references
- Analysis doesn't auto-recalculate unless explicitly triggered
