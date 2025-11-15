import grpc
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from google.protobuf.json_format import MessageToDict
from pb2 import order_pb2, order_pb2_grpc
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends
from gateway.auth.authorize import authorize

# --------------------------- #
#        MODELOS Pydantic     #
# --------------------------- #

# Representa un ítem dentro de una orden
class OrderItemPayload(BaseModel):
    productId: str
    productName: str
    quantity: int
    unitPrice: float

# Payload del endpoint para crear una orden completa
class CreateOrderPayload(BaseModel):
    userId: str
    userName: str
    address: str
    userEmail: str
    items: list[OrderItemPayload]

# Payload para cambiar el estado de una orden
class ChangeOrderStatePayload(BaseModel):
    orderStatus: str
    trackingNumber: str | None = ""

# Payload para cancelar una orden
class CancelOrderPayload(BaseModel):
    reason: str | None = ""


# -------------------------------------- #
#   Router principal que consume gRPC    #
# -------------------------------------- #
def create_orders_router(service_url: str) -> APIRouter:

    router = APIRouter()
    
    # Se obtiene solo el host y puerto removiendo http/https
    grpc_target_url = service_url.replace("http://", "").replace("https://", "")

    # -----------------------------------------------------------
    # POST /orders → Crear una orden consumiendo el microservicio gRPC
    # -----------------------------------------------------------
    @router.post("/orders")
    def create_order(order: CreateOrderPayload):
        """
        Crea una nueva orden enviando una solicitud gRPC al servicio OrderService.
        Convierte los ítems recibidos vía HTTP en objetos gRPC y envía la solicitud
        CreateOrderRequest. Devuelve la respuesta transformada a diccionario.
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)

                # Construcción de los items gRPC
                grpc_items = []
                for i in order.items:
                    item = order_pb2.OrderItemRequest(
                        product_id=i.productId,
                        product_name=i.productName,
                        quantity=i.quantity,
                        unit_price=i.unitPrice
                    )
                    grpc_items.append(item)
                
                # Construcción de la solicitud gRPC
                request = order_pb2.CreateOrderRequest(
                    user_id=order.userId,
                    user_name=order.userName,
                    address=order.address,
                    UserEmail=order.userEmail,
                    items=grpc_items
                )

                response = stub.CreateOrder(request, timeout=5) 
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            # Error si el microservicio gRPC está caído o no responde
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # -------------------------------------------------------------------
    # GET /orders/{identifier} → Obtener el estado de una orden por ID
    # -------------------------------------------------------------------
    @router.get("/orders/{identifier}")
    def get_order_status(identifier: str):
        """
        Consulta el estado de una orden mediante el método gRPC GetOrderStatus.
        El parámetro puede ser ID o número de orden según el servicio gRPC.
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                request = order_pb2.GetOrderStatusRequest(identifier=identifier)
                
                response = stub.GetOrderStatus(request, timeout=5)
                
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # --------------------------------------------------------------------------
    # PUT /orders/{identifier}/status → Cambiar estado de una orden (Admin)
    # --------------------------------------------------------------------------
    @router.put("/orders/{identifier}/status")
    def change_order_state(identifier: str, data: ChangeOrderStatePayload, token: HTTPAuthorizationCredentials = Depends(authorize("Admin"))):
        """
        Cambia el estado de una orden (por ejemplo: 'Shipped', 'Delivered').
        También permite adjuntar el número de seguimiento si aplica.
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.ChangeOrderStateRequest(
                    identifier=identifier,
                    order_status=data.orderStatus,
                    tracking_number=data.trackingNumber,
                )
                
                response = stub.ChangeOrderState(request, timeout=5)

                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # -------------------------------------------------------
    # PATCH /orders/{identifier} → Cancelar una orden
    # -------------------------------------------------------
    @router.patch("/orders/{identifier}")
    def cancel_order(identifier: str, data: CancelOrderPayload):
        """
        Cancela una orden indicando una razón. Envía CancelOrderRequest al servicio.
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.CancelOrderRequest(
                    identifier=identifier,
                    reason=data.reason
                )
                
                response = stub.CancelOrder(request, timeout=5)
                
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # -------------------------------------------------------------------------
    # GET /orders/user/{userId} → Obtener órdenes de un usuario con filtros
    # -------------------------------------------------------------------------
    @router.get("/orders/user/{userId}")
    def get_user_orders(
        userId: str, 
        orderIdentifier: str | None = Query(None),
        initialDate: str | None = Query(None),
        finishDate: str | None = Query(None)
    ):
        """
        Obtiene las órdenes de un usuario, permitiendo filtros opcionales como:
        - Identificador de orden
        - Fecha inicial y final
        Llama al método gRPC GetUserOrders.
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.GetUserOrdersRequest(
                    user_id=userId,
                    order_identifier=orderIdentifier,
                    initial_date=initialDate,
                    finish_date=finishDate
                )
                
                response = stub.GetUserOrders(request, timeout=5)
                
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    # -------------------------------------------------------------------------
    # GET /orders → Consultar órdenes para admins con filtros
    # -------------------------------------------------------------------------
    @router.get("/orders")
    def get_admin_orders(
        userIdentifier: str | None = Query(None),
        orderIdentifier: str | None = Query(None),
        initialDate: str | None = Query(None),
        finishDate: str | None = Query(None),
        token: HTTPAuthorizationCredentials = Depends(authorize("Admin"))
    ):
        """
        Obtiene órdenes para uso administrativo.  
        Permite múltiples filtros opcionales:
        - Usuario
        - Identificador de orden
        - Rango de fechas
        """
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.GetAdminOrdersRequest(
                    user_identifier=userIdentifier,
                    order_identifier=orderIdentifier,
                    initial_date=initialDate,
                    finish_date=finishDate
                )
                
                response = stub.GetAdminOrders(request, timeout=5)
                
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
