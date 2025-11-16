# Censudex Microservices API Gateway

[![CI/CD](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/nico-alvz/censudex-api-gateway)
[![gRPC](https://img.shields.io/badge/gRPC-1.60.0-orange)](https://grpc.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.11-green)](https://fastapi.tiangolo.com)
[![Microservices](https://img.shields.io/badge/microservices-gRPC%20%2B%20HTTP-purple)](https://github.com/nico-alvz/censudex-api-gateway)

> 🚀 **Censudex API Gateway** – Implementación de un gateway para una arquitectura de microservicios distribuida con comunicación gRPC y RabbitMQ. Proyecto desarrollado como parte de un taller de arquitectura de sistemas.

---

## 🏗️ Arquitectura del Proyecto

### Descripción General
```
┌────────────────────────────────────────────────────────────────┐
│                       Nginx (Reverse Proxy)                    │
│              Puerto 80/443 - Load Balancer                     │
└──────────────────────┬─────────────────────────────────────────┘
                       │ HTTP/gRPC
┌──────────────────────▼─────────────────────────────────────────┐
│              FastAPI Gateway Service (Puerto 8000)             │
│           Punto central de comunicación y ruteo                │
│  • Autenticación & Autorización (JWT)                          │
│  • Traducción de protocolos HTTP ↔ gRPC                        │
│  • Rate Limiting & Security Headers                            │
│  • Health Checks & Service Discovery                           │
│  • Middleware: Request ID, Rate Limiting                       │
└────────┬──────────────┬──────────────┬────────────┬────────────┘
         │              │              │            │
    gRPC │          gRPC │         HTTP │     RabbitMQ
         │              │              │     Redis
         ▼              ▼              ▼     ▼
   ┌─────────────┐ ┌──────────────┐ ┌──────────┐
   │Auth Service │ │Clients Svc   │ │Inventory │
   │(C#, :5001)  │ │(C#, :5002)   │ │(Py, :8001)
   │PostgreSQL   │ │PostgreSQL    │ │PostgreSQL│
   └─────────────┘ └──────────────┘ └──────────┘
         │              │                    │
         └──────────────┼────────────────────┘
                        │
              ┌─────────▼────────────┐
              │  RabbitMQ (Puerto 5672)
              │  - Async Messaging
              │  - Service Decoupling
              │  - Event Notifications
              └──────────────────────┘
```

---

## 🧩 Descripción del Proyecto

**Censudex** es una empresa del rubro retail que está migrando de un sistema monolítico a una arquitectura basada en microservicios.  
El **API Gateway** actúa como punto único de entrada, gestionando autenticación, ruteo, balanceo de carga y comunicación entre servicios distribuidos mediante:

- **gRPC** para comunicación síncrona de alto rendimiento entre servicios
- **HTTP/REST** para servicios heredados y clientes externos
- **RabbitMQ** para comunicación asíncrona y desacoplamiento

### Objetivos del Proyecto
- ✅ Implementar una **arquitectura de microservicios** modular, escalable y performante  
- ✅ Centralizar autenticación, ruteo y seguridad mediante **API Gateway Pattern**  
- ✅ Soportar **comunicación síncrona (gRPC)** y **asíncrona (RabbitMQ)**  
- ✅ Facilitar el **descubrimiento, monitoreo y health checks de servicios**  
- ✅ Proporcionar **aislamiento** entre servicios independientes  

---

## 🧱 Servicios Disponibles

| Servicio | Responsable | Protocolo | Base de Datos | Puerto | Estado | Endpoints |
|----------|-------------|-----------|---------------|--------|---------|-----------|
| **Auth Service** | Alberto Lyons | gRPC | PostgreSQL (JWT) | 5001 | ✅ Operativo | gRPC methods (via gateway) |
| **Clients Service** | Alberto Lyons | gRPC | PostgreSQL | 5002 | ✅ Operativo | `/api/clients` (via gateway) |
| **Inventory Service** | Developer C | gRPC + HTTP | PostgreSQL (Supabase) | 8001/50051 | ✅ Operativo | `/api/v1/inventory` |
| **Orders Service** | Developer D | HTTP | MySQL (Railway) | 5206 | ✅ Operativo | `/api/orders` |
| **Products Service** | Developer B | HTTP | MongoDB (Atlas) | 8005 | 🔄 Desarrollo | `/api/v1/products` |

> **Nota**: Auth y Clients usan **gRPC** para máximo rendimiento en comunicación interna. Inventory Service soporta tanto gRPC (puerto 50051) como HTTP REST (puerto 8001). Orders Service se integra vía HTTP a través del gateway y nginx.

---

## ⚙️ Comunicación entre Servicios

### Síncrona (gRPC/HTTP)

#### **gRPC Services** (Comunicación interna)
- **Gateway ↔ Auth Service** (`:5001`) - Autenticación y validación de tokens
- **Gateway ↔ Clients Service** (`:5002`) - Gestión de clientes con protobuf
- Ventajas: Baja latencia, multiplexing HTTP/2, serialización binaria eficiente
- Implementación: Protocol Buffers (.proto) compilados a Python

#### **HTTP Services** (Comunicación heredada/externa)
- **Gateway ↔ Inventory Service** (`:8001`) - REST API JSON
- **Clientes externos** → Gateway (Puerto 80/443 Nginx)
- Ventajas: Compatibilidad amplia, fácil debugging, estándares REST

### Asíncrona (RabbitMQ)
- **Order Created** → Inventory (descontar stock)
- **Low Stock Alert** → Notifications Service
- **Order Status Change** → Email Service
- Ventajas: Desacoplamiento temporal, escalabilidad, retry logic

---

## 🧾 Endpoints de la Gateway

### Cliente Service (vía gRPC)
```http
GET    /api/clients              # Listar todos los clientes
POST   /api/clients              # Crear nuevo cliente
GET    /api/clients/{id}         # Obtener cliente por ID
PATCH  /api/clients/{id}         # Actualizar cliente
DELETE /api/clients/{id}         # Eliminar cliente
```

**Ejemplo:**
```bash
curl http://localhost/api/clients
# Respuesta: Lista de clientes con datos completos (id, fullname, email, etc.)
```

### Autenticación
```http
POST   /api/auth/login           # Autenticar usuario
POST   /api/auth/logout          # Cerrar sesión
GET    /api/auth/validate        # Validar token JWT
```

### Inventory Service (vía HTTP)
```http
GET    /api/v1/inventory         # Listar inventario
GET    /api/v1/inventory/{id}    # Obtener item específico
PATCH  /api/v1/inventory/{id}    # Actualizar cantidad/estado
```

### Health Checks
```http
GET    /gateway/health           # Estado de gateway y servicios downstream
# Respuesta: Detalle de estado de cada servicio (gRPC/HTTP)
```

---

## 🔒 Seguridad y Validaciones

- **JWT Tokens**: Autenticación basada en tokens con expiración  
- **Role-based Access Control (RBAC)**: Permisos según tipo de usuario  
- **Validaciones de entrada**: Email, password, edad, stock  
- **Rutas protegidas**: Inventario, pedidos, usuarios administrativos  
- **Rate Limiting**: Middleware de limite de requests por IP  
- **Headers de seguridad**: CORS, X-Request-ID, User-Agent validation  
- **Mutual TLS (mTLS)** disponible para gRPC (futuro)

---

## 🐳 Quick Start

### Requisitos Previos
```bash
# Linux/macOS
docker --version        # v20.10+
docker-compose --version # v2.0+
curl                    # para testing
```

### Instalación y Ejecución

**1. Clonar repositorio**
```bash
git clone https://github.com/nico-alvz/censudex-api-gateway.git
cd censudex-api-gateway
```

**2. Ejecutar todos los servicios**
```bash
# Opción A: Producción (recomendado - todas las dependencias)
docker-compose -f docker-compose.prod.yml up -d

# Opción B: Desarrollo (solo gateway local)
docker-compose up -d
```

**3. Verificar estado de servicios**
```bash
curl http://localhost/gateway/health
```

**4. Probar endpoints**
```bash
# Obtener clientes (vía gRPC)
curl http://localhost/api/clients

# Ver documentación interactiva
curl http://localhost:8000/docs

# Acceder a RabbitMQ Management
open http://localhost:15672  # guest:guest
```

### Acceso a Componentes

| Componente | URL | Credenciales |
|-----------|-----|--------------|
| **Nginx Reverse Proxy** | http://localhost:80 | N/A |
| **FastAPI Swagger** | http://localhost:8000/docs | N/A |
| **RabbitMQ Management** | http://localhost:15672 | guest:guest |
| **PostgreSQL** | localhost:5432 | user: inventory_user |
| **Redis CLI** | redis://localhost:6379 | N/A |

---

## 🚀 Características Principales

- ✨ **Comunicación gRPC**: Alta performance entre servicios internos
- 🔐 **Autenticación JWT**: Seguridad en todos los endpoints
- ⚡ **Rate Limiting**: Protección contra abuso
- 📊 **Health Checks**: Monitoreo continuo de servicios (gRPC + HTTP)
- 🔄 **Service Discovery**: DNS-based (Docker network)
- 📨 **Async Messaging**: RabbitMQ para decoupling
- 💾 **Caching**: Redis para datos frecuentes
- 📝 **Logging & Tracing**: Request ID middleware
- 🐳 **Docker Ready**: Compose file con all-in-one setup
- 📱 **Nginx Reverse Proxy**: Load balancing y SSL/TLS

---

## 📁 Estructura del Proyecto

```
censudex-api-gateway/
├── gateway/                    # Servicio FastAPI
│   ├── main.py                 # Punto de entrada, rutas principales
│   ├── Dockerfile              # Imagen Docker con proto compilation
│   ├── requirements.txt         # Dependencias Python
│   ├── auth/
│   │   └── authorize.py         # Middleware JWT
│   ├── middleware/
│   │   ├── rate_limiting.py     # Rate limiter
│   │   └── request_id.py        # Request ID tracking
│   └── routes/
│       ├── auth.py              # Endpoints /api/auth
│       ├── clients.py           # Endpoints /api/clients (gRPC)
│       ├── health.py            # Health checks
│       ├── proxy.py             # Proxy genérico
│       └── Orders.py            # Endpoints /api/orders (HTTP)
│
├── models/                     # Modelos de datos
│   ├── requests.py             # Schemas de entrada
│   ├── responses.py            # Schemas de respuesta
│   └── user.py                 # User model
│
├── pb2/                        # Protocol Buffers compilados
│   ├── order_pb2.py            # Generado desde order.proto
│   ├── order_pb2_grpc.py       # Stubs gRPC generados
│   ├── user_pb2.py             # Generado desde user.proto
│   └── user_pb2_grpc.py        # Stubs gRPC generados
│
├── proto/                      # Definiciones Protocol Buffers
│   ├── order.proto
│   └── user.proto
│
├── services/                   # Servicios auxiliares
│   ├── auth-stub/              # Auth service stub (testing)
│   ├── inventory/              # Inventory service
│   ├── order-stub/             # Order service stub
│   ├── product-stub/           # Product service stub
│   └── user_stub/              # Clients service stub
│
├── nginx/
│   └── nginx.conf              # Configuración reverse proxy
│
├── tests/
│   └── test_gateway.py         # Tests unitarios e integración
│
├── scripts/
│   ├── run-tests.sh            # Script para correr tests
│   └── setup-dev.sh            # Setup de desarrollo
│
├── docker-compose.yml          # Desarrollo (gateway local)
├── docker-compose.prod.yml     # Producción (todos servicios)
└── README.md                   # Este archivo
```

---

## 🧪 Testing

### Tests Unitarios e Integración
```bash
# Ejecutar todos los tests
./scripts/run-tests.sh

# Tests específicos
pytest tests/ -v
pytest tests/test_gateway.py::test_clients_endpoint -v

# Con cobertura
pytest tests/ --cov=gateway --cov=services
```

### Tests Manuales (cURL)
```bash
# Health check (todos los servicios)
curl http://localhost/gateway/health | jq

# Listar clientes (gRPC)
curl http://localhost/api/clients | jq

# Health de inventory (HTTP)
curl http://localhost/api/v1/inventory/health | jq

# Request con custom header
curl -H "X-Request-ID: 12345" http://localhost/api/clients
```

### Stress Testing
```bash
# Generar carga para probar rate limiting
ab -n 1000 -c 10 http://localhost/api/clients

# Con authentication token
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost/api/clients
```

---

## 🔄 CI/CD

Pipeline automatizado en GitHub Actions (`.github/workflows/ci.yml`):

1. **Linting & Code Quality** - Pylint, isort, black
2. **Unit Tests** - pytest con cobertura
3. **Integration Tests** - Docker Compose + gRPC
4. **Build Docker Images** - Build gateway image
5. **Push to Registry** - Deploy a Docker Hub (opcional)

**Estado**: [![CI/CD](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml)

---

## 🐛 Troubleshooting

### La gateway no conecta con Auth Service
```bash
# Verificar que Auth Service esté corriendo
docker ps | grep auth-service

# Revisar logs
docker logs censudex_auth-service

# Probar conexión directa
telnet auth-service 5001  # desde container de gateway
```

### gRPC service "unavailable"
```bash
# Los servicios gRPC no tienen /health endpoint HTTP
# Usar socket test en su lugar:
curl /gateway/health | jq '.services.auth.status'
```

### RabbitMQ connection refused
```bash
# Asegurar RabbitMQ esté levantado
docker ps | grep rabbitmq

# Revisar logs de RabbitMQ
docker logs censudex_rabbitmq

# Acceder a management UI
curl http://localhost:15672  # guest:guest
```

### Puerto 80 ya en uso
```bash
# Ver qué proceso ocupa el puerto
lsof -i :80

# O ejecutar nginx en puerto alternativo
docker-compose -f docker-compose.prod.yml run -p 8080:80 nginx
```

---

## 📊 Arquitectura de Protobuf

### User Service (Clients)
```protobuf
service UserService {
  rpc CreateUser (User) returns (UserResponse);
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (Empty) returns (UserList);
  rpc UpdateUser (User) returns (UserResponse);
  rpc DeleteUser (DeleteUserRequest) returns (Empty);
}
```

### Order Service
```protobuf
service OrderService {
  rpc CreateOrder (Order) returns (OrderResponse);
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc ListOrders (Empty) returns (OrderList);
}
```

**Compilar protos:**
```bash
python -m grpc_tools.protoc -I proto \
  --python_out=pb2 \
  --grpc_python_out=pb2 \
  proto/user.proto proto/order.proto
```

---

## 🔗 Repositorios Relacionados

| Servicio | Repositorio | Stack |
|----------|-------------|-------|
| **Gateway** | [censudex-api-gateway](https://github.com/nico-alvz/censudex-api-gateway) | FastAPI + gRPC |
| **Auth Service** | [censudex-auth-service](https://github.com/AlbertoLyons/censudex-auth-service) | ASP.NET Core 9.0 gRPC |
| **Clients Service** | [censudex-clients-service](https://github.com/AlbertoLyons/censudex-clients-service) | ASP.NET Core 9.0 gRPC |
| **Inventory** | [censudex-inventory-service](https://github.com/nico-alvz/censudex-inventory-service) | Python FastAPI |
| **Products** | [censudex-products](https://github.com/estudiante-b/censudex-products) | Node.js/TypeScript |
| **Orders** | [censudex-orders](https://github.com/estudiante-d/censudex-orders) | Python FastAPI |

---

## 📚 Recursos y Referencias

- [gRPC Documentation](https://grpc.io/docs/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)

---

## 🤝 Contribuyendo

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Notas de Versión

### v2.0 - gRPC Migration (Actual)
- ✅ Migración de Auth y Clients a gRPC
- ✅ Health checks adaptados para gRPC (socket test)
- ✅ RabbitMQ integrado para mensajería asíncrona
- ✅ Nginx configurado para Docker network
- ✅ CI/CD pipeline actualizado

### v1.0 - Initial Release
- HTTP-only gateway
- Servicios stub básicos
- Monitoreo simple

---

**🧠 Taller de Arquitectura de Sistemas – Censudex Microservices Platform**  
**API Gateway gRPC, escalable, con RabbitMQ y listo para producción.** 🚀

Última actualización: 2024 | Arquitectura: Microservicios + gRPC + RabbitMQ
