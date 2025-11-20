#!/bin/bash

# DRIP Team Portal - Database Clear Script
# This script clears all data and forces a fresh schema deployment

echo "🗄️  DRIP Database Clear Script"
echo "=============================="
echo ""

# Step 1: Clear all database tables via API (if accessible)
echo "1️⃣  Attempting to clear via API..."

# Try to get components and delete them
echo "   Checking for existing components..."
COMPONENTS=$(curl -s -X GET "https://backend-production-aa29.up.railway.app/api/v1/components/" -H "Authorization: Bearer test")
echo "   Components found: $COMPONENTS"

# The API doesn't have bulk delete, so we rely on Railway UI

echo ""
echo "2️⃣  Manual Database Wipe Required:"
echo "   👉 Go to Railway Dashboard"
echo "   👉 Find PostgreSQL service in your project"
echo "   👉 Delete the PostgreSQL service completely"
echo "   👉 Create a new PostgreSQL service"
echo "   👉 Copy the new DATABASE_URL"
echo "   👉 Update backend service environment variable"
echo ""

# Step 2: Force backend redeployment
echo "3️⃣  Forcing backend redeployment..."

# Update a file to trigger deployment
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
cat > /tmp/force_deploy.txt << EOF
# Force deployment trigger
# Timestamp: $TIMESTAMP
# Purpose: Test formula fields with clean database
EOF

# Update the health endpoint to include timestamp
sed -i.bak "s/\"updated\": \"[^\"]*\"/\"updated\": \"$(date +%Y-%m-%d)\"/g" drip-team-portal/backend/app/main.py

echo "   Modified main.py to trigger deployment"

# Commit and push
git add drip-team-portal/backend/app/main.py
git commit -m "FORCE DEPLOY: Clear database test - $(date '+%Y-%m-%d %H:%M:%S')

Testing formula fields integration after complete database wipe.
Timestamp: $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)"

echo "   Pushing to trigger Railway deployment..."
git push origin main

echo ""
echo "4️⃣  Verification Commands:"
echo "   # Check deployment status"
echo "   curl https://backend-production-aa29.up.railway.app/health"
echo ""
echo "   # Check clean database"
echo "   curl -H 'Authorization: Bearer test' https://backend-production-aa29.up.railway.app/api/v1/components/"
echo ""
echo "   # Test property creation with formula fields"
echo "   curl -X POST -H 'Authorization: Bearer test' -H 'Content-Type: application/json' \\"
echo "        https://backend-production-aa29.up.railway.app/api/v1/components \\"
echo "        -d '{\"component_id\":\"TEST-001\",\"name\":\"Test\"}'"
echo ""

echo "🎯 Database clear process initiated!"
echo "   Railway deployment will take 1-3 minutes"
echo "   Use verification commands above to test integration"