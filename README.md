# Censudex Microservices API Gateway

[![CI/CD](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/nico-alvz/censudex-api-gateway/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://github.com/nico-alvz/censudex-api-gateway)
[![Nginx](https://img.shields.io/badge/nginx-1.21-green)](https://github.com/nico-alvz/censudex-api-gateway)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)](https://github.com/nico-alvz/censudex-api-gateway)
[![Microservices](https://img.shields.io/badge/microservices-ready-purple)](https://github.com/nico-alvz/censudex-api-gateway)

> 🚀 **Censudex API Gateway** – Implementación de un gateway para una arquitectura de microservicios distribuida. Proyecto desarrollado como parte de un taller de arquitectura de sistemas.

---

## 🏗️ Arquitectura del Proyecto

### Descripción General
```
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx API Gateway                          │
│              (Load Balancer + HTTP/gRPC Router)                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                 FastAPI Gateway Service                        │
│           (Punto central de comunicación)                      │
│  • Authentication & Authorization (JWT)                        │
│  • Request Routing & Protocol Translation                      │
│  • Rate Limiting & Security Headers                            │
│  • Service Discovery & Health Checks                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──┐    ┌──────▼──────┐    ┌───▼─────────┐
│ Services │    │ RabbitMQ    │    │   Redis     │
│(Custom)  │    │(Async Msg)  │    │ (Caching)   │
│          │    │   Queue     │    │             │
└──────────┘    └─────────────┘    └─────────────┘
```

---

## 🧩 Descripción del Proyecto

**Censudex** es una empresa del rubro retail que está migrando de un sistema monolítico a una arquitectura basada en microservicios.  
El **API Gateway** actúa como punto único de entrada, gestionando autenticación, ruteo, balanceo de carga y comunicación entre servicios distribuidos.

### Objetivos del Proyecto
- ✅ Implementar una **arquitectura de microservicios** modular y escalable  
- ✅ Centralizar autenticación, ruteo y seguridad mediante **API Gateway Pattern**  
- ✅ Soportar **comunicación síncrona (HTTP/gRPC)** y **asíncrona (RabbitMQ)**  
- ✅ Facilitar el **descubrimiento y monitoreo de servicios**  

---

## 🧱 Servicios Disponibles

| Servicio | Responsable | Base de Datos | Puerto | Estado | Endpoints |
|----------|--------------|---------------|--------|---------|------------|
| **Clients Service** | Alberto Lyons | PostgreSQL | 5000 | ✅ Implementado | `/clients` |
| **Auth Service** | Alberto Lyons | No utiliza | 5001 | ✅ Implementado | `/auth` |
| **Products Service** | Developer B | MongoDB (Atlas) | 8005 | 🔄 En desarrollo | `/products` |
| **Inventory Service** | Developer C | PostgreSQL (Supabase) | 8001 | ✅ Implementado | `/inventory` |
| **Orders Service** | Developer D | MySQL (Railway) | 5206 | ✅ Implementado | `/orders` |

---

## ⚙️ Comunicación entre Servicios

### Síncrona (HTTP/gRPC)
- **Gateway ↔ Auth Service**: HTTP (autenticación)
- **Gateway ↔ Servicios**: gRPC (mayor rendimiento)
- **Validaciones en tiempo real**: para operaciones críticas

### Asíncrona (RabbitMQ)
- **Order Created → Inventory** (descontar stock)
- **Low Stock → Notifications**
- **Order Status → Email Service**

---

## 🧾 Endpoints Clave

#### Clients Service
```http
POST   /api/clients
GET    /api/clients
GET    /api/clients/{id}
PATCH  /api/clients/{id}
DELETE /api/clients/{id}
```
#### Auth Service
```http
POST   /api/login
GET    /api/validate-token
POST   /api/logout
```

#### Products Service
```http
POST   /api/v1/products
GET    /api/v1/products
GET    /api/v1/products/{id}
PATCH  /api/v1/products/{id}
DELETE /api/v1/products/{id}
```

#### Inventory Service
```http
GET    /api/v1/inventory
GET    /api/v1/inventory/{id}
PATCH  /api/v1/inventory/{id}
```

#### Orders Service
```http
POST   /api/v1/orders
GET    /api/v1/orders
GET    /api/v1/orders/{id}
GET    /api/v1/orders/user/{id}
PUT    /api/v1/orders/{id}/status
PATCH  /api/v1/orders/{id}
```

---

## 🔒 Seguridad y Validaciones

- **JWT Tokens**: autenticación basada en tokens  
- **Role-based Access**: permisos según tipo de usuario  
- **Validaciones**: email, password, edad, stock  
- **Rutas protegidas**: inventario, pedidos, usuarios  

---

## 🐳 Quick Start

### Requisitos Previos
- Docker & Docker Compose  
- Git  
- curl (para pruebas rápidas)

### Instalación
```bash
git clone https://github.com/nico-alvz/censudex-api-gateway.git
cd censudex-api-gateway
docker-compose up -d
```

### Acceso
- **API Gateway (Nginx)** → http://localhost:80  
- **FastAPI Gateway Service** → http://localhost:8000  
- **Swagger Docs** → http://localhost:8000/docs  
- **RabbitMQ Management** → http://localhost:15672  

---

## 🚀 Características Principales

- Autenticación JWT y rate limiting  
- Balanceo de carga con Nginx  
- Comunicación síncrona/asíncrona entre servicios  
- Integración con RabbitMQ y Redis  
- Arquitectura extensible y modular  

---

## 📁 Estructura del Proyecto

```
censudex-api-gateway/
├── gateway/
│   ├── main.py
│   ├── auth/
│   ├── middleware/
│   └── routes/
├── services/
│   ├── inventory/
│   ├── auth-stub/
│   ├── user-stub/
│   └── order-stub/
├── nginx/
│   ├── nginx.conf
│   └── sites/
├── tests/
├── docker-compose.yml
└── scripts/
```

---

## 🧪 Testing

```bash
./scripts/run-tests.sh
```

Ejemplos de pruebas:
```bash
curl -X GET http://localhost/api/v1/inventory/health
curl -X POST http://localhost/api/v1/auth/login -d '{"username":"test","password":"test"}'
```

---

## 🔄 CI/CD

Pipeline automatizado que incluye:
1. Linting y formateo  
2. Tests unitarios e integración  
3. Build de contenedores Docker  
4. Deploy automatizado  

---

## 🔗 Repositorios Relacionados

| Servicio | Repositorio |
|-----------|-------------|
| **Gateway** | [censudex-api-gateway](https://github.com/nico-alvz/censudex-api-gateway) |
| **Inventory** | [censudex-inventory-service](https://github.com/nico-alvz/censudex-inventory-service) |
| **Clients** | [censudex-clients](https://github.com/AlbertoLyons/censudex-clients-service) |
| **Products** | [censudex-products](https://github.com/estudiante-b/censudex-products) |
| **Orders** | [censudex-orders](https://github.com/estudiante-d/censudex-orders) |
| **Auth** | [censudex-auth](https://github.com/AlbertoLyons/censudex-auth-service) |


---

**🧠 Taller de Arquitectura de Sistemas – Censudex Microservices Platform**  
**API Gateway distribuido, escalable y listo para producción.** 🚀
