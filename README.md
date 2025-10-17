# Censudx Microservices API Gateway

[![CI/CD](https://github.com/och1ai/censudx-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/och1ai/censudx-api-gateway/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/och1ai/censudx-api-gateway)
[![Nginx](https://img.shields.io/badge/nginx-1.21-green)](https://github.com/och1ai/censudx-api-gateway)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)](https://github.com/och1ai/censudx-api-gateway)
[![Microservices](https://img.shields.io/badge/microservices-ready-purple)](https://github.com/och1ai/censudx-api-gateway)

> 🚀 Production-ready API Gateway for Censudx microservices architecture with Nginx load balancing, authentication, and service orchestration.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx API Gateway                   │
│                (Load Balancer + Router)                │
└─────────┬─────────────────────────────────┬─────────────┘
          │                                 │
┌─────────▼────────┐                ┌──────▼──────────────┐
│  Gateway Service │                │  Message Queues     │
│  (FastAPI)       │                │  (RabbitMQ)         │
│  - Authentication│                │  - Event Bus        │
│  - Rate Limiting │                │  - Inter-service    │
│  - Request Router│                │    Communication    │
└─────────┬────────┘                └─────────────────────┘
          │
    ┌─────┼─────┐
    │     │     │
┌───▼──┐ ┌▼───┐ ┌▼────────┐
│Auth  │ │Inv.│ │Future   │
│Svc   │ │Svc │ │Services │
│(Stub)│ │(✅)│ │(Stubs)  │
└──────┘ └────┘ └─────────┘
```

## 📋 Services Status

| Service | Status | Implementation | Port | Endpoints |
|---------|--------|---------------|------|-----------|
| **API Gateway** | ✅ Implemented | Nginx + FastAPI | 80/443 | Route all requests |
| **Inventory Service** | ✅ Production Ready | Full Implementation | 8001 | CRUD + Stock Management |
| **Auth Service** | 🟡 Stub | Authentication Stub | 8002 | Login, Validate, Register |
| **User Service** | 🟡 Stub | User Management Stub | 8003 | Profile, Preferences |
| **Order Service** | 🟡 Stub | Order Processing Stub | 8004 | Create, Track, Update |
| **Product Service** | 🟡 Stub | Product Catalog Stub | 8005 | Catalog, Search, Details |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- curl (for testing)

### 1-Command Setup
```bash
git clone <repository-url>
cd censudx-api-gateway
docker-compose up -d
```

### Access Points
- **API Gateway**: http://localhost (Nginx)
- **Gateway Service**: http://localhost:8000 (FastAPI)
- **Swagger Docs**: http://localhost:8000/docs
- **Inventory Service**: http://localhost:8001
- **RabbitMQ Management**: http://localhost:15672

## 🎯 Key Features

### 🔒 **Authentication & Security**
- JWT-based authentication with configurable expiration
- Rate limiting per IP and per user
- CORS configuration for frontend integration
- Security headers and HTTPS redirect

### 🔄 **Load Balancing & Routing**
- Nginx-based reverse proxy with health checks
- Automatic failover and service discovery
- Request routing based on path patterns
- WebSocket support for real-time features

### 📊 **Service Integration**
- **Inventory Service**: Full production implementation
- **Authentication Stub**: Simulates user authentication
- **Extensible Architecture**: Easy to add new services

### 🐰 **Event-Driven Communication**
- RabbitMQ message broker for inter-service communication
- Event sourcing for audit trails
- Asynchronous processing capabilities

## 🔧 Development Guide

### Adding New Services

1. **Create service directory**:
   ```bash
   mkdir -p services/your-service
   cd services/your-service
   ```

2. **Implement FastAPI service**:
   ```python
   from fastapi import FastAPI
   
   app = FastAPI(title="Your Service")
   
   @app.get("/health")
   async def health():
       return {"status": "healthy"}
   ```

3. **Update docker-compose.yml**:
   ```yaml
   your-service:
     build: ./services/your-service
     ports:
       - "8006:8000"
     networks:
       - censudx-network
   ```

4. **Add to Nginx routing**:
   ```nginx
   location /api/v1/your-service/ {
       proxy_pass http://your-service:8000/;
   }
   ```

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/service-name`: Individual service development
- `feature/gateway-*`: Gateway improvements

## 📁 Project Structure

```
censudx-api-gateway/
├── gateway/                    # API Gateway Service
│   ├── main.py                # FastAPI gateway application
│   ├── auth/                  # Authentication logic
│   ├── middleware/            # Custom middleware
│   └── routes/                # Route definitions
├── services/                  # Microservices
│   ├── inventory/             # ✅ Production Ready
│   ├── auth-stub/             # 🟡 Authentication Stub
│   ├── user-stub/             # 🟡 User Management Stub
│   └── order-stub/            # 🟡 Order Processing Stub
├── nginx/                     # Nginx configuration
│   ├── nginx.conf            # Main configuration
│   ├── sites/                # Site-specific configs
│   └── ssl/                  # SSL certificates
├── tests/                     # Comprehensive test suite
│   ├── gateway/              # Gateway tests
│   ├── integration/          # Inter-service tests
│   └── e2e/                  # End-to-end tests
├── docker-compose.yml        # Full stack orchestration
├── docker-compose.dev.yml    # Development environment
└── scripts/                  # Utility scripts
    ├── setup-dev.sh          # Development setup
    ├── run-tests.sh          # Test runner
    └── deploy.sh             # Deployment script
```

## 🧪 Testing

### Run All Tests
```bash
./scripts/run-tests.sh
```

### Test Categories
- **Unit Tests**: Individual service logic
- **Integration Tests**: Service-to-service communication
- **E2E Tests**: Full user workflows through gateway
- **Load Tests**: Performance and scalability

### Example Test Commands
```bash
# Test gateway routing
curl -X GET http://localhost/api/v1/inventory/health

# Test authentication flow
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Test inventory operations through gateway
curl -X POST http://localhost/api/v1/inventory/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"product_id": "item001", "quantity": 100}'
```

## 🐳 Docker & Deployment

### Development Environment
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production Environment
```bash
docker-compose -f docker-compose.yml up -d
```

### Service Scaling
```bash
docker-compose up -d --scale inventory-service=3
```

## 🔄 CI/CD Pipeline

Automated pipeline includes:
1. **Code Quality**: Linting, formatting, security scans
2. **Unit Tests**: All services tested independently
3. **Integration Tests**: Service communication validation
4. **E2E Tests**: Full workflow testing
5. **Docker Build**: Multi-service container building
6. **Deployment**: Automated staging and production deployment

## 🤝 Contributing

### For Service Development:
1. Create feature branch: `git checkout -b feature/your-service`
2. Implement your service in `services/your-service/`
3. Add comprehensive tests
4. Update documentation
5. Create pull request

### For Gateway Improvements:
1. Create feature branch: `git checkout -b feature/gateway-improvement`
2. Modify gateway components
3. Ensure backward compatibility
4. Add tests for new functionality
5. Create pull request

## 🔗 Related Repositories

- **Inventory Service**: [censudx-inventory-service](https://github.com/och1ai/censudx-inventory-service) - ✅ Production Ready
- **Frontend Application**: [censudx-frontend](https://github.com/och1ai/censudx-frontend) - 🟡 Coming Soon
- **DevOps Configuration**: [censudx-infrastructure](https://github.com/och1ai/censudx-infrastructure) - 🟡 Coming Soon

---

**Built for scalable microservices architecture** | **Ready for team development** 🚀