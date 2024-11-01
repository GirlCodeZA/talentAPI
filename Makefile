# Makefile for Talent API

# Variables
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Set up a virtual environment and install dependencies
setup: $(VENV_DIR)

$(VENV_DIR): requirements.txt
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Activate the virtual environment
activate:
	source $(VENV_DIR)/bin/activate

# Run the app
up: $(VENV_DIR)
	$(PYTHON) run.py

# Run tests
test: $(VENV_DIR)
	$(PYTHON) -m unittest discover -s app/tests

# Lint the code with Pylint
lint:
	$(VENV_DIR)/bin/pylint $(shell git ls-files '*.py')

# Docker commands
docker-build:
	docker build -t talent-backend .

docker-up:
	docker run -d -p 8000:8000 talent-backend

docker-down:
	docker stop $$(docker ps -q --filter ancestor=talent-backend)

# Clean up virtual environment and Docker images
clean:
	rm -rf $(VENV_DIR)
	docker rmi -f talent-backend

# Help message to list all commands
help:
	@echo "Available commands:"
	@echo "  make setup         - Set up virtual environment and install dependencies"
	@echo "  make activate      - Activate the virtual environment"
	@echo "  make up            - Run the app"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Lint the code with Pylint"
	@echo "  make docker-build  - Build the Docker image"
	@echo "  make docker-up     - Run the app in Docker"
	@echo "  make docker-down   - Stop the Docker container"
	@echo "  make clean         - Remove virtual environment and Docker image"
