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
        self.connect()
    """
    Connect to RabbitMQ server and create a channel.
    """
    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
    """
    Publish a message to a RabbitMQ queue.
    """
    def publish(self, queue_name, message):
        # Ensure connection is established
        if not self.channel:
            raise Exception("Connection is not established.")
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