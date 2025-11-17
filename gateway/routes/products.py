from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from gateway.services.products_client import ProductsClient
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import ParseDict
from pb2 import products_pb2

router = APIRouter(prefix="/api/v1/products", tags=["products"])

# Host/port se pueden leer de variables de entorno si lo deseas
client = ProductsClient(host="products-service", port=50051)

def proto_product_to_dict(proto_msg):
    # usa MessageToDict para convertir Timestamp a strings; preserveProtoFieldName FALSE por default
    return MessageToDict(proto_msg, preserving_proto_field_name=False)

@router.get("/", response_class=JSONResponse)
def list_products():
    try:
        resp = client.list_products()
        products = [proto_product_to_dict(p) for p in resp.products]
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}", response_class=JSONResponse)
def get_product(product_id: str = Path(..., description="UUID del producto")):
    try:
        resp = client.get_product(product_id)
        return proto_product_to_dict(resp)
    except Exception as e:
        # grpc RpcError -> contiene detalles; simplificamos
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_class=JSONResponse)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    description: str | None = Form(None)
):
    try:
        content = await image.read()
        resp = client.create_product(
            name=name,
            description=description,
            price=price,
            category=category,
            image_bytes=content,
            image_file_name=image.filename,
            image_content_type=image.content_type
        )
        return proto_product_to_dict(resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{product_id}", response_class=JSONResponse)
async def update_product(
    product_id: str = Path(...),
    name: str | None = Form(None),
    price: float | None = Form(None),
    category: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None)
):
    try:
        image_bytes = None
        image_filename = None
        image_content_type = None
        if image is not None:
            image_bytes = await image.read()
            image_filename = image.filename
            image_content_type = image.content_type

        resp = client.update_product(
            id_=product_id,
            name=name,
            description=description,
            price=price,
            category=category,
            image_bytes=image_bytes,
            image_file_name=image_filename,
            image_content_type=image_content_type
        )
        return proto_product_to_dict(resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id}", response_class=JSONResponse)
def delete_product(product_id: str = Path(...)):
    try:
        resp = client.delete_product(product_id)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
