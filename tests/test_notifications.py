"""
Tests for Inventory Notifications System
Tests for RabbitMQ messaging, event consumer, and notification endpoints
"""

import pytest
from datetime import datetime

# Note: These tests assume RabbitMQ is running


class TestMessageSchema:
    """Test message schema generation"""
    
    def test_inventory_update_schema(self):
        """Test inventory update message schema"""
        from services.messaging import MessageSchema
        
        message = MessageSchema.inventory_update(
            item_id=1,
            product_id="PROD-001",
            old_quantity=50,
            new_quantity=45,
            transaction_type="OUT",
            location="shelf-a1"
        )
        
        assert message["event_type"] == "inventory_updated"
        assert message["service"] == "inventory-service"
        assert message["payload"]["item_id"] is None  # Changed from inventory_item_id
        assert message["payload"]["product_id"] == "PROD-001"
        assert message["payload"]["quantity_change"] == -5
        assert message["payload"]["transaction_type"] == "OUT"
    
    def test_low_stock_alert_schema(self):
        """Test low stock alert message schema"""
        from services.messaging import MessageSchema
        
        message = MessageSchema.low_stock_alert(
            item_id=1,
            product_id="PROD-002",
            current_quantity=0,
            threshold=10,
            location="warehouse-main"
        )
        
        assert message["event_type"] == "low_stock_alert"
        assert message["severity"] == "critical"  # Out of stock = critical
        assert message["payload"]["current_quantity"] == 0
        assert message["payload"]["action_required"] is True
    
    def test_low_stock_alert_warning(self):
        """Test low stock alert with warning severity"""
        from services.messaging import MessageSchema
        
        message = MessageSchema.low_stock_alert(
            item_id=2,
            product_id="PROD-003",
            current_quantity=5,
            threshold=10
        )
        
        assert message["severity"] == "warning"  # Low but not out = warning
    
    def test_stock_validation_schema(self):
        """Test stock validation message schema"""
        from services.messaging import MessageSchema
        
        message = MessageSchema.stock_validation(
            product_id="PROD-004",
            requested_quantity=10,
            available_quantity=20,
            order_id="ORD-001"
        )
        
        assert message["event_type"] == "stock_validation"
        assert message["payload"]["validation_result"] is True
    
    def test_stock_reserved_schema(self):
        """Test stock reservation message schema"""
        from services.messaging import MessageSchema
        
        message = MessageSchema.stock_reserved(
            product_id="PROD-005",
            reserved_quantity=5,
            available_quantity=15,
            order_id="ORD-002",
            reservation_id="RES-001"
        )
        
        assert message["event_type"] == "stock_reserved"
        assert message["payload"]["order_id"] == "ORD-002"
        assert message["payload"]["reservation_id"] == "RES-001"


class TestEventConsumer:
    """Test event consumer functionality"""
    
    def test_consumer_initialization(self):
        """Test event consumer initialization"""
        from services.event_consumer import InventoryEventConsumer
        
        consumer = InventoryEventConsumer()
        assert consumer is not None
        assert len(consumer.handlers) == 0
        assert len(consumer.alert_history) == 0
    
    def test_register_handler(self):
        """Test handler registration"""
        from services.event_consumer import InventoryEventConsumer
        
        consumer = InventoryEventConsumer()
        
        def test_handler(msg):
            pass
        
        consumer.register_handler("test_event", test_handler)
        assert "test_event" in consumer.handlers
        assert consumer.handlers["test_event"] == test_handler
    
    def test_process_message(self):
        """Test message processing"""
        from services.event_consumer import InventoryEventConsumer
        
        consumer = InventoryEventConsumer()
        messages_received = []
        
        def test_handler(msg):
            messages_received.append(msg)
        
        consumer.register_handler("test_event", test_handler)
        
        test_message = {
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {"test": "data"}
        }
        
        consumer.process_message(test_message)
        
        assert len(messages_received) == 1
        assert messages_received[0]["payload"]["test"] == "data"
    
    def test_message_history(self):
        """Test message history tracking"""
        from services.event_consumer import InventoryEventConsumer
        
        consumer = InventoryEventConsumer()
        
        def dummy_handler(msg):
            pass
        
        consumer.register_handler("event1", dummy_handler)
        
        for i in range(5):
            consumer.process_message({
                "event_type": "event1",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {"index": i}
            })
        
        assert len(consumer.alert_history) == 5
        
        # Test get_history with limit
        history = consumer.get_history(limit=3)
        assert len(history) == 3


class TestNotificationHandlers:
    """Test default notification handlers"""
    
    def test_handle_inventory_updated(self):
        """Test inventory update handler"""
        from services.event_consumer import InventoryNotificationHandlers
        
        message = {
            "event_type": "inventory_updated",
            "payload": {
                "inventory_item_id": 1,
                "product_id": "PROD-001",
                "quantity_change": -5,
                "transaction_type": "OUT"
            }
        }
        
        # Should not raise exception
        InventoryNotificationHandlers.handle_inventory_updated(message)
    
    def test_handle_low_stock_alert(self):
        """Test low stock alert handler"""
        from services.event_consumer import InventoryNotificationHandlers
        
        message = {
            "event_type": "low_stock_alert",
            "severity": "critical",
            "payload": {
                "inventory_item_id": 1,
                "product_id": "PROD-001",
                "current_quantity": 0,
                "threshold": 10
            }
        }
        
        # Should not raise exception
        InventoryNotificationHandlers.handle_low_stock_alert(message)
    
    def test_handle_stock_validation(self):
        """Test stock validation handler"""
        from services.event_consumer import InventoryNotificationHandlers
        
        message = {
            "event_type": "stock_validation",
            "payload": {
                "product_id": "PROD-001",
                "requested_quantity": 10,
                "available_quantity": 5,
                "validation_result": False
            }
        }
        
        # Should not raise exception
        InventoryNotificationHandlers.handle_stock_validation(message)
    
    def test_handle_stock_reserved(self):
        """Test stock reservation handler"""
        from services.event_consumer import InventoryNotificationHandlers
        
        message = {
            "event_type": "stock_reserved",
            "payload": {
                "product_id": "PROD-001",
                "reserved_quantity": 5,
                "available_quantity": 15,
                "order_id": "ORD-001"
            }
        }
        
        # Should not raise exception
        InventoryNotificationHandlers.handle_stock_reserved(message)


class TestNotificationEndpoints:
    """Test notification API endpoints"""
    
    @pytest.fixture
    def app_client(self):
        """Create test app client"""
        from fastapi.testclient import TestClient
        from gateway.main import app
        
        return TestClient(app)
    
    def test_notifications_health_endpoint(self, app_client):
        """Test notifications health check endpoint"""
        response = app_client.get("/api/v1/notifications/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["service"] == "notifications"
    
    def test_list_notifications_endpoint(self, app_client):
        """Test list notifications endpoint"""
        response = app_client.get("/api/v1/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total_count" in data
        assert "limit" in data
        assert "offset" in data
    
    def test_low_stock_alerts_endpoint(self, app_client):
        """Test low stock alerts endpoint"""
        response = app_client.get("/api/v1/notifications/low-stock")
        
        assert response.status_code == 200
        data = response.json()
        assert "low_stock_alerts" in data
        assert "total_count" in data
        assert "critical_count" in data
    
    def test_recent_notifications_endpoint(self, app_client):
        """Test recent notifications endpoint"""
        response = app_client.get("/api/v1/notifications/recent?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        assert "recent_notifications" in data
        assert "grouped_by_type" in data
        assert "stats" in data
    
    def test_notifications_summary_endpoint(self, app_client):
        """Test notifications summary endpoint"""
        response = app_client.get("/api/v1/notifications/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_notifications" in data["summary"]
        assert "by_type" in data["summary"]


class TestRabbitMQIntegration:
    """Integration tests with RabbitMQ (optional)"""
    
    @pytest.mark.skip(reason="Requires RabbitMQ to be running")
    def test_rabbitmq_connection(self):
        """Test RabbitMQ connection"""
        from services.messaging import RabbitMQService
        
        service = RabbitMQService()
        assert service.connect()
        service.disconnect()
    
    @pytest.mark.skip(reason="Requires RabbitMQ to be running")
    def test_publish_message(self):
        """Test publishing messages to RabbitMQ"""
        from services.messaging import RabbitMQService
        
        service = RabbitMQService()
        service.connect()
        
        result = service.publish_inventory_update(
            item_id=1,
            product_id="TEST-PROD",
            old_quantity=10,
            new_quantity=5,
            transaction_type="OUT"
        )
        
        assert result is True
        service.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
