#!/bin/bash

# Quick sync script that runs commands as fast as possible

echo "🚀 Starting quick sync..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" || true
sleep 1

# Start port forwarding
echo "🔌 Starting port forward..."
kubectl port-forward svc/secondnature-alpha-db 5440:5432 -n secondnature-alpha &
PF_PID=$!

# Wait for port forward
sleep 3

# Test connection quickly
echo "🧪 Testing connection..."
if timeout 5 psql 'postgresql://postgres:postgres@localhost:5440/default?sslmode=require' -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Connection successful!"
    
    # Update environment
    sed -i '' 's|PG_DATABASE_URL=.*|PG_DATABASE_URL=postgresql://postgres:postgres@localhost:5440/default?sslmode=require|' local.env
    
    # Run sync commands as fast as possible
    echo "🔄 Syncing agents..."
    timeout 10 python3 -m src.cli agent sync-all || echo "Agents sync failed"
    
    echo "🔄 Syncing workflows..."
    timeout 10 python3 -m src.cli workflow sync-all || echo "Workflows sync failed"
    
    echo "✅ Sync completed!"
else
    echo "❌ Connection failed!"
fi

# Clean up
kill $PF_PID 2>/dev/null || true
echo "🎉 Done!"
