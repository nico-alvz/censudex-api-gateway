# python env create

venv:
	@echo "$(GREEN)Creating Python virtual environment...$(NC)"
	@python -m venv .censudex-api-main
	@echo "$(GREEN)Virtual environment created$(NC)"
# python env activate
venv-activate:
	@echo "$(GREEN)To activate the virtual environment, run the following command:$(NC)"
	@echo "$(YELLOW).\.censudex-api-main\Scripts\Activate.ps1$(NC)"
venv-deactivate:
	@echo "$(GREEN)To deactivate the virtual environment, run the following command:$(NC)"
	@echo "$(YELLOW)deactivate$(NC)"
venv-install:
	@echo "$(GREEN)Installing required Python packages...$(NC)"
	@cd pip install -r requirements.txt
	@echo "$(GREEN)Required packages installed$(NC)"
# proto compile 
proto-compile:
	@echo "$(GREEN)Compiling protobuf files...$(NC)"
	@python -m grpc_tools.protoc -I=proto --python_out=pb2 --grpc_python_out=pb2 proto/user.proto
	@echo "$(GREEN)Protobuf files compiled successfully$(NC)"
test-client:
	@echo "$(GREEN)Running User Stub Service...$(NC)"
	@fastapi dev ../services/user-stub/main.py