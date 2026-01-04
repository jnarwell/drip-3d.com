# Resources Module

**Last Updated:** 2026-01-02

## Overview

Central hub for team documents, data, contacts, and reference materials. The Resources section provides unified access to all project information.

---

## Subpages

### Data Tables
- Structured data storage
- CSV-like tables for project data
- Import/export capabilities

### Constants
- Physics/engineering constants
- Symbol, value, unit, category
- Example: `g = 9.81 m/s²` (Physics)

### Documents
Files, links, and Drive integrations.

**Supported Types:**
`doc` | `pdf` | `spreadsheet` | `slides` | `image` | `video` | `link` | `folder` | `paper`

**Features:**
- Google Drive integration (browse, search, link files)
- Collections (organize docs into groups)
- Starring (quick access to important docs)
- Bulk operations (multi-select, bulk add to collection, bulk delete)
- Sort by: date added, name, type
- Filter by: type, tags, collection, starred

### Contacts
- People and companies
- Email, phone, company, role, notes

---

## Tagging Standards

### Recommended Tags

**By Phase:**
`phase-1` `phase-2` `l1-demo` `l2` `l4`

**By System:**
`acoustic` `thermal` `control` `mechanical` `electrical`
`droplet` `nozzle` `chamber` `transducer`

**By Type:**
`research` `reference` `spec` `datasheet`
`meeting-notes` `decision` `template`
`vendor` `supplier` `quote`

**By Status:**
`active` `archived` `draft` `approved`
`needs-review` `outdated`

**By Priority:**
`critical` `important` `reference-only`

### Tag Guidelines
- Use lowercase, hyphenated: `meeting-notes` not `Meeting Notes`
- Be specific: `aluminum-6061` not just `material`
- Max 5-7 tags per document
- Prefer existing tags over creating new ones

---

## Collections vs Tags

| Use Collections for... | Use Tags for... |
|------------------------|-----------------|
| Active project groupings | Categorization |
| Curated sets | Searchable attributes |
| Team-specific views | Cross-cutting concerns |
| Temporary organization | Permanent metadata |

**Example:**
- Collection: "L1 Demo Prep" (temporary working set)
- Tags: `l1-demo`, `acoustic`, `critical` (permanent attributes)

---

## V2 Features (Planned)

### Vendors/Suppliers Subpage
- Lead times, MOQs, pricing
- Catalog links
- Part number cross-reference
- Vendor ratings

### Smart Collections
- Auto-populate based on rules
- Example: "All PDFs tagged 'datasheet'"

### Document Preview
- Inline preview without leaving page
- PDF viewer, image viewer

### Related Documents
- "Also linked to Component X"
- Auto-suggestions based on tags/content

### Folder Import
- Select Drive folder -> bulk import all files

---

*See also: [TAGGING_GUIDE.md](./TAGGING_GUIDE.md) for quick reference*
