#!/bin/bash

################################################################################
# Censudex API Gateway - Complete E2E Flow Test Script
# Tests: Authentication -> Inventory -> Clients
# Author: Censudex Team
# Date: 2025-11-16
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Sleep time between tests (seconds)
SLEEP_TIME=1

################################################################################
# Dependencies Check
################################################################################

check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}✗ Missing required dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Please install them with:${NC}"
        echo -e "  sudo apt-get install ${missing_deps[*]}  # Debian/Ubuntu"
        echo -e "  sudo yum install ${missing_deps[*]}      # RHEL/CentOS"
        echo -e "  brew install ${missing_deps[*]}          # macOS"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All dependencies are installed (curl, jq)${NC}\n"
}

# Configuration
GATEWAY_URL="http://localhost:8000"
ADMIN_USERNAME="adminCensudex"
ADMIN_PASSWORD="Admin1234!"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
    sleep $SLEEP_TIME
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
    sleep $SLEEP_TIME
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to make API calls with better error handling
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    
    if [ -n "$token" ]; then
        if [ -n "$data" ]; then
            curl -s -X "$method" "$GATEWAY_URL$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data"
        else
            curl -s -X "$method" "$GATEWAY_URL$endpoint" \
                -H "Authorization: Bearer $token"
        fi
    else
        if [ -n "$data" ]; then
            curl -s -X "$method" "$GATEWAY_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data"
        else
            curl -s -X "$method" "$GATEWAY_URL$endpoint"
        fi
    fi
}

################################################################################
# Test Functions
################################################################################

test_gateway_health() {
    print_header "1. GATEWAY HEALTH CHECK"
    print_test "Checking gateway health endpoint"
    
    echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/gateway/health${NC}"
    response=$(api_call "GET" "/gateway/health")
    status=$(echo "$response" | jq -r '.status // empty')
    
    if [ "$status" == "healthy" ]; then
        print_success "Gateway is healthy"
        echo "$response" | jq '.'
    else
        print_error "Gateway health check failed"
        echo "$response"
    fi
    echo ""
}

test_authentication() {
    print_header "2. AUTHENTICATION FLOW"
    
    # Test 2.1: Successful login
    print_test "Login with admin credentials"
    echo -e "${BLUE}→ Executing: POST $GATEWAY_URL/api/login${NC}"
    response=$(api_call "POST" "/api/login" "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}")
    
    TOKEN=$(echo "$response" | jq -r '.token // empty')
    
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        print_success "Authentication successful - Token obtained"
        echo "Token (first 50 chars): ${TOKEN:0:50}..."
    else
        print_error "Authentication failed"
        echo "$response" | jq '.'
        exit 1
    fi
    echo ""
    
    # Test 2.2: Invalid credentials
    print_test "Login with invalid credentials (should fail)"
    echo -e "${BLUE}→ Executing: POST $GATEWAY_URL/api/login (invalid credentials)${NC}"
    response=$(api_call "POST" "/api/login" "{\"username\":\"invaliduser\",\"password\":\"wrongpass\"}")
    
    error=$(echo "$response" | jq -r '.error // .message // .detail // empty')
    if [ -n "$error" ] && [ "$error" != "null" ]; then
        print_success "Invalid credentials correctly rejected"
    else
        print_error "Invalid credentials should have been rejected"
    fi
    echo ""
}

test_inventory() {
    print_header "3. INVENTORY OPERATIONS"
    
    # Test 3.1: List inventory
    print_test "List all inventory items"
    echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/api/v1/inventory/?limit=5&offset=0${NC}"
    response=$(api_call "GET" "/api/v1/inventory/?limit=5&offset=0" "" "$TOKEN")
    
    count=$(echo "$response" | jq '. | length')
    if [ "$count" -ge 0 ]; then
        print_success "Listed $count inventory items"
        echo "$response" | jq '.[0:2]'  # Show first 2 items
    else
        print_error "Failed to list inventory"
        echo "$response"
    fi
    echo ""
    
    # Test 3.2: Create inventory item
    print_test "Create new inventory item"
    TIMESTAMP=$(date +%s)
    PRODUCT_ID="TEST_PROD_${TIMESTAMP}"
    
    create_payload="{\"product_id\":\"$PRODUCT_ID\",\"quantity\":100,\"location\":\"test_warehouse\",\"reserved_quantity\":0}"
    echo -e "${BLUE}→ Executing: POST $GATEWAY_URL/api/v1/inventory/${NC}"
    response=$(api_call "POST" "/api/v1/inventory/" "$create_payload" "$TOKEN")
    
    ITEM_ID=$(echo "$response" | jq -r '.id // empty')
    if [ -n "$ITEM_ID" ] && [ "$ITEM_ID" != "null" ]; then
        print_success "Created inventory item with ID: $ITEM_ID"
        echo "$response" | jq '.'
    else
        print_error "Failed to create inventory item"
        echo "$response"
        ITEM_ID=""
    fi
    echo ""
    
    # Test 3.3: Get specific inventory item
    if [ -n "$ITEM_ID" ]; then
        print_test "Get inventory item by ID: $ITEM_ID"
        echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/api/v1/inventory/$ITEM_ID${NC}"
        response=$(api_call "GET" "/api/v1/inventory/$ITEM_ID" "" "$TOKEN")
        
        retrieved_id=$(echo "$response" | jq -r '.id // empty')
        if [ "$retrieved_id" == "$ITEM_ID" ]; then
            print_success "Retrieved inventory item successfully"
            echo "$response" | jq '.'
        else
            print_error "Failed to retrieve inventory item"
        fi
        echo ""
    fi
    
    # Test 3.4: Update inventory item
    if [ -n "$ITEM_ID" ]; then
        print_test "Update inventory item quantity"
        update_payload="{\"quantity\":150,\"location\":\"updated_warehouse\"}"
        echo -e "${BLUE}→ Executing: PUT $GATEWAY_URL/api/v1/inventory/$ITEM_ID${NC}"
        response=$(api_call "PUT" "/api/v1/inventory/$ITEM_ID" "$update_payload" "$TOKEN")
        
        new_quantity=$(echo "$response" | jq -r '.quantity // empty')
        if [ "$new_quantity" == "150" ]; then
            print_success "Updated inventory item - New quantity: $new_quantity"
            echo "$response" | jq '.'
        else
            print_error "Failed to update inventory item"
        fi
        echo ""
    fi
    
    # Test 3.5: Check stock availability
    print_test "Check stock availability"
    stock_check_payload="{\"product_id\":\"$PRODUCT_ID\",\"requested_quantity\":10}"
    echo -e "${BLUE}→ Executing: POST $GATEWAY_URL/api/v1/inventory/check-stock${NC}"
    response=$(api_call "POST" "/api/v1/inventory/check-stock" "$stock_check_payload" "$TOKEN")
    
    available=$(echo "$response" | jq -r '.available // empty')
    if [ "$available" == "true" ] || [ "$available" == "false" ]; then
        print_success "Stock check completed - Available: $available"
        echo "$response" | jq '.'
    else
        print_error "Failed to check stock"
    fi
    echo ""
    
    # Test 3.6: Delete inventory item
    if [ -n "$ITEM_ID" ]; then
        print_test "Delete inventory item"
        echo -e "${BLUE}→ Executing: DELETE $GATEWAY_URL/api/v1/inventory/$ITEM_ID${NC}"
        response=$(api_call "DELETE" "/api/v1/inventory/$ITEM_ID" "" "$TOKEN")
        
        message=$(echo "$response" | jq -r '.message // empty')
        if [[ "$message" == *"deleted"* ]]; then
            print_success "Deleted inventory item successfully"
        else
            print_error "Failed to delete inventory item"
        fi
        echo ""
    fi
}

test_clients() {
    print_header "4. CLIENTS OPERATIONS"
    
    # Test 4.1: List clients
    print_test "List all clients"
    echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/api/clients${NC}"
    response=$(api_call "GET" "/api/clients" "" "$TOKEN")
    
    clients=$(echo "$response" | jq -r '.clients | length')
    if [ "$clients" -gt 0 ]; then
        print_success "Listed $clients clients"
        echo "$response" | jq '.clients[0:2]'  # Show first 2 clients
    else
        print_error "Failed to list clients"
    fi
    echo ""
    
    # Test 4.2: Create client
    print_test "Create new client"
    TIMESTAMP=$(date +%s)
    CLIENT_USERNAME="testuser${TIMESTAMP}"
    CLIENT_EMAIL="test${TIMESTAMP}@censudex.cl"
    
    create_client_payload="{
        \"names\":\"Test\",
        \"lastnames\":\"Usuario\",
        \"email\":\"$CLIENT_EMAIL\",
        \"username\":\"$CLIENT_USERNAME\",
        \"birthdate\":\"1990-01-01\",
        \"address\":\"Test Address 123\",
        \"phonenumber\":\"+56912345678\",
        \"password\":\"Test123!\"
    }"
    
    echo -e "${BLUE}→ Executing: POST $GATEWAY_URL/api/clients${NC}"
    response=$(api_call "POST" "/api/clients" "$create_client_payload" "$TOKEN")
    
    message=$(echo "$response" | jq -r '.message // empty')
    if [[ "$message" == *"creado"* ]] || [[ "$message" == *"created"* ]]; then
        print_success "Created client: $CLIENT_USERNAME"
        
        # Get the client ID
        sleep 1  # Give it a moment
        list_response=$(api_call "GET" "/api/clients?usernamefilter=$CLIENT_USERNAME" "" "$TOKEN")
        CLIENT_ID=$(echo "$list_response" | jq -r '.clients[0].id // empty')
        
        if [ -n "$CLIENT_ID" ] && [ "$CLIENT_ID" != "null" ]; then
            print_info "Client ID: $CLIENT_ID"
        fi
    else
        print_error "Failed to create client"
        CLIENT_ID=""
    fi
    echo ""
    
    # Test 4.3: Get specific client
    if [ -n "$CLIENT_ID" ]; then
        print_test "Get client by ID: $CLIENT_ID"
        echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/api/clients/$CLIENT_ID${NC}"
        response=$(api_call "GET" "/api/clients/$CLIENT_ID" "" "$TOKEN")
        
        username=$(echo "$response" | jq -r '.client.username // empty')
        if [ "$username" == "$CLIENT_USERNAME" ]; then
            print_success "Retrieved client successfully"
            echo "$response" | jq '.client'
        else
            print_error "Failed to retrieve client"
        fi
        echo ""
    fi
    
    # Test 4.4: Update client
    if [ -n "$CLIENT_ID" ]; then
        print_test "Update client information"
        update_client_payload="{
            \"names\":\"Test Updated\",
            \"lastnames\":\"Usuario Modificado\",
            \"email\":\"$CLIENT_EMAIL\",
            \"username\":\"$CLIENT_USERNAME\",
            \"birthdate\":\"1990-01-01\",
            \"address\":\"Updated Address 456\",
            \"phonenumber\":\"+56999999999\"
        }"
        
        echo -e "${BLUE}→ Executing: PATCH $GATEWAY_URL/api/clients/$CLIENT_ID${NC}"
        response=$(api_call "PATCH" "/api/clients/$CLIENT_ID" "$update_client_payload" "$TOKEN")
        
        message=$(echo "$response" | jq -r '.message // empty')
        if [[ "$message" == *"actualizado"* ]] || [[ "$message" == *"updated"* ]]; then
            print_success "Updated client successfully"
        else
            print_error "Failed to update client"
        fi
        echo ""
    fi
    
    # Test 4.5: Delete client (requires Admin role)
    if [ -n "$CLIENT_ID" ]; then
        print_test "Delete client (Admin only)"
        echo -e "${BLUE}→ Executing: DELETE $GATEWAY_URL/api/clients/$CLIENT_ID${NC}"
        response=$(api_call "DELETE" "/api/clients/$CLIENT_ID" "" "$TOKEN")
        
        message=$(echo "$response" | jq -r '.message // empty')
        if [[ "$message" == *"eliminado"* ]] || [[ "$message" == *"deleted"* ]]; then
            print_success "Deleted client successfully (Admin authorization verified)"
        else
            print_error "Failed to delete client"
        fi
        echo ""
    fi
}

test_authorization() {
    print_header "5. AUTHORIZATION TESTS"
    
    # Test 5.1: Access without token
    print_test "Access inventory without authentication (should fail)"
    echo -e "${BLUE}→ Executing: GET $GATEWAY_URL/api/v1/inventory/ (without auth token)${NC}"
    response=$(api_call "GET" "/api/v1/inventory/" "")
    
    # Should get 401 or 403
    error=$(echo "$response" | jq -r '.error // .detail // empty')
    if [ -n "$error" ] && [ "$error" != "null" ]; then
        print_success "Unauthorized access correctly blocked: $error"
    else
        print_error "Should have blocked unauthorized access"
        echo "$response" | jq '.'
    fi
    echo ""
}

################################################################################
# Main Execution
################################################################################

print_header "CENSUDEX API GATEWAY - COMPLETE FLOW TEST"
print_info "Testing against: $GATEWAY_URL"
print_info "Admin User: $ADMIN_USERNAME"
echo ""

# Check dependencies
check_dependencies

# Run all tests
test_gateway_health
test_authentication
test_inventory
test_clients
test_authorization

################################################################################
# Summary
################################################################################

print_header "TEST SUMMARY"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
