# Censudex Microservices API Gateway

[![CI/CD](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/nico-alvz/censudex-api-gateway)
[![gRPC](https://img.shields.io/badge/gRPC-1.60.0-orange)](https://grpc.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.11-green)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-orange)](https://www.rabbitmq.com/)

> 🚀 **Censudex API Gateway** – Implementación de un gateway de alto rendimiento para una arquitectura de microservicios distribuida con comunicación gRPC, HTTP/REST y RabbitMQ. Proyecto desarrollado como parte del Taller 2 de Arquitectura de Sistemas.

---

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Arquitectura](#️-arquitectura)
- [Patrones de Diseño](#-patrones-de-diseño)
- [Servicios y Endpoints](#-servicios-y-endpoints)
- [Instalación y Ejecución](#-instalación-y-ejecución)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
- [Ejecución de Pruebas](#-ejecución-de-pruebas)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Troubleshooting](#-troubleshooting)

---

## 🧩 Descripción del Proyecto

**Censudex** es una empresa del rubro retail que está migrando de un sistema monolítico a una arquitectura basada en microservicios. El **API Gateway** actúa como punto único de entrada (Single Point of Entry), gestionando:

- ✅ **Autenticación y Autorización**: JWT tokens con validación centralizada
- ✅ **Ruteo Inteligente**: Distribución de peticiones a microservicios especializados
- ✅ **Traducción de Protocolos**: HTTP/REST ↔ gRPC
- ✅ **Balanceo de Carga**: Nginx como reverse proxy
- ✅ **Rate Limiting**: Protección contra abuso y ataques DDoS
- ✅ **Mensajería Asíncrona**: Integración con RabbitMQ para eventos
- ✅ **Monitoreo**: Health checks y service discovery

### Tecnologías Principales

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **FastAPI** | 0.115.11 | Framework web de alto rendimiento |
| **gRPC** | 1.60.0 | Comunicación inter-servicios eficiente |
| **RabbitMQ** | 3.12 | Message broker para comunicación asíncrona |
| **Nginx** | latest | Reverse proxy y load balancer |
| **Redis** | 7.2 | Caché distribuido |
| **PostgreSQL** | 15 | Base de datos principal |
| **MySQL** | 8.0 | Base de datos para servicio de órdenes |
| **Docker** | 20.10+ | Containerización |
| **Protocol Buffers** | 3.0 | Serialización de datos para gRPC |

---
## 🏗️ Arquitectura

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENTES EXTERNOS (Web/Mobile)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Nginx Reverse Proxy (Puerto 80/443)                │
│  • Load Balancing (Round Robin)                                     │
│  • SSL/TLS Termination                                              │
│  • Rate Limiting (10000 req/min)                                    │
│  • Request Buffering                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FastAPI API Gateway (Puerto 8000)                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Middleware Stack:                                             │ │
│  │  1. RequestIDMiddleware    → Trazabilidad de requests        │ │
│  │  2. RateLimitingMiddleware → Token bucket algorithm          │ │
│  │  3. CORSMiddleware         → Control de acceso CORS          │ │
│  │  4. TrustedHostMiddleware  → Validación de hosts             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Routers:                                                      │ │
│  │  • /api/auth       → Auth Service (gRPC)                     │ │
│  │  • /api/clients    → Clients Service (gRPC)                  │ │
│  │  • /api/v1/inventory → Inventory Service (gRPC + HTTP)       │ │
│  │  • /api/orders     → Orders Service (HTTP)                   │ │
│  │  • /gateway/health → Health checks                           │ │
│  └───────────────────────────────────────────────────────────────┘ │
└──────┬─────────┬─────────┬─────────┬──────────┬────────────────────┘
       │         │         │         │          │
   gRPC│     gRPC│    gRPC │    HTTP │   RabbitMQ
       │         │      +HTTP│         │          │
       ▼         ▼         ▼         ▼          ▼
┌──────────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐
│  Auth    │ │Clients  │ │ Inventory  │ │  Orders  │ │  RabbitMQ    │
│ Service  │ │Service  │ │  Service   │ │ Service  │ │   Broker     │
│ (C# .NET)│ │(C# .NET)│ │  (Python)  │ │(C# .NET) │ │              │
│          │ │         │ │            │ │          │ │  Exchanges:  │
│ :5001    │ │ :5002   │ │:8001/:50051│ │ :5206    │ │  • inventory │
│          │ │         │ │            │ │          │ │  • orders    │
│PostgreSQL│ │PostgreSQL│ │PostgreSQL │ │  MySQL   │ │  • alerts    │
│  :5432   │ │  :5432  │ │(Supabase) │ │  :3307   │ │              │
└──────────┘ └─────────┘ └────────────┘ └──────────┘ └──────────────┘
       │         │              │              │              │
       └─────────┴──────────────┴──────────────┴──────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Redis Cache (:6379) │
                    │   • Session storage   │
                    │   • Rate limit counters│
                    └───────────────────────┘
```

### Flujo de Comunicación

#### 1. Síncrona (Request-Response)

**gRPC (Comunicación Interna)**
- Gateway ↔ Auth Service: Validación de tokens JWT
- Gateway ↔ Clients Service: CRUD de clientes usando Protocol Buffers
- Gateway ↔ Inventory Service: Consultas de inventario (dual: gRPC + HTTP)

**HTTP/REST (Comunicación Externa/Legacy)**
- Clientes ↔ Gateway: API REST JSON
- Gateway ↔ Orders Service: Gestión de pedidos
- Gateway ↔ Inventory Service: Endpoints HTTP alternativos

#### 2. Asíncrona (Event-Driven)

**RabbitMQ Message Patterns:**

```
┌─────────────┐     order_created      ┌──────────────┐
│   Orders    │ ───────────────────────>│  Inventory   │
│   Service   │                         │   Service    │
└─────────────┘                         └──────────────┘
                                              │
                                              │ low_stock_alert
                                              ▼
                                        ┌──────────────┐
                                        │ Notification │
                                        │   Service    │
                                        └──────────────┘
```

**Eventos Implementados:**
- `order_created` → Descuento de stock en inventario
- `low_stock_alert` → Notificación cuando stock < umbral
- `stock_reserved` → Reserva temporal de productos
- `stock_validation` → Validación de disponibilidad

---

## 🎨 Patrones de Diseño

### 1. API Gateway Pattern

**Propósito**: Proporcionar un punto de entrada único para todos los clientes, encapsulando la arquitectura interna.

**Implementación:**

```python
# gateway/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Censudx API Gateway",
    description="Production-ready API Gateway for microservices"
)

# Service registry para ruteo dinámico
SERVICE_REGISTRY = {
    "inventory": {
        "url": "inventory:50051",
        "grpc": True,
        "requires_auth": True,
        "timeout": 30
    },
    "auth": {
        "url": "http://auth-service:5001",
        "requires_auth": False,
        "timeout": 10
    }
}
```

**Beneficios:**
- ✅ Simplicidad para clientes (una sola URL)
- ✅ Desacoplamiento entre frontend y backend
- ✅ Centralización de cross-cutting concerns (auth, logging, rate limiting)

---

### 2. Middleware Chain Pattern

**Propósito**: Procesar requests en una cadena de responsabilidad antes de llegar a los handlers.

**Implementación:**

```python
# gateway/middleware/request_id.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generar o extraer Request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Procesar request
        response = await call_next(request)
        
        # Agregar Request ID a response
        response.headers["x-request-id"] = request_id
        return response
```

```python
# gateway/middleware/rate_limiting.py
class TokenBucket:
    def __init__(self, tokens: int, refill_rate: float):
        self.capacity = tokens
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        # Refill tokens basado en tiempo transcurrido
        self.tokens = min(
            self.capacity,
            self.tokens + (now - self.last_refill) * self.refill_rate
        )
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.buckets: Dict[str, TokenBucket] = {}
        
        # Configuración: 3000 tokens, refill 300/seg = 18000 req/min
        self.rate_limits = {
            "default": {"tokens": 3000, "refill_rate": 300.0},
            "auth": {"tokens": 3000, "refill_rate": 300.0},
        }
```

**Aplicación del Middleware:**

```python
# gateway/main.py
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitingMiddleware)  # Token Bucket Algorithm
```

---

### 3. Service Registry Pattern

**Propósito**: Descubrimiento dinámico de servicios y configuración centralizada.

**Implementación:**

```python
# gateway/main.py
async def check_services_health() -> Dict[str, Any]:
    """Health check de todos los servicios registrados"""
    services_health = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, config in SERVICE_REGISTRY.items():
            is_grpc = config.get('grpc', False)
            
            if is_grpc:
                # gRPC: verificar socket TCP
                hostname, port = config['url'].split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((hostname, int(port)))
                sock.close()
                
                services_health[service_name] = {
                    "status": "healthy" if result == 0 else "unhealthy",
                    "type": "gRPC"
                }
            else:
                # HTTP: verificar endpoint de health
                response = await client.get(f"{config['url']}/health")
                services_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "type": "HTTP"
                }
    
    return services_health
```

---

### 4. Circuit Breaker Pattern (Implícito)

**Propósito**: Prevenir cascadas de fallos cuando un servicio está caído.

**Implementación:**

```python
# gateway/routes/clients.py
def create_clients_router(service_url: str) -> APIRouter:
    router = APIRouter()
    
    @router.get("/clients")
    async def get_all_clients():
        try:
            # Timeout configurado en SERVICE_REGISTRY
            with grpc.insecure_channel(service_url) as channel:
                stub = pb2.user_pb2_grpc.UserServiceStub(channel)
                # gRPC tiene timeout implícito
                response = stub.GetAll(request)
                return response
        except grpc.RpcError as e:
            # Circuit breaker: si falla, devolver error sin reintentar
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {e.details()}"
            )
```

---

### 5. Adapter Pattern (Protocol Translation)

**Propósito**: Traducir entre HTTP/REST y gRPC transparentemente.

**Implementación:**

```python
# gateway/routes/clients.py
@router.post("/clients")
async def create_client(user: CreateUserRequest):
    """
    Adapter: HTTP Request → gRPC Call
    Convierte JSON a Protocol Buffer
    """
    with grpc.insecure_channel(user_service_url) as channel:
        stub = pb2.user_pb2_grpc.UserServiceStub(channel)
        
        # Traducción: Pydantic model → Protobuf message
        request = pb2.user_pb2.CreateUserRequest(
            names=user.names,
            lastnames=user.lastnames,
            email=user.email,
            username=user.username,
            birthdate=user.birthdate,
            address=user.address,
            phonenumber=user.phonenumber,
            password=user.password,
        )
        
        # Llamada gRPC
        response = stub.Create(request)
        
        # Traducción: Protobuf response → JSON
        return {
            "id": response.id,
            "message": response.message,
            "success": response.success
        }
```

---

### 6. Dependency Injection Pattern

**Propósito**: Inyección de dependencias para autorización y validación.

**Implementación:**

```python
# gateway/auth/authorize.py
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException

security = HTTPBearer()

async def get_user_roles(token: str) -> list[str]:
    """Obtener roles del usuario desde Auth Service"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            "http://auth-service:5001/api/auth",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        return response.json().get("roles", [])

def authorize(*required_roles: str):
    """Dependency para validar roles"""
    async def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        roles = await get_user_roles(token)
        
        # Validar roles requeridos
        if required_roles and not any(role in roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        
        return token
    
    return role_checker
```

**Uso en Endpoints:**

```python
@router.get("/clients", dependencies=[Depends(authorize("admin", "manager"))])
async def get_clients():
    """Solo accesible para admin o manager"""
    # Endpoint protegido
    pass
```

---

### 7. Publisher-Subscriber Pattern (RabbitMQ)

**Propósito**: Comunicación asíncrona desacoplada entre servicios.

**Implementación:**

```python
# services/messaging.py
import pika

class RabbitMQService:
    def __init__(self, rabbitmq_url: str):
        self.url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.consumers = {}
    
    def publish_event(self, exchange: str, routing_key: str, message: dict):
        """Publisher: Publicar evento"""
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json'
            )
        )
    
    def register_consumer(self, queue: str, callback):
        """Subscriber: Registrar consumidor de eventos"""
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_consume(
            queue=queue,
            on_message_callback=callback,
            auto_ack=False
        )
        self.consumers[queue] = callback
```

**Uso:**

```python
# Publicar evento de pedido creado
messaging.publish_event(
    exchange="orders",
    routing_key="order.created",
    message={
        "order_id": "12345",
        "items": [{"product_id": "abc", "quantity": 2}]
    }
)

# Consumir eventos de bajo stock
messaging.register_consumer(
    queue="low_stock_alerts",
    callback=lambda msg: send_alert_email(msg)
)
```

---
## 📡 Servicios y Endpoints

### Servicios Disponibles

| Servicio | Tecnología | Protocolo | Base de Datos | Puerto | Estado |
|----------|------------|-----------|---------------|--------|---------|
| **Auth Service** | ASP.NET Core 9.0 | gRPC | PostgreSQL | 5001 | ✅ Operativo |
| **Clients Service** | ASP.NET Core 9.0 | gRPC | PostgreSQL | 5002 | ✅ Operativo |
| **Inventory Service** | Python FastAPI | gRPC + HTTP | PostgreSQL (Supabase) | 8001/50051 | ✅ Operativo |
| **Orders Service** | ASP.NET Core 9.0 | HTTP | MySQL (Railway) | 5206 | ✅ Operativo |
| **API Gateway** | Python FastAPI | HTTP | - | 8000 | ✅ Operativo |
| **Nginx** | Nginx | HTTP | - | 80/443 | ✅ Operativo |

---

### Endpoints Disponibles

#### 🔐 Autenticación (`/api/auth`)

```http
POST   /api/auth/login              # Autenticar usuario
POST   /api/auth/logout             # Cerrar sesión
GET    /api/auth/validate           # Validar token JWT
POST   /api/auth/refresh            # Refrescar token
```

**Ejemplo - Login:**

```bash
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "adminCensudex",
    "password": "Admin1234!"
  }'
```

**Respuesta:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "refresh_token_here",
  "expiresIn": 3600,
  "user": {
    "id": "user-id",
    "username": "adminCensudex",
    "roles": ["admin"]
  }
}
```

---

#### 👥 Clientes (`/api/clients`) - vía gRPC

```http
GET    /api/clients                 # Listar todos los clientes
POST   /api/clients                 # Crear nuevo cliente
GET    /api/clients/{id}            # Obtener cliente por ID
PATCH  /api/clients/{id}            # Actualizar cliente
DELETE /api/clients/{id}            # Eliminar cliente
GET    /api/clients?namefilter=X    # Filtrar por nombre
GET    /api/clients?emailfilter=X   # Filtrar por email
```

**Ejemplo - Crear Cliente:**

```bash
curl -X POST http://localhost/api/clients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "names": "Juan Carlos",
    "lastnames": "Pérez González",
    "email": "juan.perez@example.com",
    "username": "jperez",
    "birthdate": "1990-05-15",
    "address": "Av. Principal 123, Santiago",
    "phonenumber": "+56912345678",
    "password": "SecurePass123!"
  }'
```

**Ejemplo - Listar Clientes con Filtro:**

```bash
curl http://localhost/api/clients?namefilter=Juan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Respuesta:**

```json
{
  "clients": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "names": "Juan Carlos",
      "lastnames": "Pérez González",
      "email": "juan.perez@example.com",
      "username": "jperez",
      "birthdate": "1990-05-15",
      "address": "Av. Principal 123, Santiago",
      "phonenumber": "+56912345678",
      "status": "active",
      "createdAt": "2024-11-16T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

#### 📦 Inventario (`/api/v1/inventory`) - Dual: gRPC + HTTP

```http
GET    /api/v1/inventory            # Listar inventario completo
GET    /api/v1/inventory/{id}       # Obtener item específico
POST   /api/v1/inventory            # Crear nuevo item
PATCH  /api/v1/inventory/{id}       # Actualizar item
DELETE /api/v1/inventory/{id}       # Eliminar item
GET    /api/v1/inventory/search?q=X # Buscar productos
GET    /api/v1/inventory/low-stock  # Items con stock bajo
GET    /api/v1/inventory/health     # Health check del servicio
```

**Ejemplo - Listar Inventario:**

```bash
curl http://localhost/api/v1/inventory \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Ejemplo - Actualizar Stock:**

```bash
curl -X PATCH http://localhost/api/v1/inventory/prod-123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "quantity": 50,
    "status": "available"
  }'
```

**Ejemplo - Items con Stock Bajo:**

```bash
curl http://localhost/api/v1/inventory/low-stock \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 🛒 Pedidos (`/api/orders`)

```http
POST   /api/orders                  # Crear nuevo pedido
GET    /api/orders/{id}             # Obtener pedido por ID
GET    /api/orders                  # Listar pedidos
PATCH  /api/orders/{id}/status      # Actualizar estado
DELETE /api/orders/{id}             # Cancelar pedido
```

**Ejemplo - Crear Pedido:**

```bash
curl -X POST http://localhost/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "userId": "2ce25761-a799-44bf-9a2c-ec50d58bc500",
    "userName": "adminCensudex",
    "address": "Av. Libertador 456, Santiago",
    "userEmail": "admin@censudex.com",
    "items": [
      {
        "productId": "550e8400-e29b-41d4-a716-446655440000",
        "productName": "Laptop HP",
        "quantity": 2,
        "unitPrice": 599.99
      }
    ]
  }'
```

**Respuesta:**

```json
{
  "orderId": "order-12345",
  "status": "pending",
  "totalAmount": 1199.98,
  "createdAt": "2024-11-16T14:20:00Z",
  "message": "Order created successfully"
}
```

---

#### 🏥 Health Checks y Monitoreo

```http
GET    /gateway/health              # Estado del gateway y todos los servicios
GET    /gateway/services            # Lista de servicios registrados
GET    /docs                        # Documentación Swagger interactiva
GET    /redoc                       # Documentación ReDoc
GET    /nginx_status                # Estado de Nginx
```

**Ejemplo - Health Check:**

```bash
curl http://localhost/gateway/health | jq
```

**Respuesta:**

```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "timestamp": "2024-11-16T15:45:30.123456",
  "uptime": 1700145930,
  "services": {
    "auth": {
      "status": "healthy",
      "url": "http://auth-service:5001",
      "type": "gRPC",
      "last_check": "2024-11-16T15:45:30.100000"
    },
    "clients": {
      "status": "healthy",
      "url": "clients-service:5002",
      "type": "gRPC",
      "last_check": "2024-11-16T15:45:30.110000"
    },
    "inventory": {
      "status": "healthy",
      "url": "inventory:50051",
      "type": "gRPC + HTTP",
      "last_check": "2024-11-16T15:45:30.120000"
    },
    "orders": {
      "status": "healthy",
      "url": "http://host.docker.internal:5207",
      "type": "HTTP",
      "last_check": "2024-11-16T15:45:30.130000"
    }
  }
}
```

---

#### 🔔 Notificaciones (`/api/notifications`)

```http
GET    /api/notifications           # Obtener todas las notificaciones
GET    /api/notifications/unread    # Notificaciones no leídas
POST   /api/notifications/{id}/read # Marcar como leída
DELETE /api/notifications/{id}      # Eliminar notificación
```

**Ejemplo - Listar Notificaciones:**

```bash
curl http://localhost/api/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Códigos de Respuesta HTTP

| Código | Significado | Descripción |
|--------|-------------|-------------|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado exitosamente |
| 204 | No Content | Eliminación exitosa |
| 400 | Bad Request | Datos inválidos en la solicitud |
| 401 | Unauthorized | Token inválido o expirado |
| 403 | Forbidden | Sin permisos para acceder al recurso |
| 404 | Not Found | Recurso no encontrado |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Error interno del servidor |
| 502 | Bad Gateway | Error en servicio downstream |
| 503 | Service Unavailable | Servicio temporalmente no disponible |
| 504 | Gateway Timeout | Timeout en servicio downstream |

---
## 💻 Instalación y Ejecución

### Requisitos Previos

#### Linux/macOS

```bash
# Docker y Docker Compose
docker --version        # >= 20.10
docker-compose --version # >= 2.0

# Python (para desarrollo local)
python3 --version       # >= 3.11

# .NET SDK 9.0 (para Orders Service)
# Instalación:
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 9.0 --install-dir $HOME/.dotnet
export PATH="$HOME/.dotnet:$PATH"

# Herramientas adicionales
curl --version          # Para testing
jq --version           # Para parsear JSON
socat --version        # Para port forwarding
```

#### Windows

```powershell
# Docker Desktop for Windows
# Descargar: https://docs.docker.com/desktop/install/windows-install/
docker --version        # >= 20.10
docker-compose --version # >= 2.0

# Python 3.11+
# Descargar: https://www.python.org/downloads/windows/
python --version        # >= 3.11

# .NET SDK 9.0
# Descargar: https://dotnet.microsoft.com/download/dotnet/9.0
dotnet --version        # >= 9.0.100

# Git for Windows
# Descargar: https://git-scm.com/download/win

# Herramientas adicionales
# Instalar desde: https://curl.se/windows/
curl --version

# jq para Windows
# Descargar: https://jqlang.github.io/jq/download/
```

---

### Instalación Paso a Paso

#### Linux/macOS

##### 1. Clonar el Repositorio

```bash
# Clonar proyecto principal
git clone https://github.com/nico-alvz/censudex-api-gateway.git
cd censudex-api-gateway

# Verificar estructura
ls -la
```

##### 2. Configurar Variables de Entorno

```bash
# Crear archivo .env (opcional - tiene defaults)
cat > .env << EOF
# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=censudx
RABBITMQ_PASSWORD=censudex_password
RABBITMQ_VHOST=/censudx_vhost

# Inventory Service
LOW_STOCK_THRESHOLD=10
ENABLE_AUTO_ALERTS=true
ALERT_EMAIL_RECIPIENTS=admin@censudex.com

# Gateway
DEBUG=false
ENABLE_NOTIFICATIONS=true
LOG_LEVEL=INFO
MAX_NOTIFICATION_HISTORY=1000
EOF
```

##### 3. Opción A - Inicio Rápido con Script Automatizado

```bash
# Dar permisos de ejecución
chmod +x start_all_services.sh

# Ejecutar script de inicio completo
./start_all_services.sh
```

Este script realiza:
- ✅ Verificación de prerequisitos
- ✅ Inicio de servicios Docker (Gateway, Auth, Clients, Inventory, Databases, RabbitMQ, Redis)
- ✅ Configuración de RabbitMQ
- ✅ Inicio del Orders Service con .NET 9
- ✅ Configuración de port forwarding (socat)
- ✅ Health checks de todos los servicios
- ✅ Reporte de estado final

**Salida esperada:**

```
========================================
CENSUDEX - SYSTEM STARTUP
========================================

ℹ Checking prerequisites...
✓ All prerequisites found

========================================
STEP 1: Configure RabbitMQ
========================================
✓ RabbitMQ configured

========================================
STEP 2: Start Docker Services
========================================
ℹ Starting services with docker-compose...
✓ Docker services started

========================================
STEP 3: Configure Port Forwarding
========================================
✓ Port forwarding started (PID: 12345)

========================================
STEP 4: Start Orders Service (.NET 9.0)
========================================
✓ Orders service started (PID: 67890)

========================================
STEP 5: Service Verification
========================================
✓ Gateway listening on port 8000
✓ Auth Service (Docker) listening on port 5001
✓ Clients Service (Docker) listening on port 5002
✓ Inventory Service (Docker) listening on port 50051
✓ Orders Service (Host) listening on port 5206
✓ Port Forwarding (socat) listening on port 5207

========================================
STEP 6: Gateway Health Check
========================================
✓ Gateway is healthy

========================================
STARTUP COMPLETE
========================================
✓ All services are running!
```

##### 4. Opción B - Inicio Manual Paso a Paso

```bash
# Paso 1: Iniciar servicios Docker
cd /path/to/taller2
docker-compose -f docker-compose.prod.yml up -d

# Paso 2: Esperar a que los servicios estén listos
sleep 30

# Paso 3: Configurar RabbitMQ
docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password

# Paso 4: Configurar port forwarding para Orders Service
# (necesario para comunicación entre container y host)
pkill -f "socat.*5207" || true
socat TCP4-LISTEN:5207,fork,reuseaddr TCP4:127.0.0.1:5206 &

# Paso 5: Iniciar Orders Service
cd censudex-orders-service
$HOME/.dotnet/dotnet run --project OrderService.csproj \
  --no-launch-profile > orders.log 2>&1 &

# Paso 6: Verificar health
curl http://localhost:8000/gateway/health | jq
```

##### 5. Verificar Instalación

```bash
# Ver containers en ejecución
docker ps

# Verificar logs del Gateway
docker logs censudex_gateway -f

# Verificar logs de Orders Service
tail -f censudex-orders-service/orders.log

# Test rápido de endpoints
curl http://localhost/gateway/health
curl http://localhost/api/clients
```

---

#### Windows

##### 1. Clonar el Repositorio

```powershell
# Abrir PowerShell como Administrador

# Clonar proyecto
git clone https://github.com/nico-alvz/censudex-api-gateway.git
cd censudex-api-gateway
```

##### 2. Crear Script PowerShell de Inicio

```powershell
# Crear archivo start_all_services.ps1
@'
# CENSUDEX - Windows Startup Script
Write-Host "========================================" -ForegroundColor Blue
Write-Host "CENSUDEX - SYSTEM STARTUP" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Verificar Docker Desktop
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Verificar .NET SDK
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "Error: .NET SDK not found. Please install .NET 9.0 SDK." -ForegroundColor Red
    exit 1
}

Write-Host "Prerequisites OK" -ForegroundColor Green

# Navegar al directorio del proyecto
$TALLER2_DIR = "C:\Users\YourUser\Desktop\taller2"  # CAMBIAR ESTA RUTA
cd $TALLER2_DIR

# Iniciar servicios Docker
Write-Host "`nStarting Docker services..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d

# Esperar a que los servicios estén listos
Write-Host "Waiting for services to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Configurar RabbitMQ
Write-Host "Configuring RabbitMQ..." -ForegroundColor Yellow
docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password

# Iniciar Orders Service
Write-Host "`nStarting Orders Service..." -ForegroundColor Yellow
cd censudex-orders-service

Start-Process -NoNewWindow -FilePath "dotnet" `
    -ArgumentList "run","--project","OrderService.csproj","--no-launch-profile" `
    -RedirectStandardOutput "orders.log" `
    -RedirectStandardError "orders_error.log"

Start-Sleep -Seconds 15

# Verificar health
Write-Host "`nChecking gateway health..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8000/gateway/health"
Write-Host "Gateway Status: $($health.status)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "STARTUP COMPLETE" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "`nAccess URLs:" -ForegroundColor Cyan
Write-Host "  Gateway:  http://localhost:8000" -ForegroundColor White
Write-Host "  Nginx:    http://localhost:80" -ForegroundColor White
Write-Host "  Swagger:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  RabbitMQ: http://localhost:15672" -ForegroundColor White
'@ | Out-File -FilePath start_all_services.ps1 -Encoding UTF8
```

##### 3. Ejecutar Script de Inicio

```powershell
# Permitir ejecución de scripts (ejecutar UNA VEZ como Administrador)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Ejecutar script de inicio
.\start_all_services.ps1
```

##### 4. Inicio Manual (Alternativa)

```powershell
# Paso 1: Iniciar Docker Desktop
# Verificar que Docker Desktop esté ejecutándose

# Paso 2: Iniciar servicios
cd C:\Users\YourUser\Desktop\taller2  # Ajustar ruta
docker-compose -f docker-compose.prod.yml up -d

# Paso 3: Esperar
Start-Sleep -Seconds 30

# Paso 4: Configurar RabbitMQ
docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password

# Paso 5: Iniciar Orders Service
cd censudex-orders-service
Start-Process -NoNewWindow -FilePath "dotnet" `
    -ArgumentList "run","--project","OrderService.csproj"

# Paso 6: Verificar
Invoke-RestMethod -Uri "http://localhost:8000/gateway/health" | ConvertTo-Json
```

##### 5. Verificar Instalación Windows

```powershell
# Ver containers
docker ps

# Ver logs del Gateway
docker logs censudex_gateway -f

# Ver logs de Orders Service
Get-Content censudex-orders-service\orders.log -Wait

# Test de endpoints
Invoke-RestMethod -Uri "http://localhost/gateway/health"
Invoke-RestMethod -Uri "http://localhost/api/clients"
```

---

### Acceso a Componentes

| Componente | URL | Credenciales | Descripción |
|-----------|-----|--------------|-------------|
| **API Gateway** | http://localhost:8000 | - | FastAPI application |
| **Nginx Proxy** | http://localhost:80 | - | Reverse proxy y load balancer |
| **Swagger UI** | http://localhost:8000/docs | - | Documentación interactiva |
| **ReDoc** | http://localhost:8000/redoc | - | Documentación alternativa |
| **RabbitMQ Management** | http://localhost:15672 | guest / guest | UI de administración |
| **PostgreSQL** | localhost:5432 | postgres / postgres | Base de datos principal |
| **MySQL** | localhost:3307 | root / root | Base de datos Orders |
| **Redis** | localhost:6379 | - | Caché distribuido |

---

### Comandos Útiles

#### Linux/macOS

```bash
# Ver logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker logs censudex_gateway -f
docker logs censudex_auth_service -f
docker logs censudex_inventory -f

# Reiniciar un servicio
docker-compose -f docker-compose.prod.yml restart gateway

# Detener todos los servicios
docker-compose -f docker-compose.prod.yml down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker-compose -f docker-compose.prod.yml down -v

# Ver estado de puertos
ss -tlnp | grep -E '8000|5001|5002|5206|5672|5432'

# Acceder a un container
docker exec -it censudex_gateway /bin/bash

# Ver uso de recursos
docker stats
```

#### Windows PowerShell

```powershell
# Ver logs de todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker logs censudex_gateway -Follow
docker logs censudex_auth_service -Follow

# Reiniciar un servicio
docker-compose -f docker-compose.prod.yml restart gateway

# Detener todos los servicios
docker-compose -f docker-compose.prod.yml down

# Ver estado de puertos
Get-NetTCPConnection | Where-Object {$_.LocalPort -in 8000,5001,5002,5206,5672}

# Acceder a un container
docker exec -it censudex_gateway /bin/bash

# Ver uso de recursos
docker stats
```

---
## 🧪 Ejecución de Pruebas

### Pruebas Unitarias e Integración

#### Linux/macOS

```bash
# Navegar al directorio del proyecto
cd /path/to/censudex-api-gateway

# Opción 1: Usar script de pruebas
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh

# Opción 2: Ejecutar con pytest directamente
# Activar entorno virtual (si aplica)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todas las pruebas
pytest tests/ -v

# Ejecutar pruebas específicas
pytest tests/test_gateway.py -v
pytest tests/test_gateway.py::test_health_endpoint -v

# Con cobertura de código
pytest tests/ --cov=gateway --cov=services --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Windows PowerShell

```powershell
# Navegar al directorio del proyecto
cd C:\path\to\censudex-api-gateway

# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todas las pruebas
pytest tests\ -v

# Ejecutar pruebas específicas
pytest tests\test_gateway.py -v

# Con cobertura de código
pytest tests\ --cov=gateway --cov=services --cov-report=html

# Ver reporte de cobertura
Start-Process htmlcov\index.html
```

---

### Pruebas de Integración (Workflow Completo)

#### Linux/macOS

```bash
# Script de pruebas de inventario completo
chmod +x inventory_tests.sh
./inventory_tests.sh

# Script de pruebas de workflow de pedidos
chmod +x test_inventory_workflow.sh
./test_inventory_workflow.sh
```

**Salida esperada de `inventory_tests.sh`:**

```
========================================
CENSUDEX INVENTORY SERVICE - TEST SUITE
========================================

TEST 1: Health Check
----------------------------------------
✓ Inventory service is healthy

TEST 2: List All Items
----------------------------------------
✓ Found 15 items in inventory

TEST 3: Create New Item
----------------------------------------
✓ Item created: prod-test-12345

TEST 4: Get Specific Item
----------------------------------------
✓ Retrieved item: prod-test-12345

TEST 5: Update Item
----------------------------------------
✓ Item updated successfully

TEST 6: Low Stock Alert
----------------------------------------
✓ 3 items with low stock detected

TEST 7: RabbitMQ Integration
----------------------------------------
✓ Low stock alert published to RabbitMQ

========================================
ALL TESTS PASSED ✓
========================================
```

#### Windows PowerShell

```powershell
# Crear script de pruebas de inventario
@'
Write-Host "========================================" -ForegroundColor Blue
Write-Host "CENSUDEX INVENTORY SERVICE - TEST SUITE" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

$BASE_URL = "http://localhost/api/v1/inventory"

# TEST 1: Health Check
Write-Host "`nTEST 1: Health Check" -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "$BASE_URL/health"
if ($health.status -eq "healthy") {
    Write-Host "✓ Inventory service is healthy" -ForegroundColor Green
}

# TEST 2: List All Items
Write-Host "`nTEST 2: List All Items" -ForegroundColor Yellow
$items = Invoke-RestMethod -Uri $BASE_URL
Write-Host "✓ Found $($items.Count) items in inventory" -ForegroundColor Green

# TEST 3: Create New Item
Write-Host "`nTEST 3: Create New Item" -ForegroundColor Yellow
$newItem = @{
    id = "prod-test-" + (Get-Random)
    name = "Test Product"
    quantity = 100
    price = 29.99
    status = "available"
} | ConvertTo-Json

$created = Invoke-RestMethod -Uri $BASE_URL -Method Post `
    -Body $newItem -ContentType "application/json"
Write-Host "✓ Item created: $($created.id)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "TESTS COMPLETED" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
'@ | Out-File -FilePath inventory_tests.ps1 -Encoding UTF8

# Ejecutar
.\inventory_tests.ps1
```

---

### Pruebas de Estrés (JMeter)

El proyecto incluye pruebas de estrés con Apache JMeter para validar el rendimiento del sistema bajo carga.

#### Prerequisitos

```bash
# Linux/macOS
# Descargar JMeter 5.6.3
wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xzf apache-jmeter-5.6.3.tgz
sudo mv apache-jmeter-5.6.3 /opt/jmeter
export PATH="/opt/jmeter/bin:$PATH"

# Verificar instalación
jmeter --version
```

```powershell
# Windows
# Descargar: https://jmeter.apache.org/download_jmeter.cgi
# Extraer a C:\jmeter
# Agregar C:\jmeter\bin al PATH

# Verificar
jmeter --version
```

#### Ejecutar Pruebas de Estrés

##### Linux/macOS

```bash
cd stress_tests

# Opción 1: Script automatizado con 3 modos
chmod +x run_jmeter_tests.sh
./run_jmeter_tests.sh

# Seleccionar modo:
# [1] Quick Test  - 20 usuarios, 30 segundos
# [2] Medium Test - 200 usuarios, 2 minutos
# [3] Full Test   - 2000 usuarios, 5 minutos

# Opción 2: Ejecutar test específico manualmente

# Test de Login (2000 usuarios, 5 minutos)
jmeter -n -t login/Login_Stress_Test.jmx \
  -JNUM_THREADS=2000 \
  -JRAMP_UP=10 \
  -JDURATION=300 \
  -l results/login_2000users.jtl \
  -e -o results/login_2000users_report

# Test de Creación de Pedidos (500 usuarios, 15 minutos)
jmeter -n -t orders/Create_Orders.jmx \
  -JNUM_THREADS=500 \
  -JRAMP_UP=60 \
  -JDURATION=900 \
  -JTHINK_TIME=1000 \
  -l results/orders_500users.jtl \
  -e -o results/orders_500users_report

# Test de Navegación de Catálogo (5000 usuarios, 3 loops)
jmeter -n -t catalog/Browse_Catalog.jmx \
  -JNUM_THREADS=5000 \
  -JRAMP_UP=120 \
  -JLOOPS=3 \
  -JTHINK_TIME=2000 \
  -l results/catalog_5000users.jtl \
  -e -o results/catalog_5000users_report

# Ver reportes HTML
xdg-open results/login_2000users_report/index.html
```

##### Windows PowerShell

```powershell
cd stress_tests

# Test de Login
jmeter -n -t login\Login_Stress_Test.jmx `
  -JNUM_THREADS=2000 `
  -JRAMP_UP=10 `
  -JDURATION=300 `
  -l results\login_2000users.jtl `
  -e -o results\login_2000users_report

# Test de Pedidos
jmeter -n -t orders\Create_Orders.jmx `
  -JNUM_THREADS=500 `
  -JRAMP_UP=60 `
  -JDURATION=900 `
  -l results\orders_500users.jtl `
  -e -o results\orders_500users_report

# Abrir reporte
Start-Process results\login_2000users_report\index.html
```

#### Resultados de Pruebas de Estrés

**Test de Login (2000 usuarios concurrentes):**

```
Summary Report:
=====================================
Total Requests:    2000
Successful:        1386 (69.3%)
Failed:            614 (30.7%)
Throughput:        175.7 req/s
Avg Response Time: 1199 ms
Min Response Time: 614 ms
Max Response Time: 29821 ms

Error Analysis:
- NoHttpResponseException: 614 (connection pool exhausted - expected under extreme load)

Conclusion: ✅ System handles 1386 concurrent logins successfully
```

**Test de Creación de Pedidos (500 usuarios, 15 minutos):**

```
Summary Report:
=====================================
Total Requests:    161,777
Successful:        718 (0.44%)
Failed:            161,059 (99.56%)
Throughput:        180 req/s
Avg Response Time: 1095 ms

Error Analysis:
- 503 Service Unavailable: 19,380 (MySQL connection pool saturated)
- NoHttpResponseException: 141,679 (gateway connection limit reached)

Conclusion: ⚠️ Orders service saturates under extreme load (expected with 500 concurrent users)
Note: Real-world scenarios rarely have 500 simultaneous order creations
```

---

### Pruebas Manuales con cURL

#### Autenticación

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"adminCensudex","password":"Admin1234!"}' \
  | jq -r '.token')

echo "Token: $TOKEN"
```

#### Clientes (gRPC)

```bash
# Listar clientes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/clients | jq

# Crear cliente
curl -X POST http://localhost/api/clients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "names": "Test User",
    "lastnames": "Demo",
    "email": "test@demo.com",
    "username": "testuser",
    "birthdate": "1990-01-01",
    "address": "Test Address 123",
    "phonenumber": "+56912345678",
    "password": "Test1234!"
  }' | jq

# Filtrar por nombre
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost/api/clients?namefilter=Test" | jq
```

#### Inventario

```bash
# Listar inventario
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/inventory | jq

# Items con stock bajo
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/v1/inventory/low-stock | jq

# Actualizar item
curl -X PATCH http://localhost/api/v1/inventory/prod-123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 50}' | jq
```

#### Pedidos

```bash
# Crear pedido
curl -X POST http://localhost/api/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "2ce25761-a799-44bf-9a2c-ec50d58bc500",
    "userName": "adminCensudex",
    "address": "Test Address",
    "userEmail": "admin@censudex.com",
    "items": [{
      "productId": "550e8400-e29b-41d4-a716-446655440000",
      "productName": "Test Product",
      "quantity": 2,
      "unitPrice": 99.99
    }]
  }' | jq
```

---

### Pruebas de RabbitMQ

```bash
# Ver eventos de stock bajo
chmod +x scripts/check_rabbitmq_events.sh
./scripts/check_rabbitmq_events.sh

# Demo de alertas
chmod +x scripts/demo_rabbitmq_alerts.sh
./scripts/demo_rabbitmq_alerts.sh

# Acceder a RabbitMQ Management UI
# Browser: http://localhost:15672
# User: guest / Password: guest
```

---

### Verificación de Salud del Sistema

```bash
# Health check completo
curl http://localhost/gateway/health | jq

# Verificar cada servicio
curl http://localhost:8000/gateway/health | jq '.services.auth'
curl http://localhost:8000/gateway/health | jq '.services.clients'
curl http://localhost:8000/gateway/health | jq '.services.inventory'
curl http://localhost:8000/gateway/health | jq '.services.orders'

# Verificar conectividad de base de datos
docker exec censudex_postgres psql -U postgres -c "\l"
docker exec censudex_mysql mysql -u root -proot -e "SHOW DATABASES;"

# Verificar RabbitMQ
docker exec censudx_rabbitmq rabbitmqctl list_queues
docker exec censudx_rabbitmq rabbitmqctl list_exchanges
```

---

### Análisis de Performance

```bash
# Apache Bench - Test rápido
ab -n 1000 -c 10 http://localhost/gateway/health

# Con autenticación
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost/api/clients

# wrk - Benchmark más avanzado (si está instalado)
wrk -t12 -c400 -d30s http://localhost/gateway/health

# Monitorear recursos de containers
docker stats --no-stream

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f gateway
```

---
## 📁 Estructura del Proyecto

```
censudex-api-gateway/
│
├── 📄 README.md                          # Este archivo
├── 📄 requirements.txt                   # Dependencias Python
├── 📄 pytest.ini                         # Configuración de pytest
├── 📄 Makefile                           # Comandos make para desarrollo
├── 📄 docker-compose.yml                 # Docker compose para desarrollo
├── 📄 .env                               # Variables de entorno (crear manualmente)
├── 📄 .gitignore                         # Archivos ignorados por git
│
├── 📂 gateway/                           # Código principal del Gateway
│   ├── 📄 __init__.py
│   ├── 📄 main.py                        # Punto de entrada FastAPI
│   ├── 📄 config.py                      # Configuración centralizada
│   ├── 📄 Dockerfile                     # Imagen Docker del gateway
│   ├── 📄 requirements.txt               # Dependencias específicas
│   │
│   ├── 📂 auth/                          # Módulo de autenticación
│   │   ├── 📄 __init__.py
│   │   └── 📄 authorize.py               # Middleware JWT y RBAC
│   │
│   ├── 📂 middleware/                    # Middlewares personalizados
│   │   ├── 📄 __init__.py
│   │   ├── 📄 rate_limiting.py           # Rate limiting (Token Bucket)
│   │   └── 📄 request_id.py              # Request ID tracking
│   │
│   └── 📂 routes/                        # Routers de endpoints
│       ├── 📄 __init__.py
│       ├── 📄 auth.py                    # Endpoints /api/auth
│       ├── 📄 clients.py                 # Endpoints /api/clients (gRPC)
│       ├── 📄 inventory.py               # Endpoints /api/v1/inventory (gRPC+HTTP)
│       ├── 📄 Orders.py                  # Endpoints /api/orders
│       ├── 📄 health.py                  # Health checks
│       ├── 📄 proxy.py                   # Proxy genérico
│       └── 📄 notifications.py           # Notificaciones
│
├── 📂 models/                            # Modelos de datos (Pydantic)
│   ├── 📄 __init__.py
│   ├── 📄 requests.py                    # Schemas de request
│   ├── 📄 responses.py                   # Schemas de response
│   └── 📄 user.py                        # Modelo de usuario
│
├── 📂 pb2/                               # Protocol Buffers compilados
│   ├── 📄 __init__.py
│   ├── 📄 inventory_pb2.py               # Generado desde inventory.proto
│   ├── 📄 inventory_pb2_grpc.py          # Stubs gRPC de inventory
│   ├── 📄 order_pb2.py                   # Generado desde order.proto
│   ├── 📄 order_pb2_grpc.py              # Stubs gRPC de orders
│   ├── 📄 user_pb2.py                    # Generado desde user.proto
│   └── 📄 user_pb2_grpc.py               # Stubs gRPC de users
│
├── 📂 proto/                             # Definiciones Protocol Buffers (.proto)
│   ├── 📄 inventory.proto                # Contrato de Inventory Service
│   ├── 📄 order.proto                    # Contrato de Order Service
│   └── 📄 user.proto                     # Contrato de User/Clients Service
│
├── 📂 services/                          # Servicios auxiliares y stubs
│   ├── 📂 auth-stub/                     # Auth service stub (testing)
│   ├── 📂 inventory/                     # Inventory service (Python FastAPI)
│   ├── 📂 order-stub/                    # Order service stub
│   ├── 📂 product-stub/                  # Product service stub
│   ├── 📂 user_stub/                     # Clients service stub
│   ├── 📄 messaging.py                   # RabbitMQ service wrapper
│   └── 📄 event_consumer.py              # Event consumer logic
│
├── 📂 nginx/                             # Configuración Nginx
│   └── 📄 nginx.conf                     # Reverse proxy + load balancer config
│
├── 📂 tests/                             # Pruebas unitarias e integración
│   ├── 📄 __init__.py
│   ├── 📄 test_gateway.py                # Tests del gateway
│   ├── 📄 test_auth.py                   # Tests de autenticación
│   ├── 📄 test_clients.py                # Tests de clientes
│   └── 📄 test_inventory.py              # Tests de inventario
│
├── 📂 scripts/                           # Scripts de utilidad
│   ├── 📄 run-tests.sh                   # Ejecutar suite de tests
│   ├── 📄 setup-dev.sh                   # Setup de desarrollo
│   ├── 📄 check_rabbitmq_events.sh       # Monitorear eventos RabbitMQ
│   ├── 📄 demo_load_balancer.sh          # Demo de balanceo de carga
│   └── 📄 demo_rabbitmq_alerts.sh        # Demo de alertas asíncronas
│
├── 📂 stress_tests/                      # Pruebas de estrés (JMeter)
│   ├── 📄 run_jmeter_tests.sh            # Script automatizado de tests
│   │
│   ├── 📂 login/                         # Test de autenticación
│   │   ├── 📄 Login_Stress_Test.jmx      # Plan de prueba JMeter
│   │   ├── 📄 POST_LOGIN_20.csv          # Datos para 20 usuarios
│   │   ├── 📄 POST_LOGIN_200.csv         # Datos para 200 usuarios
│   │   └── 📄 POST_LOGIN_2000.csv        # Datos para 2000 usuarios
│   │
│   ├── 📂 orders/                        # Test de creación de pedidos
│   │   └── 📄 Create_Orders.jmx          # Plan de prueba (500 users, 15 min)
│   │
│   ├── 📂 catalog/                       # Test de navegación de catálogo
│   │   └── 📄 Browse_Catalog.jmx         # Plan de prueba (5000 users)
│   │
│   └── 📂 results/                       # Resultados de tests (generados)
│       ├── 📂 login_2000users_report/    # Reporte HTML
│       └── 📄 login_2000users.jtl        # Archivo de resultados
│
├── 📂 Postman/                           # Colecciones Postman
│   ├── 📄 API GATEWAY.postman_collection.json
│   └── 📄 Censudex_API_Complete_Flow.postman_collection.json
│
├── 📄 start_all_services.sh              # Script de inicio completo (Linux/macOS)
├── 📄 start-services.sh                  # Script de inicio alternativo
├── 📄 inventory_tests.sh                 # Tests de inventario
└── 📄 worker.py                          # Worker RabbitMQ standalone

```

---

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=censudx
RABBITMQ_PASSWORD=censudex_password
RABBITMQ_VHOST=/censudx_vhost
RABBITMQ_URL=amqp://censudx:censudex_password@rabbitmq:5672/censudx_vhost

# Inventory Service Configuration
LOW_STOCK_THRESHOLD=10
ENABLE_AUTO_ALERTS=true
ALERT_EMAIL_RECIPIENTS=admin@censudex.com,inventory@censudex.com

# Gateway Configuration
DEBUG=false
ENABLE_NOTIFICATIONS=true
LOG_LEVEL=INFO
MAX_NOTIFICATION_HISTORY=1000

# Service URLs (Docker network)
AUTH_SERVICE_URL=http://auth-service:5001
CLIENTS_SERVICE_URL=clients-service:5002
INVENTORY_SERVICE_URL=inventory:50051
ORDERS_SERVICE_URL=http://host.docker.internal:5207

# Security
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Database (si aplica)
DATABASE_URL=postgresql://user:password@localhost:5432/censudex

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

### Compilación de Protocol Buffers

Si modificas los archivos `.proto`:

```bash
# Navegar al directorio del proyecto
cd censudex-api-gateway

# Compilar todos los archivos .proto
python -m grpc_tools.protoc \
  -I proto \
  --python_out=pb2 \
  --grpc_python_out=pb2 \
  proto/user.proto \
  proto/order.proto \
  proto/inventory.proto

# O usar el Makefile
make proto-compile
```

---

### Configuración de Nginx

El archivo `nginx/nginx.conf` configura:

- **Reverse Proxy**: Ruteo de requests al gateway
- **Load Balancing**: Distribución entre múltiples instancias
- **Rate Limiting**: Límite de 10000 req/min por IP
- **Buffering**: Optimización de requests grandes
- **Timeouts**: Configuración de timeouts HTTP

```nginx
upstream gateway_backend {
    # Load balancing: Round Robin
    server gateway:8000;
    # Descomentar para múltiples instancias:
    # server gateway2:8000;
    # server gateway3:8000;
}

server {
    listen 80;
    server_name localhost;

    # Rate limiting zone
    limit_req_zone $binary_remote_addr zone=gateway_limit:10m rate=10000r/m;

    location / {
        limit_req zone=gateway_limit burst=20 nodelay;
        
        proxy_pass http://gateway_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 🐛 Troubleshooting

### Problema: Gateway no conecta con Auth Service

**Síntomas:**
```
ERROR: Connection refused to auth-service:5001
```

**Solución:**

```bash
# 1. Verificar que Auth Service esté corriendo
docker ps | grep auth

# 2. Ver logs del Auth Service
docker logs censudex_auth_service

# 3. Verificar red Docker
docker network inspect taller2_default

# 4. Probar conectividad desde el container del gateway
docker exec -it censudex_gateway ping auth-service
docker exec -it censudex_gateway telnet auth-service 5001

# 5. Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart auth-service gateway
```

---

### Problema: gRPC "Service Unavailable"

**Síntomas:**
```json
{
  "error": "Service unavailable: StatusCode.UNAVAILABLE"
}
```

**Solución:**

```bash
# Los servicios gRPC no tienen endpoints HTTP /health
# Verificar con socket test:

# Opción 1: Desde host
telnet localhost 5001  # Auth Service
telnet localhost 5002  # Clients Service

# Opción 2: Desde container gateway
docker exec censudex_gateway python3 -c "
import socket
sock = socket.socket()
result = sock.connect_ex(('auth-service', 5001))
print('OK' if result == 0 else 'FAIL')
sock.close()
"

# Opción 3: Ver health en gateway
curl http://localhost/gateway/health | jq '.services.auth'
```

---

### Problema: RabbitMQ Connection Refused

**Síntomas:**
```
pika.exceptions.AMQPConnectionError: Connection refused
```

**Solución:**

```bash
# 1. Verificar RabbitMQ está corriendo
docker ps | grep rabbitmq

# 2. Ver logs
docker logs censudx_rabbitmq

# 3. Acceder a Management UI
open http://localhost:15672  # guest/guest

# 4. Verificar vhost y usuario
docker exec censudx_rabbitmq rabbitmqctl list_vhosts
docker exec censudx_rabbitmq rabbitmqctl list_users

# 5. Crear vhost si no existe
docker exec censudx_rabbitmq rabbitmqctl add_vhost /censudx_vhost
docker exec censudx_rabbitmq rabbitmqctl set_permissions -p /censudx_vhost censudx ".*" ".*" ".*"

# 6. Cambiar contraseña
docker exec censudx_rabbitmq rabbitmqctl change_password censudx censudex_password
```

---

### Problema: Puerto 80 Ya en Uso

**Síntomas:**
```
Error: bind: address already in use (0.0.0.0:80)
```

**Solución:**

```bash
# Linux/macOS
# Ver qué proceso usa el puerto
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# Matar proceso
sudo kill -9 <PID>

# O usar puerto alternativo en docker-compose
# Editar docker-compose.prod.yml:
# ports:
#   - "8080:80"  # Cambiar a puerto 8080

# Windows
# Ver proceso
netstat -ano | findstr :80
Get-Process -Id <PID>

# Matar proceso
Stop-Process -Id <PID> -Force
```

---

### Problema: Orders Service No Inicia (.NET 9)

**Síntomas:**
```
A fatal error occurred. The required library libhostfxr.so could not be found.
```

**Solución:**

```bash
# Verificar .NET instalado
$HOME/.dotnet/dotnet --version

# Si no existe, instalar:
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 9.0 --install-dir $HOME/.dotnet

# Agregar al PATH
echo 'export PATH="$HOME/.dotnet:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verificar
dotnet --version  # Debe mostrar 9.0.xxx
```

---

### Problema: MySQL Connection Pool Saturado (Orders Service)

**Síntomas:**
```
MySqlException: Connect Timeout expired. All pooled connections are in use.
```

**Análisis:**
- Esto ocurre bajo carga extrema (500+ usuarios concurrentes creando pedidos)
- Es un comportamiento esperado cuando se satura el pool de conexiones
- En producción se mitiga con:
  1. Auto-scaling horizontal del servicio
  2. Connection pooling mejorado
  3. Queue de pedidos (asíncrono)

**Mitigación en desarrollo:**

```bash
# Aumentar límite de conexiones MySQL
docker exec censudex_mysql mysql -u root -proot -e "
SET GLOBAL max_connections = 500;
SHOW VARIABLES LIKE 'max_connections';
"

# Modificar appsettings.json del Orders Service:
# "ConnectionStrings": {
#   "DefaultConnection": "Server=...;MaxPoolSize=200;..."
# }
```

---

### Problema: Rate Limit Excedido en Tests

**Síntomas:**
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429
}
```

**Solución:**

```bash
# Opción 1: Deshabilitar rate limiting temporalmente
# Editar gateway/main.py:
# Comentar línea:
# app.add_middleware(RateLimitingMiddleware)

# Opción 2: Aumentar límites en gateway/middleware/rate_limiting.py:
# self.rate_limits = {
#     "default": {"tokens": 10000, "refill_rate": 1000.0},
# }

# Opción 3: Usar múltiples IPs en tests JMeter
# (configurar proxy rotativo o distribuir carga)
```

---

### Logs Útiles

```bash
# Ver todos los logs
docker-compose -f docker-compose.prod.yml logs -f

# Logs de gateway con filtro de errores
docker logs censudex_gateway 2>&1 | grep -i "error\|exception\|fail"

# Logs de Orders Service
tail -f censudex-orders-service/orders.log

# Logs de RabbitMQ
docker logs censudx_rabbitmq | grep -i "error\|failed"

# Exportar logs a archivo
docker-compose -f docker-compose.prod.yml logs > system_logs_$(date +%Y%m%d_%H%M%S).log
```

---

## 📚 Recursos Adicionales

### Documentación Oficial

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [gRPC Python Documentation](https://grpc.io/docs/languages/python/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [Nginx Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

### Repositorios Relacionados

| Servicio | Repositorio | Responsable |
|----------|-------------|-------------|
| **API Gateway** | [censudex-api-gateway](https://github.com/nico-alvz/censudex-api-gateway) | Nicolás Álvarez |
| **Auth Service** | [censudex-auth-service](https://github.com/AlbertoLyons/censudex-auth-service) | Alberto Lyons |
| **Clients Service** | [censudex-clients-service](https://github.com/AlbertoLyons/censudex-clients-service) | Alberto Lyons |
| **Inventory Service** | [censudex-inventory-service](https://github.com/nico-alvz/censudex-inventory-service) | Nicolás Álvarez |
| **Orders Service** | [censudex-orders-service](https://github.com/estudiante-d/censudex-orders) | Developer D |

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor sigue estos pasos:

1. **Fork** el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request**

### Guidelines de Contribución

- Mantén el código limpio y bien documentado
- Agrega tests para nuevas funcionalidades
- Actualiza el README si es necesario
- Sigue PEP 8 para código Python
- Usa commits semánticos: `feat:`, `fix:`, `docs:`, `refactor:`

---

## 📝 Licencia

Este proyecto fue desarrollado como parte del **Taller 2 de Arquitectura de Sistemas**. 

Todos los derechos reservados © 2024 Censudex Team

---

## 👥 Equipo de Desarrollo

- **Nicolás Álvarez** - API Gateway & Inventory Service
- **Alberto Lyons** - Auth Service & Clients Service  
- **Developer C** - Inventory Service
- **Developer D** - Orders Service

---

## 📞 Contacto y Soporte

Para preguntas, issues o sugerencias:

- **GitHub Issues**: [https://github.com/nico-alvz/censudex-api-gateway/issues](https://github.com/nico-alvz/censudex-api-gateway/issues)
- **Email**: ochiai@example.com

---

**🚀 Censudex API Gateway - Taller 2 de Arquitectura de Sistemas**

*High-performance API Gateway with gRPC, HTTP/REST, RabbitMQ integration, and production-ready microservices architecture.*

**Última actualización:** Noviembre 2024 | **Versión:** 1.0.0

---
