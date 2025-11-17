#!/bin/bash

###############################################################################
# CENSUDEX - Complete System Startup Script
# Starts all services including Orders service integration
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
TALLER2_DIR="/home/ochiai/Desktop/taller2"
GATEWAY_DIR="$TALLER2_DIR/censudex-api-gateway"
ORDERS_DIR="$TALLER2_DIR/censudex-orders-service"

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_header "CENSUDEX - SYSTEM STARTUP"

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

if ! command -v socat &> /dev/null; then
    print_error "socat not found. Please install socat (sudo apt install socat)."
    exit 1
fi

if [ ! -f "$HOME/.dotnet/dotnet" ]; then
    print_error ".NET 9.0 SDK not found in $HOME/.dotnet"
    print_info "Please run: wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 9.0.100 --install-dir $HOME/.dotnet"
    exit 1
fi

print_success "All prerequisites found"

# Step 1: Configure RabbitMQ (if needed)
print_header "STEP 1: Configure RabbitMQ"

# Check if RabbitMQ container exists and is running
if docker ps -q -f name=censudx_rabbitmq > /dev/null 2>&1; then
    print_info "Configuring RabbitMQ password..."
    docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password 2>/dev/null || true
    print_success "RabbitMQ configured"
else
    print_info "RabbitMQ not running yet, will configure after Docker services start"
fi

# Step 2: Start Docker services
print_header "STEP 2: Start Docker Services"

cd "$TALLER2_DIR"
print_info "Starting services with docker-compose..."
docker-compose -f docker-compose.prod.yml up -d

print_info "Waiting for services to be healthy (30 seconds)..."
sleep 30

# Configure RabbitMQ if we skipped it earlier
if ! docker exec censudx_rabbitmq rabbitmqctl authenticate_user censudx censudex_password &>/dev/null; then
    print_info "Configuring RabbitMQ password..."
    docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password 2>/dev/null || true
fi

print_success "Docker services started"

# Show running containers
print_info "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "censudex|censudx|NAMES"

# Step 3: Start port forwarding
print_header "STEP 3: Configure Port Forwarding"

# Kill existing socat processes on port 5207
pkill -f "socat.*5207.*5206" 2>/dev/null || true
sleep 2

print_info "Starting port forwarding: 0.0.0.0:5207 → 127.0.0.1:5206"
socat TCP4-LISTEN:5207,fork,reuseaddr TCP4:127.0.0.1:5206 > /dev/null 2>&1 &
SOCAT_PID=$!

sleep 2

if ss -tlnp 2>/dev/null | grep -q 5207; then
    print_success "Port forwarding started (PID: $SOCAT_PID)"
else
    print_error "Port forwarding failed to start"
    exit 1
fi

# Step 4: Start Orders service
print_header "STEP 4: Start Orders Service (.NET 9.0)"

# Kill existing Orders service
pkill -f "dotnet run.*OrderService" 2>/dev/null || true
sleep 2

cd "$ORDERS_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found in $ORDERS_DIR"
    exit 1
fi

print_info "Starting Orders service..."
ASPNETCORE_URLS="http://localhost:5206" \
ASPNETCORE_ENVIRONMENT=Development \
$HOME/.dotnet/dotnet run --project OrderService.csproj --no-launch-profile > orders.log 2>&1 &
ORDERS_PID=$!

print_info "Waiting for Orders service to start (15 seconds)..."
sleep 15

# Check if Orders service is running
if ps -p $ORDERS_PID > /dev/null 2>&1; then
    print_success "Orders service started (PID: $ORDERS_PID)"
    
    # Check for errors in log
    if grep -qi "error\|exception\|fail" orders.log 2>/dev/null; then
        print_error "Errors detected in orders.log:"
        tail -20 orders.log
    else
        print_success "Orders service running without errors"
    fi
else
    print_error "Orders service failed to start"
    print_info "Last 30 lines of orders.log:"
    tail -30 orders.log
    exit 1
fi

# Step 5: Verify all services
print_header "STEP 5: Service Verification"

print_info "Checking service ports..."

check_port() {
    local port=$1
    local service=$2
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        print_success "$service listening on port $port"
        return 0
    else
        print_error "$service NOT listening on port $port"
        return 1
    fi
}

check_port 8000 "Gateway"
check_port 5001 "Auth Service (Docker)"
check_port 5002 "Clients Service (Docker)"
check_port 50051 "Inventory Service (Docker)"
check_port 5206 "Orders Service (Host)"
check_port 5207 "Port Forwarding (socat)"
check_port 5432 "PostgreSQL (Docker)"
check_port 3307 "MySQL (Docker)"
check_port 5672 "RabbitMQ (Docker)"
check_port 6379 "Redis (Docker)"

# Step 6: Test gateway health
print_header "STEP 6: Gateway Health Check"

print_info "Checking gateway health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/gateway/health)

if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    print_success "Gateway is healthy"
    
    # Show service statuses
    echo -e "\n${BLUE}Service Status:${NC}"
    echo "$HEALTH_RESPONSE" | jq -r '.services | to_entries[] | "\(.key): \(.value.status)"' | while read line; do
        if echo "$line" | grep -q "healthy"; then
            echo -e "${GREEN}✓${NC} $line"
        else
            echo -e "${YELLOW}⚠${NC} $line"
        fi
    done
else
    print_error "Gateway health check failed"
    echo "$HEALTH_RESPONSE" | jq '.'
fi

# Final summary
print_header "STARTUP COMPLETE"

print_success "All services are running!"
echo ""
print_info "Service URLs:"
echo "  Gateway:    http://localhost:8000"
echo "  Nginx:      http://localhost:80"
echo "  RabbitMQ:   http://localhost:15672 (guest/guest)"
echo ""
print_info "Test the system:"
echo "  cd $GATEWAY_DIR && ./inventory_tests.sh"
echo ""
print_info "View logs:"
echo "  Gateway:    docker logs -f censudex_gateway"
echo "  Orders:     tail -f $ORDERS_DIR/orders.log"
echo "  All Docker: docker-compose -f $TALLER2_DIR/docker-compose.prod.yml logs -f"
echo ""
print_info "Process IDs:"
echo "  socat:      $SOCAT_PID"
echo "  Orders:     $ORDERS_PID"
echo ""
print_info "To stop all services:"
echo "  cd $TALLER2_DIR && docker-compose -f docker-compose.prod.yml down"
echo "  kill $SOCAT_PID $ORDERS_PID"
echo ""
