#!/bin/bash
# Development environment setup script

set -e

echo "🚀 Setting up Censudx API Gateway development environment"
echo "========================================================"

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing gateway dependencies..."
cd gateway
pip install -r requirements.txt
cd ..

echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
JWT_SECRET_KEY=development-secret-key-change-in-production
DATABASE_URL=postgresql://inventory_user:inventory_password@localhost:5432/inventory_db
RABBITMQ_URL=amqp://censudx:censudx_password@localhost:5672/censudx_vhost
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF
fi

echo "✅ Development environment ready!"
echo ""
echo "🚀 To start development:"
echo "   source venv/bin/activate"
echo "   docker-compose up -d          # Start infrastructure"
echo "   cd gateway && python main.py  # Start gateway"
echo ""
echo "🔗 Access points:"
echo "   - Gateway: http://localhost:8000"
echo "   - Swagger: http://localhost:8000/docs"
echo "   - Nginx: http://localhost"