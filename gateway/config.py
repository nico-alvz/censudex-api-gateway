"""
Configuration Module
Centralized configuration management for the gateway
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RabbitMQConfig:
    """RabbitMQ Configuration"""
    HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    USERNAME: str = os.getenv("RABBITMQ_USER", "guest")
    PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    VHOST: str = os.getenv("RABBITMQ_VHOST", "/")
    
    @property
    def connection_url(self) -> str:
        """Generate RabbitMQ connection URL"""
        return f"amqp://{self.USERNAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}{self.VHOST}"


class InventoryConfig:
    """Inventory Service Configuration"""
    LOW_STOCK_THRESHOLD: int = int(os.getenv("LOW_STOCK_THRESHOLD", 10))
    ENABLE_AUTO_ALERTS: bool = os.getenv("ENABLE_AUTO_ALERTS", "true").lower() == "true"
    ALERT_EMAIL_RECIPIENTS: str = os.getenv("ALERT_EMAIL_RECIPIENTS", "admin@example.com")


class GatewayConfig:
    """Gateway Configuration"""
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_NOTIFICATION_HISTORY: int = int(os.getenv("MAX_NOTIFICATION_HISTORY", 1000))


class Config:
    """Main Configuration Class"""
    RABBITMQ = RabbitMQConfig()
    INVENTORY = InventoryConfig()
    GATEWAY = GatewayConfig()
