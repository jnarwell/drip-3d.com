---
title: "Contacts"
description: "Internal and external contact directory"
---

# Contacts

**Route:** `/resources` → Contacts tab

Directory of internal team members and external contacts.

## Contact Fields

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Full name |
| Email | Yes | Primary email address |
| Organization | No | Company or team |
| Expertise | No | Array of specialties |
| Secondary Email | No | Alternate email |
| Phone | No | Phone number |
| Notes | No | Additional information |
| Is Internal | No | Boolean: team member or external |

## Internal vs External

The `is_internal` boolean distinguishes:

| is_internal | Description |
|-------------|-------------|
| true | Team members, employees |
| false | Vendors, suppliers, consultants |

## Adding Contacts

1. Click "Add Contact"
2. Fill required fields (name, email)
3. Add optional details
4. Toggle "Internal" if team member
5. Save

## Expertise Tags

Add multiple expertise areas:

```
["Mechanical Design", "FEA", "GD&T"]
```

Used for:
- Searching by specialty
- Finding subject matter experts
- Component assignments

## Search and Filter

- **Search**: By name, email, or organization
- **Filter**: Internal only, external only, or all
- **Expertise filter**: Find by specialty

## Linking to Components

Contacts link to components as:
- Designer
- Reviewer
- Approver
- Point of contact

## Bulk Operations

- **Import**: CSV upload with headers matching field names
- **Export**: Download filtered list as CSV

## Contact Card

Click contact row to expand:
- All contact details
- Linked components
- Edit/Delete buttons
