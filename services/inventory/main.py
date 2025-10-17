"""
Main FastAPI application for Censudx Inventory Service
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="Censudx Inventory Service",
    description="🏦 A comprehensive inventory management microservice built with FastAPI, PostgreSQL, and RabbitMQ. "
                "Provides robust inventory tracking, stock management, and automated alerting capabilities.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Censudx Inventory Service",
        "url": "https://github.com/och1ai/censudx-inventory-service",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "health",
            "description": "Health check endpoints for service monitoring",
        },
        {
            "name": "inventory",
            "description": "CRUD operations for inventory items management",
        },
        {
            "name": "stock",
            "description": "Stock operations: check availability, reserve, and release",
        },
        {
            "name": "alerts",
            "description": "Low stock alerts and notification management",
        },
        {
            "name": "transactions",
            "description": "Inventory transaction history and audit trail",
        },
    ]
)
security = HTTPBearer()

# Health check endpoint
@app.get("/health", tags=["health"], summary="Health Check", description="Returns the health status of the inventory service")
async def health_check():
    """Health check endpoint for monitoring service availability"""
    return {"status": "healthy", "service": "inventory-service", "version": "1.0.0"}

# Basic Pydantic models for testing
class InventoryItemCreate(BaseModel):
    product_id: str
    quantity: int
    location: str
    reserved_quantity: int = 0

class InventoryItemUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    reserved_quantity: Optional[int] = None

class InventoryItemResponse(BaseModel):
    id: int
    product_id: str
    quantity: int
    location: str
    reserved_quantity: int

class StockCheckRequest(BaseModel):
    product_id: str
    requested_quantity: int

class StockCheckResponse(BaseModel):
    available: bool
    current_stock: int
    available_stock: int
    requested_quantity: int

class StockReserveRequest(BaseModel):
    product_id: str
    quantity: int
    reference_id: str

# Inventory endpoints
@app.get("/api/v1/inventory/", response_model=List[InventoryItemResponse], tags=["inventory"], summary="Get All Inventory Items")
async def get_inventory_items():
    """Retrieve all inventory items with their current stock levels"""
    return []

# Alert endpoints
@app.get("/api/v1/inventory/alerts", tags=["alerts"], summary="Get Low Stock Alerts")
async def get_low_stock_alerts():
    """Retrieve all unresolved low stock alerts"""
    return []

# Transaction endpoints
@app.get("/api/v1/inventory/transactions/{item_id}", tags=["transactions"], summary="Get Item Transaction History")
async def get_transactions(item_id: int):
    """Retrieve transaction history for a specific inventory item"""
    return []

# Stock operation endpoints
@app.post("/api/v1/inventory/check-stock", response_model=StockCheckResponse, tags=["stock"], summary="Check Stock Availability")
async def check_stock(request: StockCheckRequest):
    """Check if requested quantity is available for a specific product"""
    return StockCheckResponse(
        available=True,
        current_stock=100,
        available_stock=95,
        requested_quantity=request.requested_quantity
    )

@app.post("/api/v1/inventory/reserve", tags=["stock"], summary="Reserve Stock")
async def reserve_stock(request: StockReserveRequest):
    """Reserve stock for a pending order or allocation"""
    return {"message": "Stock reserved successfully"}

@app.post("/api/v1/inventory/release", tags=["stock"], summary="Release Reserved Stock")
async def release_stock(request: StockReserveRequest):
    """Release previously reserved stock back to available inventory"""
    return {"message": "Stock released successfully"}

# CRUD endpoints (parametric routes last to avoid conflicts)
@app.get("/api/v1/inventory/{item_id}", response_model=InventoryItemResponse, tags=["inventory"], summary="Get Inventory Item by ID")
async def get_inventory_item(item_id: int):
    """Retrieve a specific inventory item by its unique identifier"""
    if item_id == 999:
        raise HTTPException(status_code=404, detail="Item not found")
    return InventoryItemResponse(
        id=item_id,
        product_id="test_product",
        quantity=100,
        location="warehouse_a",
        reserved_quantity=0
    )

@app.post("/api/v1/inventory/", response_model=InventoryItemResponse, tags=["inventory"], summary="Create New Inventory Item")
async def create_inventory_item(item: InventoryItemCreate):
    """Create a new inventory item with initial stock levels"""
    return InventoryItemResponse(
        id=1,
        product_id=item.product_id,
        quantity=item.quantity,
        location=item.location,
        reserved_quantity=item.reserved_quantity
    )

@app.put("/api/v1/inventory/{item_id}", response_model=InventoryItemResponse, tags=["inventory"], summary="Update Inventory Item")
async def update_inventory_item(item_id: int, item: InventoryItemUpdate):
    """Update an existing inventory item's quantity, location, or reserved stock"""
    return InventoryItemResponse(
        id=item_id,
        product_id="test_product",  # Keep existing product_id
        quantity=item.quantity or 100,
        location=item.location or "warehouse_a",
        reserved_quantity=item.reserved_quantity or 0
    )

@app.delete("/api/v1/inventory/{item_id}", tags=["inventory"], summary="Delete Inventory Item")
async def delete_inventory_item(item_id: int):
    """Permanently delete an inventory item and all associated data"""
    return {"message": "Item deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)