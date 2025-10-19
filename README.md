# Censudx Microservices API Gateway - Taller 2

[![CI/CD](https://github.com/och1ai/censudx-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/och1ai/censudx-api-gateway/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/och1ai/censudx-api-gateway)
[![Nginx](https://img.shields.io/badge/nginx-1.21-green)](https://github.com/och1ai/censudx-api-gateway)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)](https://github.com/och1ai/censudx-api-gateway)
[![Microservices](https://img.shields.io/badge/microservices-ready-purple)](https://github.com/och1ai/censudx-api-gateway)
[![Academic](https://img.shields.io/badge/academic-taller2-orange)](https://github.com/och1ai/censudx-api-gateway)

> 🎓 **API Gateway Académico** - Proyecto para Taller 2 de Arquitectura de Sistemas UCN. Gateway para arquitectura de microservicios distribuida donde cada estudiante implementa un servicio específico.

## 🏗️ Arquitectura del Proyecto Académico

### Distribución por Estudiante (Taller 2)
```
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx API Gateway                          │
│              (Load Balancer + HTTP/gRPC Router)                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                 FastAPI Gateway Service                        │
│           (Shared - All team members collaborate)              │
│  • Authentication & Authorization (JWT)                        │
│  • Request Routing & Protocol Translation                      │
│  • Rate Limiting & Security Headers                            │
│  • Service Discovery & Health Checks                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──┐    ┌──────▼──────┐    ┌───▼─────────┐
│ Student  │    │ RabbitMQ    │    │   Redis     │
│Services  │    │(Async Msg)  │    │ (Caching)   │
│(Indiv.)  │    │   Queue     │    │             │
└──────────┘    └─────────────┘    └─────────────┘
```

### Servicios por Estudiante

| Servicio | Responsable | Base de Datos | Puerto | Status | Endpoints Key |
|----------|------------|---------------|--------|--------|--------------|
| **Clients Service** | Estudiante A | PostgreSQL (Render) | 8002 | 🔄 Desarrollo | POST/GET/PATCH/DELETE `/clients` |
| **Products Service** | Estudiante B | MongoDB (Atlas) | 8005 | 🔄 Desarrollo | POST/GET/PATCH/DELETE `/products` |
| **Inventory Service** | Estudiante C | PostgreSQL (Supabase) | 8001 | ✅ Implementado | GET/PATCH `/inventory` |
| **Orders Service** | Estudiante D | MySQL (Railway) | 8004 | 🔄 Desarrollo | POST/GET/PUT/PATCH `/orders` |

## 🎓 Especificaciones Académicas - Taller 2

### Contexto del Proyecto
**Censudx** es una empresa retail latinoamericana que migra de un sistema monolítico a microservicios. Este gateway sirve como punto único de entrada para coordinar la comunicación entre servicios distribuidos.

### Objetivos de Aprendizaje
- ✅ **Arquitectura de Microservicios**: Implementación práctica de patrones de diseño distribuido
- ✅ **API Gateway Pattern**: Centralización de cross-cutting concerns (auth, routing, rate limiting)
- ✅ **Protocolo HTTP vs gRPC**: Comunicación síncrona entre servicios
- ✅ **Event-Driven Architecture**: Comunicación asíncrona con RabbitMQ
- ✅ **Service Discovery**: Registro y descubrimiento automático de servicios

### Tecnologías por Servicio (Según Enunciado)

| Servicio | Tecnología Requerida | Base de Datos | Proveedor Cloud | Estudiante |
|----------|---------------------|---------------|----------------|------------|
| **Clients** | Libre elección | PostgreSQL | Render (Gratis) | Responsable A |
| **Products** | Libre elección | MongoDB | MongoDB Atlas (Gratis) | Responsable B |
| **Inventory** | Libre elección | PostgreSQL | Supabase (Gratis) | Responsable C |
| **Orders** | Libre elección | MySQL | Railway (Gratis) | Responsable D |
| **API Gateway** | FastAPI + Nginx | Sin DB propia | Colaborativo | Todo el equipo |

### Comunicación Inter-Servicios

#### Síncrona (HTTP/gRPC)
- **API Gateway ↔ Auth Service**: HTTP (autenticación de usuarios)
- **API Gateway ↔ Otros Servicios**: gRPC (mayor performance)
- **Validaciones en tiempo real**: Para operaciones críticas

#### Asíncrona (RabbitMQ)
- **Order Created** → Inventory Service (descontar stock)
- **Low Stock Alert** → Notification Service (alertas administrativas)
- **Order Status Change** → Email Service (notificar cliente)

### Endpoints Académicos por Servicio

Según el enunciado del taller, cada servicio debe exponer:

#### Clients Service (estudiante responsable)
```http
POST   /api/v1/clients          # Crear usuario
GET    /api/v1/clients          # Listar usuarios
GET    /api/v1/clients/{id}     # Obtener usuario
PATCH  /api/v1/clients/{id}     # Editar usuario
DELETE /api/v1/clients/{id}     # Soft delete
```

#### Products Service (estudiante responsable)
```http
POST   /api/v1/products         # Crear producto (admin)
GET    /api/v1/products         # Catálogo público
GET    /api/v1/products/{id}    # Detalle producto
PATCH  /api/v1/products/{id}    # Editar producto (admin)
DELETE /api/v1/products/{id}    # Soft delete (admin)
```

#### Inventory Service (implementado)
```http
GET    /api/v1/inventory        # Stock de productos (admin)
GET    /api/v1/inventory/{id}   # Stock específico
PATCH  /api/v1/inventory/{id}   # Actualizar stock
```

#### Orders Service (estudiante responsable)
```http
POST   /api/v1/orders           # Crear pedido
GET    /api/v1/orders           # Historial pedidos
GET    /api/v1/orders/{id}      # Detalle pedido
PUT    /api/v1/orders/{id}/status # Actualizar estado
PATCH  /api/v1/orders/{id}      # Cancelar pedido
```

### Validaciones Requeridas

#### Autenticación & Autorización
- **JWT Tokens**: Generados por Auth Service, validados por Gateway
- **Role-based Access**: Admin vs User permissions
- **Protected Routes**: Inventory, Orders, User management

#### Validación de Datos
- **Email format**: `@censudex.cl` para usuarios
- **Password strength**: 8+ chars, mayúscula, minúscula, número, especial
- **Chilean phone**: Formato de teléfono chileno válido
- **Age validation**: Mayor de 18 años
- **Stock validation**: Números positivos, disponibilidad

### Criterios de Evaluación

#### Funcionalidad (40%)
- ✅ CRUD completo en servicio asignado
- ✅ Validaciones de datos implementadas
- ✅ Integración con base de datos cloud
- ✅ Manejo de errores y excepciones

#### Arquitectura (30%)
- ✅ Patrón de microservicios implementado
- ✅ Comunicación HTTP/gRPC funcional
- ✅ Event-driven patterns con RabbitMQ
- ✅ Service discovery y health checks

#### Código y Documentación (20%)
- ✅ Conventional Commits
- ✅ Código comentado y limpio
- ✅ README con instrucciones de deploy
- ✅ Colección Postman con endpoints

#### Deploy y Testing (10%)
- ✅ Deploy en cloud provider asignado
- ✅ Video demostrativo del sistema
- ✅ Integración con el gateway común

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

## 🤝 Guía de Desarrollo Académico

### Para Estudiantes - Desarrollo de Servicio Asignado:

1. **Setup inicial del repositorio**:
   ```bash
   git clone <gateway-repo>
   cd censudx-api-gateway
   git checkout -b feature/mi-servicio-asignado
   ```

2. **Crear estructura del servicio**:
   ```bash
   mkdir -p services/mi-servicio
   cd services/mi-servicio
   # Implementar según tecnología elegida
   ```

3. **Configurar integración con Gateway**:
   - Agregar servicio al `docker-compose.yml`
   - Configurar upstream en `nginx/nginx.conf`
   - Registrar en `SERVICE_REGISTRY` del gateway
   - Implementar health check endpoint

4. **Implementar endpoints requeridos**:
   - Seguir especificación del enunciado del taller
   - Implementar validaciones requeridas
   - Configurar base de datos cloud asignada
   - Documentar con Swagger/OpenAPI

5. **Testing e Integración**:
   - Crear colección Postman con todos los endpoints
   - Probar integración con RabbitMQ (eventos asíncronos)
   - Validar autenticación via Gateway
   - Testing de carga con JMeter

6. **Deploy y Documentación**:
   - Deploy en proveedor cloud asignado
   - README con instrucciones paso a paso
   - Video demostrativo del servicio
   - Commits usando Conventional Commits

### Para Colaboración en Gateway (Todo el equipo):

1. **Modificaciones compartidas**:
   ```bash
   git checkout -b feature/gateway-integration-[servicio]
   ```

2. **Áreas de colaboración**:
   - Configuración de routing para nuevos servicios
   - Implementación de eventos RabbitMQ
   - Actualización de documentación
   - Testing de integración E2E

3. **Convenciones del equipo**:
   - Usar `censudx-[nombre-servicio]` para repos individuales
   - Mantener este gateway como punto central
   - Coordinar cambios de esquemas de comunicación
   - Sincronizar deploys para evitar breaking changes

## 🛠️ Comandos Útiles para Desarrollo

### Testing rápido del Gateway
```bash
# Health check del gateway
curl http://localhost/health

# Verificar servicios registrados
curl http://localhost:8000/gateway/services

# Test de autenticación
curl -X POST http://localhost/gateway/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# Validar token
curl -X POST http://localhost:8000/gateway/auth/validate \
  -H "Authorization: Bearer <tu-token>"
```

### Monitoreo de servicios
```bash
# Ver logs del gateway
docker-compose logs -f gateway

# Ver logs de RabbitMQ
docker-compose logs -f rabbitmq

# Estado de contenedores
docker-compose ps

# Restart de un servicio específico
docker-compose restart inventory
```

### Debug y desarrollo
```bash
# Acceder a RabbitMQ Management
open http://localhost:15672
# Usuario: censudx, Password: censudx_password

# Ver métricas de Nginx
curl http://localhost/nginx_status

# Validar configuración de Nginx
docker exec censudx_nginx_gateway nginx -t
```

## 🔗 Repositorios del Proyecto Académico

### Servicios por Estudiante
- **Gateway (Compartido)**: Este repositorio - ✅ Base implementada
- **Inventory Service**: [censudx-inventory](https://github.com/estudiante-c/censudx-inventory) - ✅ Implementado
- **Clients Service**: [censudx-clients](https://github.com/estudiante-a/censudx-clients) - 🔄 Desarrollo
- **Products Service**: [censudx-products](https://github.com/estudiante-b/censudx-products) - 🔄 Desarrollo
- **Orders Service**: [censudx-orders](https://github.com/estudiante-d/censudx-orders) - 🔄 Desarrollo

### Recursos de Apoyo
- **Documentación API**: Disponible en `/docs` una vez corriendo el gateway
- **Colección Postman**: En `/tests/postman/` (cada estudiante debe completar su parte)
- **Ejemplos gRPC**: En `/proto/` para comunicación entre servicios

---

**🎓 Proyecto Académico Taller 2 - Arquitectura de Microservicios UCN** | **Ready for distributed learning** 🚀
# censudx-api-gateway
