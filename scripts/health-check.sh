#!/usr/bin/env bash
# Health check script for Personal AI Agent platform

set -e

echo "🔍 Personal AI Agent - System Health Check"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Check function
check() {
    local name="$1"
    local command="$2"

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        ((FAILED++))
        return 1
    fi
}

# Warning function
warn() {
    local name="$1"
    echo -e "${YELLOW}⚠${NC} $name"
    ((WARNINGS++))
}

# Check Docker
echo "📦 Docker Services"
echo "------------------"
if command -v docker &> /dev/null; then
    check "Docker installed" "true"
    if docker ps &> /dev/null; then
        check "Docker daemon running" "true"

        # Check PostgreSQL container
        if docker ps --format '{{.Names}}' | grep -q "agent_db\|postgres"; then
            check "PostgreSQL container running" "true"
        else
            echo -e "${RED}✗${NC} PostgreSQL container not found"
            echo "  Run: docker compose -f infra/docker-compose.yml up -d"
            ((FAILED++))
        fi

        # Check Redis container
        if docker ps --format '{{.Names}}' | grep -q "agent_redis\|redis"; then
            check "Redis container running" "true"
        else
            echo -e "${RED}✗${NC} Redis container not found"
            echo "  Run: docker compose -f infra/docker-compose.yml up -d"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗${NC} Docker daemon not running"
        echo "  Start Docker Desktop"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗${NC} Docker not installed"
    ((FAILED++))
fi

echo ""
echo "🐍 Python Backend"
echo "------------------"
check "Python 3.12+ installed" "python --version | grep -E 'Python 3\.(1[2-9]|[2-9][0-9])'"

if [ -d "backend/.venv" ]; then
    check "Virtual environment exists" "true"
    if [ -f "backend/.venv/Scripts/python.exe" ] || [ -f "backend/.venv/bin/python" ]; then
        check "Python in venv accessible" "true"
    else
        warn "Virtual environment may be incomplete"
    fi
else
    echo -e "${RED}✗${NC} Virtual environment not found"
    echo "  Run: cd backend && python -m venv .venv"
    ((FAILED++))
fi

if [ -f ".env" ]; then
    check ".env file exists" "true"

    # Check for placeholder SECRET_KEY
    if grep -q "SECRET_KEY=change-me" .env; then
        warn "SECRET_KEY is still placeholder (generate with: python backend/scripts/generate_secret_key.py)"
    else
        check "SECRET_KEY configured" "true"
    fi

    # Check DATABASE_URL port
    if grep -q "DATABASE_URL=.*:5433" .env; then
        check "DATABASE_URL uses correct port (5433)" "true"
    elif grep -q "DATABASE_URL=.*:5432" .env; then
        warn "DATABASE_URL uses port 5432 (should be 5433 for Docker)"
    fi
else
    echo -e "${RED}✗${NC} .env file not found"
    echo "  Run: cp .env.example .env"
    ((FAILED++))
fi

echo ""
echo "📦 Node.js Frontend"
echo "------------------"
check "Node.js 20+ installed" "node --version | grep -E 'v(2[0-9]|[3-9][0-9])'"

if [ -d "frontend/node_modules" ]; then
    check "Frontend dependencies installed" "true"
else
    echo -e "${RED}✗${NC} Frontend dependencies not installed"
    echo "  Run: cd frontend && npm install"
    ((FAILED++))
fi

if [ -f "frontend/vite.config.ts" ]; then
    check "Vite config exists" "true"
fi

echo ""
echo "🔌 Network Ports"
echo "------------------"
check "Port 5432 available (PostgreSQL)" "! lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 || true"
check "Port 5433 available (Docker PostgreSQL)" "! lsof -Pi :5433 -sTCP:LISTEN -t >/dev/null 2>&1 || true"
check "Port 6379 available (Redis)" "! lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1 || true"
check "Port 8000 available (Django)" "! lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 || true"
check "Port 5173 available (Vite)" "! lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 || true"

echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to run.${NC}"
    echo ""
    echo "Start the platform:"
    echo "  1. docker compose -f infra/docker-compose.yml up -d"
    echo "  2. cd backend && .venv/Scripts/activate && python manage.py runserver"
    echo "  3. cd frontend && npm run dev"
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ System ready with warnings${NC}"
    exit 0
else
    echo -e "${RED}✗ Fix the failed checks above before running${NC}"
    exit 1
fi
