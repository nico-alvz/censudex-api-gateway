# gateway/services/products_client.py
import time
import grpc
from typing import Optional
from pb2 import products_pb2, products_pb2_grpc

DEFAULT_MAX_MSG = 20 * 1024 * 1024  # 20 MB

class ProductsClient:
    
    def __init__(self, host: str = "products-service", port: int = 50051, max_message_length: int = DEFAULT_MAX_MSG, retry_seconds: int = 5, retry_attempts: int = 5):
        self.target = f"{host}:{port}"
        self.options = [
            ('grpc.max_receive_message_length', max_message_length),
            ('grpc.max_send_message_length', max_message_length),
        ]
        self.channel = grpc.insecure_channel(self.target, options=self.options)
        self.stub = products_pb2_grpc.ProductsServiceStub(self.channel)

        # Espera simple hasta que el canal esté listo (retry)
        attempt = 0
        while attempt < retry_attempts:
            try:
                grpc.channel_ready_future(self.channel).result(timeout=5)
                break
            except Exception:
                attempt += 1
                time.sleep(retry_seconds)
        # no raise aquí; la llamada fallará con RpcError si no está listo

    def list_products(self):
        req = products_pb2.ListProductsRequest()
        return self.stub.ListProducts(req)

    def get_product(self, id_: str):
        req = products_pb2.GetProductRequest(id=id_)
        return self.stub.GetProduct(req)

    def create_product(self, name: str, description: Optional[str], price: float, category: str,
                       image_bytes: Optional[bytes] = None, image_file_name: Optional[str] = None,
                       image_content_type: Optional[str] = None):
        # Construye el request sólo con los campos que tenemos
        kwargs = dict(
            name=name,
            price=price,
            category=category,
        )
        if description is not None:
            kwargs["description"] = description
        if image_bytes is not None:
            kwargs["image"] = image_bytes
        if image_file_name is not None:
            kwargs["imageFileName"] = image_file_name
        if image_content_type is not None:
            kwargs["imageContentType"] = image_content_type

        req = products_pb2.CreateProductRequest(**kwargs)
        return self.stub.CreateProduct(req)

    def update_product(self, id_: str, name: Optional[str] = None, description: Optional[str] = None,
                       price: Optional[float] = None, category: Optional[str] = None,
                       image_bytes: Optional[bytes] = None, image_file_name: Optional[str] = None,
                       image_content_type: Optional[str] = None):
        kwargs = {"id": id_}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if price is not None:
            kwargs["price"] = price
        if category is not None:
            kwargs["category"] = category
        if image_bytes is not None:
            kwargs["image"] = image_bytes
        if image_file_name is not None:
            kwargs["imageFileName"] = image_file_name
        if image_content_type is not None:
            kwargs["imageContentType"] = image_content_type

        req = products_pb2.UpdateProductRequest(**kwargs)
        return self.stub.UpdateProduct(req)

    def delete_product(self, id_: str):
        req = products_pb2.DeleteProductRequest(id=id_)
        return self.stub.DeleteProduct(req)

    def close(self):
        self.channel.close()
