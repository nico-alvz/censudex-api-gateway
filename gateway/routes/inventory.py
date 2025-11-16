"""
Inventory Service gRPC Router
Handles routing requests to the Inventory Service via gRPC
"""

import logging
import grpc
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from typing import Optional, List
from pydantic import BaseModel

# Import gRPC stubs (compiled in Docker build at /app/pb2)
try:
    import pb2.inventory_pb2 as inventory_pb2
    import pb2.inventory_pb2_grpc as inventory_pb2_grpc
except ImportError as e:
    logging.error(f"Failed to import inventory stubs: {e}")
    logging.error("Proto files must be compiled during Docker build")
    inventory_pb2 = None
    inventory_pb2_grpc = None

logger = logging.getLogger(__name__)
security = HTTPBearer()
inventory_router = APIRouter(
    prefix="/api/v1/inventory",
    tags=["inventory"],
)

# Pydantic models for HTTP API
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

class InventoryCreateRequest(BaseModel):
    product_id: str
    quantity: int
    location: str
    reserved_quantity: int = 0

class InventoryUpdateRequest(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    reserved_quantity: Optional[int] = None

# gRPC Channel Cache
_grpc_channel = None

def get_grpc_channel():
    """Get or create gRPC channel to inventory service (insecure for local communication)"""
    global _grpc_channel
    if _grpc_channel is None:
        logger.info("Creating gRPC channel to inventory:50051 (insecure)")
        try:
            _grpc_channel = grpc.aio.insecure_channel("inventory:50051")
            logger.info("gRPC channel created successfully")
        except Exception as e:
            logger.error(f"Failed to create gRPC channel: {e}")
            raise
    return _grpc_channel

async def get_inventory_stub():
    """Get inventory service stub"""
    if inventory_pb2_grpc is None:
        logger.error("inventory_pb2_grpc module not available")
        raise HTTPException(
            status_code=503,
            detail="gRPC stubs not available - proto compilation failed"
        )
    try:
        channel = get_grpc_channel()
        return inventory_pb2_grpc.InventoryServiceStub(channel)
    except Exception as e:
        logger.error(f"Failed to get inventory stub: {e}")
        raise HTTPException(status_code=503, detail="Failed to connect to inventory service")

# ============================================================================
# Inventory gRPC Endpoints
# ============================================================================

@inventory_router.get("/", response_model=List[InventoryItemResponse], summary="List Inventory Items")
async def list_inventory(
    limit: int = 10,
    offset: int = 0,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """List all inventory items via gRPC"""
    try:
        stub = await get_inventory_stub()
        request = inventory_pb2.ListInventoryRequest(limit=limit, offset=offset)
        response = await stub.ListInventory(request)
        
        items = [
            InventoryItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                location=item.location,
                reserved_quantity=item.reserved_quantity
            )
            for item in response.items
        ]
        logger.info(f"gRPC: Listed {len(items)} inventory items")
        return items
    except grpc.RpcError as e:
        logger.error(f"gRPC error listing inventory: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@inventory_router.get("/{item_id}", response_model=InventoryItemResponse, summary="Get Inventory Item")
async def get_inventory_item(
    item_id: int,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """Get specific inventory item by ID via gRPC"""
    try:
        # Fetch all items and filter by ID (since proto doesn't have GetById by ID)
        stub = await get_inventory_stub()
        request = inventory_pb2.ListInventoryRequest(limit=1000, offset=0)
        response = await stub.ListInventory(request)
        
        for item in response.items:
            if item.id == item_id:
                logger.info(f"gRPC: Got inventory item {item_id}")
                return InventoryItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    location=item.location,
                    reserved_quantity=item.reserved_quantity
                )
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    except HTTPException:
        raise
    except grpc.RpcError as e:
        logger.error(f"gRPC error getting inventory item: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except Exception as e:
        logger.error(f"Error getting inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@inventory_router.post("/", response_model=InventoryItemResponse, summary="Create Inventory Item")
async def create_inventory(
    item: InventoryCreateRequest,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """Create new inventory item via gRPC"""
    try:
        stub = await get_inventory_stub()
        request = inventory_pb2.CreateInventoryRequest(
            product_id=item.product_id,
            quantity=item.quantity,
            location=item.location,
            reserved_quantity=item.reserved_quantity
        )
        response = await stub.CreateInventory(request)
        
        logger.info(f"gRPC: Created inventory item for {item.product_id}")
        return InventoryItemResponse(
            id=response.id,
            product_id=response.product_id,
            quantity=response.quantity,
            location=response.location,
            reserved_quantity=response.reserved_quantity
        )
    except grpc.RpcError as e:
        logger.error(f"gRPC error creating inventory: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except Exception as e:
        logger.error(f"Error creating inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@inventory_router.put("/{item_id}", response_model=InventoryItemResponse, summary="Update Inventory Item")
async def update_inventory(
    item_id: int,
    item: InventoryUpdateRequest,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """Update inventory item via gRPC"""
    try:
        stub = await get_inventory_stub()
        
        # Build update request with provided fields
        request = inventory_pb2.UpdateInventoryRequest(id=item_id)
        if item.quantity is not None:
            request.quantity = item.quantity
        if item.location is not None:
            request.location = item.location
        if item.reserved_quantity is not None:
            request.reserved_quantity = item.reserved_quantity
        
        response = await stub.UpdateInventory(request)
        
        logger.info(f"gRPC: Updated inventory item {item_id}")
        return InventoryItemResponse(
            id=response.id,
            product_id=response.product_id,
            quantity=response.quantity,
            location=response.location,
            reserved_quantity=response.reserved_quantity
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        logger.error(f"gRPC error updating inventory: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@inventory_router.delete("/{item_id}", summary="Delete Inventory Item")
async def delete_inventory(
    item_id: int,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """Delete inventory item via gRPC"""
    try:
        stub = await get_inventory_stub()
        request = inventory_pb2.DeleteInventoryRequest(id=item_id)
        await stub.DeleteInventory(request)
        
        logger.info(f"gRPC: Deleted inventory item {item_id}")
        return {"message": f"Item {item_id} deleted successfully"}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        logger.error(f"gRPC error deleting inventory: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@inventory_router.post("/check-stock", response_model=StockCheckResponse, summary="Check Stock Availability")
async def check_stock_grpc(
    request: StockCheckRequest,
    credentials: Optional[HTTPBearer] = Depends(security)
):
    """Check stock availability via gRPC"""
    try:
        stub = await get_inventory_stub()
        grpc_request = inventory_pb2.StockCheckRequest(
            product_id=request.product_id,
            requested_quantity=request.requested_quantity
        )
        grpc_response = await stub.CheckStock(grpc_request)
        
        logger.info(f"gRPC: Checked stock for {request.product_id}")
        return StockCheckResponse(
            available=grpc_response.available,
            current_stock=grpc_response.current_stock,
            available_stock=grpc_response.available_stock,
            requested_quantity=grpc_response.requested_quantity
        )
    except grpc.RpcError as e:
        logger.error(f"gRPC error checking stock: {e.code()} {e.details()}")
        raise HTTPException(status_code=503, detail=f"Inventory service error: {e.details()}")
    except Exception as e:
        logger.error(f"Error checking stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))
