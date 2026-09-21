#!/usr/bin/env bash
# Quick start script for Personal AI Agent

set -e

echo "🚀 Personal AI Agent - Quick Start"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start backing services
echo "📦 Starting PostgreSQL and Redis..."
docker compose -f infra/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# Check SECRET_KEY
if grep -q "SECRET_KEY=change-me" .env 2>/dev/null; then
    echo "⚠️  WARNING: Using default SECRET_KEY. Generate a secure one with:"
    echo "   python backend/scripts/generate_secret_key.py"
fi

# Backend setup
if [ ! -d "backend/.venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    cd backend
    python -m venv .venv

    if [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi

    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt

    echo "🗄️  Running database migrations..."
    python manage.py migrate

    echo "🌱 Seeding demo data..."
    python manage.py seed_demo

    cd ..
else
    echo "✓ Backend virtual environment already exists"
fi

# Frontend setup
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "✓ Frontend dependencies already installed"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Start backend:  cd backend && .venv/Scripts/activate && python manage.py runserver"
echo "   2. Start frontend: cd frontend && npm run dev"
echo "   3. Visit: http://localhost:5173"
echo "   4. Login: demo / demo12345"
echo ""
echo "📚 Documentation:"
echo "   - Setup: docs/SETUP.md"
echo "   - Architecture: docs/ARCHITECTURE.md"
echo "   - Contributing: CONTRIBUTING.md"
echo "   - Next Steps: NEXT_STEPS.md"
echo ""
