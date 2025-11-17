import pika
import os
from dotenv import load_dotenv
import json
"""
RabbitMQ client for publishing and consuming messages.
"""
class RabbitMQ:
    """
    Init RabbitMQ connection and channel with given credentials. (Only to produce messages)
    Connection is lazy - only established when needed.
    """
    def __init__(self):
        load_dotenv()
        self.user = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.urn = os.getenv('RABBITMQ_URN', 'urn:message:censudex_clients_service.src.shared:EmailMessage')
        self.connection = None
        self.channel = None
    """
    Connect to RabbitMQ server and create a channel.
    """
    def connect(self):
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials, connection_attempts=1)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
        except Exception as e:
            print(f"RabbitMQ connection failed (will retry on publish): {e}")
            self.connection = None
            self.channel = None
    """
    Publish a message to a RabbitMQ queue.
    """
    def publish(self, queue_name, message):
        # Ensure connection is established
        if not self.channel:
            try:
                self.connect()
            except Exception as e:
                print(f"Could not connect to RabbitMQ for publishing: {e}")
                return False
        
        if not self.channel:
            print("Connection is not established.")
            return False
            
        try:
            # Set message properties for durability and content type
            properties = pika.BasicProperties(
                content_type="application/json",
                headers={
                    "messageType": [
                        self.urn
                    ]
                },
                delivery_mode=2
                )
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.basic_publish(exchange='',
                                       routing_key=queue_name,
                                       body=json.dumps(message),
                                       properties=properties)
            print(f"Sent message to queue {queue_name}: {message}")
            return True
        except Exception as e:
            print(f"Failed to publish message: {e}")
            return False