#!/usr/bin/env python3
"""
Inventory Event Worker
Background process that consumes messages from RabbitMQ
Run this alongside the main FastAPI application
"""

import sys
import logging
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.messaging import RabbitMQService
from services.event_consumer import get_event_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_consumer(messaging_service: RabbitMQService):
    """
    Setup event consumer with handlers
    
    Args:
        messaging_service: RabbitMQ messaging service
    """
    consumer = get_event_consumer()
    
    # Register handlers for specific queues
    messaging_service.register_consumer(
        "inventory_updates",
        lambda msg: consumer.process_message(msg)
    )
    messaging_service.register_consumer(
        "low_stock_alerts",
        lambda msg: consumer.process_message(msg)
    )
    messaging_service.register_consumer(
        "stock_validation",
        lambda msg: consumer.process_message(msg)
    )
    messaging_service.register_consumer(
        "stock_reserved",
        lambda msg: consumer.process_message(msg)
    )
    
    logger.info("Event consumer setup complete with 4 handlers registered")


def main():
    """Main worker entry point"""
    logger.info("Starting Inventory Event Worker...")
    
    try:
        # Initialize RabbitMQ service with correct credentials
        import os
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://censudx:censudex_password@rabbitmq:5672/censudx_vhost")
        logger.info(f"Connecting to RabbitMQ at: {rabbitmq_url}")
        messaging_service = RabbitMQService(rabbitmq_url)
        
        # Attempt connection
        if not messaging_service.connect():
            logger.error("Failed to connect to RabbitMQ. Retrying in 5 seconds...")
            time.sleep(5)
            return main()
        
        # Setup consumer
        setup_consumer(messaging_service)
        
        logger.info("Inventory Event Worker is running. Listening for messages...")
        logger.info("Press Ctrl+C to stop.")
        
        # Start consuming messages
        messaging_service.start_consuming()
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        messaging_service.disconnect()
        logger.info("Worker stopped gracefully")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
