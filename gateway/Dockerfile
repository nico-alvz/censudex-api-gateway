FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy gateway requirements and install dependencies
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto definition files
COPY proto /app/proto

# Create pb2 directory and regenerate proto files with correct protobuf version
RUN mkdir -p /app/pb2 && \
    python -m grpc_tools.protoc -I/app/proto --python_out=/app/pb2 --grpc_python_out=/app/pb2 /app/proto/user.proto && \
    python -m grpc_tools.protoc -I/app/proto --python_out=/app/pb2 --grpc_python_out=/app/pb2 /app/proto/order.proto && \
    cd /app/pb2 && sed -i 's/^import user_pb2/from . import user_pb2/' user_pb2_grpc.py && \
    sed -i 's/^import order_pb2/from . import order_pb2/' order_pb2_grpc.py && \
    touch /app/pb2/__init__.py

# Copy gateway application code
COPY gateway /app/gateway

# Copy models
COPY models /app/models

# Copy services (including RabbitMQ and other stubs)
COPY services /app/services

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/gateway/health || exit 1

# Run the application from parent context (gateway module is available)
CMD ["python", "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]