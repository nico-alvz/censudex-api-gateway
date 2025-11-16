"""
Inventory Event Consumer
Listens to RabbitMQ events and processes inventory notifications
"""

import logging
from typing import Dict, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of inventory notifications"""
    INVENTORY_UPDATED = "inventory_updated"
    LOW_STOCK_ALERT = "low_stock_alert"
    STOCK_VALIDATION = "stock_validation"
    STOCK_RESERVED = "stock_reserved"


class InventoryEventConsumer:
    """
    Consumes and processes inventory events from RabbitMQ
    Handles different notification types with appropriate processing
    """
    
    def __init__(self):
        """Initialize event consumer"""
        self.handlers: Dict[str, Callable] = {}
        self.alert_history = []
        self.max_history = 1000
    
    def register_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a handler for a specific event type
        
        Args:
            event_type: Type of event to handle (e.g., 'inventory_updated')
            handler: Async function to process the event
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a message from RabbitMQ
        
        Args:
            message: Message dictionary with event data
        """
        try:
            event_type = message.get('event_type')
            timestamp = message.get('timestamp', datetime.utcnow().isoformat())
            
            logger.info(f"Processing event: {event_type} at {timestamp}")
            
            # Store in history for audit trail
            self._add_to_history(message)
            
            # Find and execute handler
            if event_type in self.handlers:
                handler = self.handlers[event_type]
                handler(message)
            else:
                logger.warning(f"No handler registered for event type: {event_type}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    def _add_to_history(self, message: Dict[str, Any]) -> None:
        """
        Add message to history for audit trail
        
        Args:
            message: Message to add to history
        """
        self.alert_history.append({
            "message": message,
            "processed_at": datetime.utcnow().isoformat()
        })
        
        # Keep history size under control
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def get_history(self, limit: int = 100) -> list:
        """
        Get recent alert history
        
        Args:
            limit: Maximum number of alerts to return
        
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:]


class InventoryNotificationHandlers:
    """Default handlers for inventory events"""
    
    @staticmethod
    def handle_inventory_updated(message: Dict[str, Any]) -> None:
        """
        Handle inventory update notifications
        
        Args:
            message: Inventory update message
        """
        payload = message.get('payload', {})
        item_id = payload.get('inventory_item_id')
        product_id = payload.get('product_id')
        quantity_change = payload.get('quantity_change')
        transaction_type = payload.get('transaction_type')
        
        logger.info(
            f"Inventory Updated - Product: {product_id}, "
            f"Item: {item_id}, Change: {quantity_change:+d}, "
            f"Type: {transaction_type}"
        )
        
        # Could integrate with external systems here:
        # - Send to analytics service
        # - Update cache
        # - Send webhook notifications
        # - Log to audit trail database
    
    @staticmethod
    def handle_low_stock_alert(message: Dict[str, Any]) -> None:
        """
        Handle low stock alert notifications
        
        Args:
            message: Low stock alert message
        """
        payload = message.get('payload', {})
        item_id = payload.get('inventory_item_id')
        product_id = payload.get('product_id')
        current_qty = payload.get('current_quantity')
        threshold = payload.get('threshold')
        severity = message.get('severity', 'warning')
        
        logger.warning(
            f"LOW STOCK ALERT [{severity.upper()}] - "
            f"Product: {product_id}, Item: {item_id}, "
            f"Current: {current_qty}/{threshold}"
        )
        
        # Could integrate with notification systems:
        # - Send email to inventory managers
        # - Send SMS alerts for critical items
        # - Create tickets in issue tracking system
        # - Send to Slack/Teams
        # - Trigger automated purchase orders
        if current_qty == 0:
            logger.critical(f"CRITICAL: Product {product_id} is out of stock!")
    
    @staticmethod
    def handle_stock_validation(message: Dict[str, Any]) -> None:
        """
        Handle stock validation notifications
        
        Args:
            message: Stock validation message
        """
        payload = message.get('payload', {})
        product_id = payload.get('product_id')
        requested = payload.get('requested_quantity')
        available = payload.get('available_quantity')
        order_id = payload.get('order_id')
        validation_result = payload.get('validation_result')
        
        logger.info(
            f"Stock Validation - Product: {product_id}, "
            f"Requested: {requested}, Available: {available}, "
            f"Order: {order_id}, Result: {'PASS' if validation_result else 'FAIL'}"
        )
        
        if not validation_result:
            logger.warning(
                f"Insufficient stock for order {order_id}: "
                f"Requested {requested} but only {available} available"
            )
    
    @staticmethod
    def handle_stock_reserved(message: Dict[str, Any]) -> None:
        """
        Handle stock reservation notifications
        
        Args:
            message: Stock reservation message
        """
        payload = message.get('payload', {})
        product_id = payload.get('product_id')
        reserved_qty = payload.get('reserved_quantity')
        available_qty = payload.get('available_quantity')
        order_id = payload.get('order_id')
        reservation_id = payload.get('reservation_id')
        
        logger.info(
            f"Stock Reserved - Product: {product_id}, "
            f"Reserved: {reserved_qty}, Available: {available_qty}, "
            f"Order: {order_id}, Reservation: {reservation_id}"
        )
        
        # Could integrate with:
        # - Order fulfillment systems
        # - Shipping logistics
        # - Warehouse management systems


def create_event_consumer() -> InventoryEventConsumer:
    """
    Create and configure event consumer with default handlers
    
    Returns:
        Configured InventoryEventConsumer instance
    """
    consumer = InventoryEventConsumer()
    
    # Register default handlers
    consumer.register_handler(
        NotificationType.INVENTORY_UPDATED.value,
        InventoryNotificationHandlers.handle_inventory_updated
    )
    consumer.register_handler(
        NotificationType.LOW_STOCK_ALERT.value,
        InventoryNotificationHandlers.handle_low_stock_alert
    )
    consumer.register_handler(
        NotificationType.STOCK_VALIDATION.value,
        InventoryNotificationHandlers.handle_stock_validation
    )
    consumer.register_handler(
        NotificationType.STOCK_RESERVED.value,
        InventoryNotificationHandlers.handle_stock_reserved
    )
    
    return consumer


# Global event consumer instance
_event_consumer: InventoryEventConsumer = create_event_consumer()


def get_event_consumer() -> InventoryEventConsumer:
    """
    Get the global event consumer instance
    
    Returns:
        Global InventoryEventConsumer instance
    """
    return _event_consumer
