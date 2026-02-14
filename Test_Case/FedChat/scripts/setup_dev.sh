#!/bin/bash
# Setup script for development environment

set -e

echo "FedChat Development Environment Setup"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker $(docker --version | awk '{print $3}')"

# Check Docker Compose
echo "Checking Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found"
    exit 1
fi
echo "✅ Docker Compose"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and configure"
echo "  2. Run: docker compose up -d"
echo "  3. Run: python scripts/init_db.py"
echo "  4. Run: python scripts/create_admin.py"
echo "  5. Start backend: uvicorn main:app --reload"
echo ""
echo "For production Kubernetes deployment:"
echo "  kubectl apply -f kubernetes/"
