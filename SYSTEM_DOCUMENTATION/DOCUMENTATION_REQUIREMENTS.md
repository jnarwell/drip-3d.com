# Documentation Requirements Guide

## Purpose

This guide establishes mandatory documentation practices for all DRIP codebase modifications. Following these requirements ensures system maintainability, prevents technical debt, and enables effective AI-assisted development.

## Core Principle

**"No Code Without Documentation"** - Every change must maintain or improve documentation quality.

## Mandatory Process for All Changes

### 1. Pre-Change Documentation Review

Before making ANY code changes:

```
STOP → SEARCH → READ → PLAN → DOCUMENT → CODE
```

#### Required Steps:

1. **Search for Existing Documentation**
   ```bash
   # Check main documentation
   ls SYSTEM_DOCUMENTATION/
   
   # Search for relevant docs
   grep -r "feature_name" SYSTEM_DOCUMENTATION/
   
   # Check inline documentation
   grep -r "TODO\|FIXME\|NOTE" src/
   ```

2. **Identify Documentation Gaps**
   - If NO documentation exists for the area you're modifying → 🚨 **STOP ALL WORK**
   - Create documentation FIRST before proceeding
   - Document current state before changing it

3. **Read All Related Documentation**
   - System overview
   - Specific component docs
   - Integration points
   - API references

### 2. File Management Protocol

#### When Adding New Features:

1. **Check for Redundancy**
   ```bash
   # Search for similar functionality
   grep -r "similar_function" --include="*.ts" --include="*.tsx" --include="*.py"
   
   # Check imports for duplicate modules
   find . -name "*.py" -o -name "*.ts" | xargs grep "import.*similar"
   ```

2. **Ensure Proper Placement**
   - Follow existing patterns
   - Check architectural documentation
   - Verify no duplication exists

3. **Legacy File Management**
   ```bash
   # If replacing old functionality:
   1. Identify obsolete files
   2. Move to legacy/ folder
   3. Update documentation to reflect change
   4. Git commit with clear message
   ```

#### Example Legacy Migration:
```bash
# Create legacy structure if needed
mkdir -p legacy/[feature_area]/

# Move obsolete files
mv old_implementation.py legacy/[feature_area]/

# Document the migration
echo "Moved to legacy on [date] - replaced by new_implementation.py" > legacy/[feature_area]/MIGRATION_NOTE.md
```

### 3. Documentation Update Requirements

#### For Every Code Change:

1. **Update Existing Documentation**
   ```markdown
   # In relevant .md file, add:
   
   ## Change Log
   - **Date**: 2025-12-03
   - **Change**: Brief description
   - **Impact**: What this affects
   - **Migration**: Any required updates
   ```

2. **Update Integration Points**
   - If changing APIs → Update API documentation
   - If changing data models → Update schema docs
   - If changing UI → Update component docs

3. **Update Examples**
   - Ensure all code examples still work
   - Update deprecated patterns
   - Add new usage examples

#### Documentation Template for New Features:

```markdown
# [Feature Name] Documentation

## Overview
Brief description of what this feature does and why it exists.

## Architecture
How this fits into the overall system.

## API Reference
### Endpoints (if applicable)
```
METHOD /api/path
Request: { ... }
Response: { ... }
```

### Functions/Classes
```python
def function_name(params) -> return_type:
    """
    Description of function.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    
    Raises:
        ErrorType: When this happens
    """
```

## Usage Examples
### Basic Usage
```python
# Example code here
```

### Advanced Usage
```python
# More complex example
```

## Integration Points
- Integrates with: [List other systems]
- Depends on: [List dependencies]
- Used by: [List consumers]

## Configuration
Any environment variables, settings, or configuration options.

## Error Handling
Common errors and how to resolve them.

## Performance Considerations
- Caching strategies
- Optimization tips
- Limits and quotas

## Testing
How to test this feature.

## Migration Guide
If replacing old functionality, how to migrate.

## Change Log
- **Date**: When created/modified
- **Author**: Who made changes
- **Changes**: What changed
```

### 4. Red Flags - When to STOP Work

#### 🚨 IMMEDIATE STOP Conditions:

1. **No Documentation Found**
   ```
   If searching for feature documentation returns nothing:
   - STOP coding
   - Document current understanding
   - Get approval before proceeding
   ```

2. **Conflicting Documentation**
   ```
   If documentation contradicts code:
   - STOP coding
   - Investigate discrepancy
   - Update documentation to reflect reality
   - Then proceed with changes
   ```

3. **Unclear Integration Points**
   ```
   If you don't understand how systems connect:
   - STOP coding
   - Map out integration points
   - Document findings
   - Verify understanding before proceeding
   ```

4. **Missing API Documentation**
   ```
   If modifying an undocumented API:
   - STOP coding
   - Document existing API behavior
   - Define changes clearly
   - Update consumers
   ```

### 5. Documentation Quality Checklist

Before committing any changes, verify:

- [ ] **Searchable**: Can someone find this documentation by searching for the feature name?
- [ ] **Current**: Does documentation match the actual code?
- [ ] **Complete**: Are all functions, APIs, and integration points documented?
- [ ] **Clear**: Can a new developer understand this without additional context?
- [ ] **Exampled**: Are there working code examples?
- [ ] **Linked**: Is this connected to the main SYSTEM_OVERVIEW.md?

### 6. Enforcement and Compliance

#### Git Commit Message Format:
```
feat(component): Add new capability

- Updated documentation: SYSTEM_DOCUMENTATION/relevant_file.md
- Moved legacy files: old_file.py → legacy/feature/
- Breaking changes: None

Docs: ✓ Updated
Legacy: ✓ Cleaned
Tests: ✓ Passing
```

#### Pull Request Checklist:
```markdown
## Documentation Checklist
- [ ] Documentation searched and read
- [ ] Redundant files checked
- [ ] Legacy files moved if applicable
- [ ] Documentation updated/created
- [ ] Examples tested and working
- [ ] Integration points documented
- [ ] SYSTEM_OVERVIEW.md updated if needed
```

### 7. Special Considerations for AI Assistants

When working as an AI assistant (like Claude):

1. **Always Start with Documentation**
   ```
   User: "Add feature X"
   
   AI Response Process:
   1. "Let me first check the existing documentation..."
   2. Search and read relevant docs
   3. "I found/didn't find documentation for this area..."
   4. Present findings before coding
   ```

2. **Flag Missing Documentation**
   ```
   "⚠️ WARNING: No documentation found for this system.
   Before proceeding, I should create documentation for the 
   current state. Should I document the existing system first?"
   ```

3. **Maintain Documentation Context**
   ```
   "Based on the documentation in SYSTEM_DOCUMENTATION/[file].md,
   this change will affect [list systems]. I'll need to update
   the following documentation files: [list files]"
   ```

## Examples of Good Practice

### Example 1: Adding a New API Endpoint

```bash
# 1. Check existing API documentation
cat SYSTEM_DOCUMENTATION/04_MATERIALS_DATABASE_API.md

# 2. Find similar endpoints
grep -r "similar_endpoint" backend/app/api/

# 3. Document new endpoint FIRST
echo "## New Endpoint Design
### POST /api/v1/materials/bulk-import
..." >> API_DESIGN.md

# 4. Implement with documentation
# 5. Update main API documentation
# 6. Add integration examples
```

### Example 2: Refactoring Legacy Code

```bash
# 1. Document current behavior
echo "## Current System Behavior
The existing system works by..." > REFACTOR_PLAN.md

# 2. Identify files to legacy
find . -name "*old_system*" > files_to_legacy.txt

# 3. Create migration plan
echo "## Migration Steps
1. Move old files to legacy/
2. Update imports in [files]
3. ..." >> REFACTOR_PLAN.md

# 4. Execute plan with documentation updates
```

## Consequences of Non-Compliance

1. **Code Without Documentation**: Will not be merged
2. **Undocumented Breaking Changes**: Immediate rollback
3. **Missing Legacy Migration**: Technical debt tracking
4. **Incomplete Documentation**: Blocked until complete

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│        DOCUMENTATION WORKFLOW           │
├─────────────────────────────────────────┤
│ 1. SEARCH existing docs                 │
│    ↓ Found?                            │
│    No → STOP & CREATE DOCS FIRST       │
│    Yes → Continue                       │
│                                         │
│ 2. READ all related documentation       │
│                                         │
│ 3. CHECK for redundant code            │
│    ↓ Found duplicates?                 │
│    Yes → CONSOLIDATE or STOP           │
│                                         │
│ 4. PLAN changes with doc updates       │
│                                         │
│ 5. UPDATE docs BEFORE coding           │
│                                         │
│ 6. CODE the implementation             │
│                                         │
│ 7. VERIFY docs match implementation    │
│                                         │
│ 8. COMMIT with doc references          │
└─────────────────────────────────────────┘
```

## Remember

**Documentation is not optional** - it's a critical part of the codebase. Poor documentation is technical debt that compounds over time. Take the time to document properly; your future self (and future AI assistants) will thank you.

---

*Last Updated: December 2, 2025*
*Version: 1.0.0*
*Status: MANDATORY - All contributors must follow*