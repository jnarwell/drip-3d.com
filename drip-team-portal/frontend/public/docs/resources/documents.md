---
title: "Documents"
description: "Document management with Google Drive integration"
---

# Documents

**Route:** `/resources` → Documents tab

Document management with Google Drive integration and collections.

## Google Drive Integration

### Connecting

1. Click "Connect Google Drive"
2. OAuth2 authentication flow
3. Grant permissions to access Drive
4. Connection persists across sessions

### Adding from Drive

1. Click "Add from Drive"
2. File picker opens
3. Navigate or search Drive
4. Select file(s)
5. Files linked (not copied)

## Document Types

| Type | Icon | Description |
|------|------|-------------|
| doc | 📄 | Google Docs, Word |
| spreadsheet | 📊 | Google Sheets, Excel |
| slides | 📽️ | Google Slides, PowerPoint |
| pdf | 📕 | PDF documents |
| paper | 📝 | Research papers |
| video | 🎬 | Video files |
| image | 🖼️ | Images, diagrams |
| link | 🔗 | External URLs |

## Collections

Organize documents into collections with color coding.

### Available Colors

10 color options:
- Red
- Orange
- Yellow
- Green
- Teal
- Blue
- Purple
- Pink
- Gray
- Brown

### Creating Collections

1. Click "New Collection"
2. Enter name
3. Select color
4. Drag documents to collection

### Managing Collections

- Rename: Click collection name
- Recolor: Click color swatch
- Delete: Removes collection only (not documents)

## Document Fields

| Field | Required | Description |
|-------|----------|-------------|
| Title | Yes | Document name |
| Type | Yes | Document type |
| URL | No | Link to document |
| Description | No | Notes about document |
| Collection | No | Organizing collection |

## Search and Filter

- **Search**: By title or description
- **Filter by type**: Select document type
- **Filter by collection**: Select collection

## Linking to Components

Documents can be linked to components:
1. Open component detail
2. Go to Documents tab
3. Link existing or add new document

## Permissions

Document access follows Google Drive permissions. The portal links to files but does not modify Drive permissions.
