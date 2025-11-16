"""
RabbitMQ Messaging Service
Handles asynchronous publishing and consuming of messages for inventory events
"""

import json
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
import traceback

logger = logging.getLogger(__name__)


class MessageSchema:
    """Defines message schemas for different event types"""
    
    @staticmethod
    def inventory_update(
        item_id: int,
        product_id: str,
        old_quantity: int,
        new_quantity: int,
        transaction_type: str,
        location: str = "unknown"
    ) -> Dict[str, Any]:
        """Schema for inventory update events"""
        return {
            "event_id": f"inventory_update_{item_id}_{datetime.utcnow().timestamp()}",
            "event_type": "inventory_updated",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "inventory-service",
            "version": "1.0.0",
            "payload": {
                "inventory_item_id": item_id,
                "product_id": product_id,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "quantity_change": new_quantity - old_quantity,
                "transaction_type": transaction_type,  # "IN", "OUT", "RETURN"
                "location": location
            }
        }
    
    @staticmethod
    def low_stock_alert(
        item_id: int,
        product_id: str,
        current_quantity: int,
        threshold: int,
        location: str = "unknown"
    ) -> Dict[str, Any]:
        """Schema for low stock alert events"""
        return {
            "event_id": f"low_stock_{item_id}_{datetime.utcnow().timestamp()}",
            "event_type": "low_stock_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "inventory-service",
            "version": "1.0.0",
            "severity": "critical" if current_quantity == 0 else "warning",
            "payload": {
                "inventory_item_id": item_id,
                "product_id": product_id,
                "current_quantity": current_quantity,
                "threshold": threshold,
                "location": location,
                "action_required": current_quantity <= threshold
            }
        }
    
    @staticmethod
    def stock_validation(
        product_id: str,
        requested_quantity: int,
        available_quantity: int,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schema for stock validation events"""
        return {
            "event_id": f"stock_validation_{product_id}_{datetime.utcnow().timestamp()}",
            "event_type": "stock_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "inventory-service",
            "version": "1.0.0",
            "payload": {
                "product_id": product_id,
                "requested_quantity": requested_quantity,
                "available_quantity": available_quantity,
                "order_id": order_id,
                "validation_result": available_quantity >= requested_quantity
            }
        }
    
    @staticmethod
    def stock_reserved(
        product_id: str,
        reserved_quantity: int,
        available_quantity: int,
        order_id: str,
        reservation_id: str
    ) -> Dict[str, Any]:
        """Schema for stock reservation events"""
        return {
            "event_id": f"stock_reserved_{reservation_id}_{datetime.utcnow().timestamp()}",
            "event_type": "stock_reserved",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "inventory-service",
            "version": "1.0.0",
            "payload": {
                "product_id": product_id,
                "reserved_quantity": reserved_quantity,
                "available_quantity": available_quantity,
                "order_id": order_id,
                "reservation_id": reservation_id
            }
        }


class RabbitMQService:
    """
    Service for managing RabbitMQ connections and messaging
    Handles publishing and consuming events with retry logic
    """
    
    # Queue definitions
    QUEUES = {
        "inventory_updates": {
            "name": "inventory_updates",
            "durable": True,
            "exchange": "inventory_events",
            "routing_key": "inventory.updated"
        },
        "low_stock_alerts": {
            "name": "low_stock_alerts",
            "durable": True,
            "exchange": "inventory_events",
            "routing_key": "inventory.low_stock"
        },
        "stock_validation": {
            "name": "stock_validation",
            "durable": True,
            "exchange": "inventory_events",
            "routing_key": "inventory.validation"
        },
        "stock_reserved": {
            "name": "stock_reserved",
            "durable": True,
            "exchange": "inventory_events",
            "routing_key": "inventory.reserved"
        }
    }
    
    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"):
        """
        Initialize RabbitMQ service
        
        Args:
            rabbitmq_url: Connection URL for RabbitMQ
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self.consumers: Dict[str, Callable] = {}
        self.max_retries = 5
        self.retry_delay = 2  # seconds
    
    def connect(self) -> bool:
        """
        Establish connection to RabbitMQ with retry logic
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt + 1}/{self.max_retries})")
                
                # Parse RabbitMQ URL to extract connection parameters
                import urllib.parse
                parsed = urllib.parse.urlparse(self.rabbitmq_url)
                
                credentials = pika.PlainCredentials(
                    parsed.username or 'guest',
                    parsed.password or 'guest'
                )
                parameters = pika.ConnectionParameters(
                    host=parsed.hostname or 'rabbitmq',
                    port=parsed.port or 5672,
                    virtual_host=parsed.path[1:] if parsed.path and len(parsed.path) > 1 else '/',
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=2,
                    blocked_connection_timeout=300
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare exchange
                self.channel.exchange_declare(
                    exchange='inventory_events',
                    exchange_type='topic',
                    durable=True
                )
                
                # Declare all queues
                for queue_config in self.QUEUES.values():
                    self.channel.queue_declare(
                        queue=queue_config['name'],
                        durable=queue_config['durable']
                    )
                    self.channel.queue_bind(
                        exchange=queue_config['exchange'],
                        queue=queue_config['name'],
                        routing_key=queue_config['routing_key']
                    )
                
                logger.info("Successfully connected to RabbitMQ")
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ: {e}")
                if attempt < self.max_retries - 1:
                    asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to connect to RabbitMQ after {self.max_retries} attempts")
                    return False
        
        return False
    
    def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        routing_key: Optional[str] = None
    ) -> bool:
        """
        Publish a message to RabbitMQ queue
        
        Args:
            queue_name: Target queue name
            message: Message content
            routing_key: Optional routing key (uses queue default if not provided)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel:
                logger.error("RabbitMQ channel not connected")
                return False
            
            queue_config = self.QUEUES.get(queue_name)
            if not queue_config:
                logger.error(f"Unknown queue: {queue_name}")
                return False
            
            routing_key = routing_key or queue_config['routing_key']
            message_body = json.dumps(message, default=str)
            
            self.channel.basic_publish(
                exchange=queue_config['exchange'],
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    timestamp=int(datetime.utcnow().timestamp())
                )
            )
            
            logger.debug(f"Published message to {queue_name}: {message['event_type']}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            traceback.print_exc()
            return False
    
    def publish_inventory_update(
        self,
        item_id: int,
        product_id: str,
        old_quantity: int,
        new_quantity: int,
        transaction_type: str,
        location: str = "unknown"
    ) -> bool:
        """Publish inventory update event"""
        message = MessageSchema.inventory_update(
            item_id, product_id, old_quantity, new_quantity,
            transaction_type, location
        )
        return self.publish_message("inventory_updates", message)
    
    def publish_low_stock_alert(
        self,
        item_id: int,
        product_id: str,
        current_quantity: int,
        threshold: int,
        location: str = "unknown"
    ) -> bool:
        """Publish low stock alert event"""
        message = MessageSchema.low_stock_alert(
            item_id, product_id, current_quantity, threshold, location
        )
        return self.publish_message("low_stock_alerts", message)
    
    def publish_stock_validation(
        self,
        product_id: str,
        requested_quantity: int,
        available_quantity: int,
        order_id: Optional[str] = None
    ) -> bool:
        """Publish stock validation event"""
        message = MessageSchema.stock_validation(
            product_id, requested_quantity, available_quantity, order_id
        )
        return self.publish_message("stock_validation", message)
    
    def publish_stock_reserved(
        self,
        product_id: str,
        reserved_quantity: int,
        available_quantity: int,
        order_id: str,
        reservation_id: str
    ) -> bool:
        """Publish stock reservation event"""
        message = MessageSchema.stock_reserved(
            product_id, reserved_quantity, available_quantity,
            order_id, reservation_id
        )
        return self.publish_message("stock_reserved", message)
    
    def register_consumer(
        self,
        queue_name: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a consumer callback for a specific queue
        
        Args:
            queue_name: Queue to consume from
            callback: Async function to handle messages
        """
        self.consumers[queue_name] = callback
    
    def start_consuming(self) -> None:
        """Start consuming messages from all registered queues"""
        if not self.channel:
            logger.error("RabbitMQ channel not connected")
            return
        
        def message_callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                queue_name = method.routing_key.split('.')[1]  # Extract queue from routing key
                
                if queue_name in self.consumers:
                    callback = self.consumers[queue_name]
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.warning(f"No consumer registered for queue: {queue_name}")
                    ch.basic_nack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
        
        # Setup consumers
        for queue_name in self.consumers:
            queue_config = self.QUEUES.get(queue_name)
            if queue_config:
                self.channel.basic_consume(
                    queue=queue_config['name'],
                    on_message_callback=message_callback,
                    auto_ack=False
                )
        
        logger.info("Starting RabbitMQ consumer...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.disconnect()
            logger.info("Consumer stopped")


# Global RabbitMQ service instance
_rabbitmq_service: Optional[RabbitMQService] = None


def get_rabbitmq_service(rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/") -> RabbitMQService:
    """
    Get or create the RabbitMQ service instance
    
    Args:
        rabbitmq_url: RabbitMQ connection URL
    
    Returns:
        RabbitMQService instance
    """
    global _rabbitmq_service
    if _rabbitmq_service is None:
        _rabbitmq_service = RabbitMQService(rabbitmq_url)
        _rabbitmq_service.connect()
    return _rabbitmq_service
