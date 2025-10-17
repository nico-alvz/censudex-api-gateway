"""
Order Service Stub for Censudx API Gateway
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Censudx Order Service (Stub)",
    description="📦 Order processing service stub",
    version="1.0.0-stub"
)

class Order(BaseModel):
    order_id: int
    customer_id: int
    status: str
    total_amount: float
    created_at: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "order-service-stub", "version": "1.0.0-stub"}

@app.get("/api/v1/orders/{order_id}", response_model=Order)
async def get_order(order_id: int):
    """Get order by ID"""
    return Order(
        order_id=order_id,
        customer_id=1,
        status="completed",
        total_amount=99.99,
        created_at=datetime.utcnow().isoformat()
    )

@app.get("/api/v1/orders/", response_model=List[Order])
async def list_orders():
    """List all orders"""
    return [
        Order(
            order_id=i,
            customer_id=i,
            status="completed" if i % 2 == 0 else "pending",
            total_amount=float(i * 10.99),
            created_at=datetime.utcnow().isoformat()
        )
        for i in range(1, 11)
    ]