# Debug Instructions for Materials Project Search

1. Open Chrome DevTools (F12 or right-click → Inspect)
2. Go to the Console tab
3. Navigate to: http://localhost:3000/components/CMP-001
4. Look for debug messages starting with 🔍

## What to look for:

1. **MaterialSelector Debug** - Should show the component state
2. Click on "Select Material" button
3. In the modal, you should see:
   - Radio buttons for "Local Database" and "Materials Project"
   - Click "Materials Project" radio button
   - Check console for "🔄 Search mode changing to: materials-project"

## To test Materials Project search:

1. Select "Materials Project" radio option
2. Type "Al" in the search box
3. Watch console for:
   - "🚀 Starting Materials Project search"
   - "📤 Sending MP search request"
   - "📥 MP search results"

## Current Status:
- Backend API is working (tested with curl)
- Frontend has the UI elements
- Need to verify they're visible and working in browser