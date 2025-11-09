import grpc
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from google.protobuf.json_format import MessageToDict
from pb2 import order_pb2, order_pb2_grpc

class OrderItemPayload(BaseModel):
    productId: str
    productName: str
    quantity: int
    unitPrice: float

class CreateOrderPayload(BaseModel):
    userId: str
    userName: str
    address: str
    userEmail: str
    items: list[OrderItemPayload]

class ChangeOrderStatePayload(BaseModel):
    identifier: str
    orderStatus: str
    trackingNumber: str | None = ""
    userEmail: str | None

class CancelOrderPayload(BaseModel):
    identifier: str
    userEmail: str
    reason: str | None = ""



def create_orders_router(service_url: str) -> APIRouter:

    router = APIRouter()
    

    grpc_target_url = service_url.replace("http://", "").replace("https://", "")


    @router.post("/")
    def create_order(order: CreateOrderPayload):
     
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)

                grpc_items = []
                for i in order.items:
                    item = order_pb2.OrderItemRequest(
                        product_id=i.productId,
                        product_name=i.productName,
                        quantity=i.quantity,
                        unit_price=i.unitPrice
                    )
                    grpc_items.append(item)
                
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
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @router.get("/status/{identifier}")
    def get_order_status(identifier: str):
    
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

    @router.put("/change-state")
    def change_order_state(data: ChangeOrderStatePayload):
        
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.ChangeOrderStateRequest(
                    identifier=data.identifier,
                    order_status=data.orderStatus,
                    tracking_number=data.trackingNumber,
                    UserEmail=data.userEmail
                )
                
                response = stub.ChangeOrderState(request, timeout=5)

                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @router.post("/cancel")
    def cancel_order(data: CancelOrderPayload):
  
        try:
            with grpc.insecure_channel(grpc_target_url) as channel:
                stub = order_pb2_grpc.OrderServiceStub(channel)
                
                request = order_pb2.CancelOrderRequest(
                    identifier=data.identifier,
                    UserEmail=data.userEmail,
                    reason=data.reason
                )
                
                response = stub.CancelOrder(request, timeout=5)
                
        
                return MessageToDict(response)
        
        except grpc.RpcError as e:
            raise HTTPException(status_code=503, detail=f"Service error ({e.code()}): {e.details()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    @router.get("/user/{userId}")
    def get_user_orders(
        userId: str, 
        orderIdentifier: str | None = Query(None),
        initialDate: str | None = Query(None),
        finishDate: str | None = Query(None)
    ):
      
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


    @router.get("/admin")
    def get_admin_orders(
        userIdentifier: str | None = Query(None),
        orderIdentifier: str | None = Query(None),
        initialDate: str | None = Query(None),
        finishDate: str | None = Query(None)
    ):
       
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