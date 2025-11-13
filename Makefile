# python env create

venv:
	@echo "$(GREEN)Creating Python virtual environment...$(NC)"
	@python -m venv .censudex-api-gateway
	@echo "$(GREEN)Virtual environment created$(NC)"
	@echo "$(GREEN)Installing required packages...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)Required packages installed$(NC)"
	@echo "$(GREEN)To activate the virtual environment, run the following command:$(NC)"
	@echo "$(YELLOW).\.censudex-api-gateway\Scripts\Activate.ps1$(NC)"
# python env activate
venv-activate:
	@echo "$(GREEN)To activate the virtual environment, run the following command:$(NC)"
	@echo "$(YELLOW).\.censudex-api-gateway\Scripts\Activate.ps1$(NC)"
venv-deactivate:
	@echo "$(GREEN)To deactivate the virtual environment, run the following command:$(NC)"
	@echo "$(YELLOW)deactivate$(NC)"
venv-install:
	@echo "$(GREEN)Installing required Python packages...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)Required packages installed$(NC)"
# proto compile 
proto-compile:
	@echo "$(GREEN)Compiling protobuf files...$(NC)"
	@python -m grpc_tools.protoc -I=proto --python_out=pb2 --grpc_python_out=pb2 proto/user.proto
	@echo "$(GREEN)Protobuf files compiled successfully$(NC)"

nginx-up:
	@echo "$(GREEN)Starting Nginx server...$(NC)"
	@docker run -d --name nginx-api-gateway -p 80:80 --add-host=host.docker.internal:host-gateway -v ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:latest

	@echo "$(GREEN)Nginx server started$(NC)"
run:
	@echo "$(GREEN)Running Api Gateway...$(NC)"
	@fastapi dev gateway/main.py