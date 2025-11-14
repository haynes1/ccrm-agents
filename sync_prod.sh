#!/bin/bash

# Script to sync agents and workflows to production database
# This script handles the unstable port forwarding issue

echo "🔄 Starting production database sync..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" || true
sleep 2

# Start port forwarding in background
echo "🔌 Starting port forward..."
kubectl port-forward svc/secondnature-alpha-db 5437:5432 -n secondnature-alpha &
PF_PID=$!

# Wait for port forward to establish
echo "⏳ Waiting for port forward to establish..."
sleep 5

# Test connection
echo "🧪 Testing database connection..."
if psql 'postgresql://postgres:postgres@localhost:5437/default?sslmode=require' -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful!"
    
    # Update environment file
    echo "📝 Updating database URL..."
    sed -i '' 's|PG_DATABASE_URL=.*|PG_DATABASE_URL=postgresql://postgres:postgres@localhost:5437/default?sslmode=require|' local.env
    
    # Run sync commands quickly
    echo "🔄 Syncing agents..."
    python3 -m src.cli agent sync-all
    
    echo "🔄 Syncing workflows..."
    python3 -m src.cli workflow sync-all
    
    echo "✅ Sync completed successfully!"
else
    echo "❌ Database connection failed!"
    exit 1
fi

# Clean up
echo "🧹 Cleaning up..."
kill $PF_PID 2>/dev/null || true

echo "🎉 All done!"
