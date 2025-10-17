"""
RabbitMQ messaging service for inventory operations
"""

import aio_pika
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RabbitMQService:
    def __init__(self, connection_url: str = "amqp://guest:guest@localhost:5672/"):
        self.connection_url = connection_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.published_messages = []  # For testing purposes

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            # In development/testing, we'll continue without RabbitMQ
            self.connection = None
            self.channel = None

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a queue"""
        try:
            # Add message to test list for testing purposes
            self.published_messages.append({
                "queue": queue_name,
                "message": message,
                "timestamp": datetime.now()
            })
            
            # If no connection, just log and return success (for testing)
            if not self.connection or not self.channel:
                logger.warning(f"No RabbitMQ connection, message logged locally: {queue_name}")
                return True

            # Declare queue
            queue = await self.channel.declare_queue(queue_name, durable=True)
            
            # Publish message
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
            
            logger.info(f"Message published to queue {queue_name}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {e}")
            return False

    async def publish_low_stock_alert(self, inventory_item_id: int, product_id: str, 
                                    current_quantity: int, threshold: int):
        """Publish a low stock alert"""
        message = {
            "event_type": "low_stock_alert",
            "inventory_item_id": inventory_item_id,
            "product_id": product_id,
            "current_quantity": current_quantity,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat(),
            "severity": "warning" if current_quantity > 0 else "critical"
        }
        return await self.publish_message("low_stock_alerts", message)

    async def publish_stock_validation(self, product_id: str, requested_quantity: int, 
                                     available_quantity: int, order_id: str):
        """Publish a stock validation message"""
        message = {
            "event_type": "stock_validation",
            "product_id": product_id,
            "requested_quantity": requested_quantity,
            "available_quantity": available_quantity,
            "order_id": order_id,
            "timestamp": datetime.now().isoformat(),
            "validation_result": available_quantity >= requested_quantity
        }
        return await self.publish_message("stock_validation", message)

    async def publish_inventory_update(self, inventory_item_id: int, product_id: str,
                                     old_quantity: int, new_quantity: int, 
                                     transaction_type: str):
        """Publish an inventory update message"""
        message = {
            "event_type": "inventory_update",
            "inventory_item_id": inventory_item_id,
            "product_id": product_id,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "quantity_change": new_quantity - old_quantity,
            "transaction_type": transaction_type,
            "timestamp": datetime.now().isoformat()
        }
        return await self.publish_message("inventory_updates", message)


# Global instance
messaging_service = RabbitMQService()

async def get_messaging_service() -> RabbitMQService:
    """Dependency to get messaging service"""
    if not messaging_service.connection:
        await messaging_service.connect()
    return messaging_service