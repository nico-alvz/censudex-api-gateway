"""
Product Service Stub for Censudx API Gateway
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Censudx Product Service (Stub)",
    description="🛍️ Product catalog service stub",
    version="1.0.0-stub"
)

class Product(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    category: str
    in_stock: bool

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service-stub", "version": "1.0.0-stub"}

@app.get("/api/v1/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get product by ID"""
    return Product(
        product_id=product_id,
        name=f"Product {product_id}",
        description=f"Description for product {product_id}",
        price=29.99,
        category="electronics",
        in_stock=True
    )

@app.get("/api/v1/products/", response_model=List[Product])
async def list_products():
    """List all products"""
    return [
        Product(
            product_id=f"prod-{i:03d}",
            name=f"Product {i}",
            description=f"High-quality product {i}",
            price=float(i * 9.99),
            category="electronics" if i % 2 == 0 else "accessories",
            in_stock=i % 3 != 0
        )
        for i in range(1, 21)
    ]