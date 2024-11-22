# Variables
PYTHON = python
VENV_DIR = env
REQUIREMENTS = requirements.txt
SRC_DIR = src
TEST_DIR = tests

# Targets
.PHONY: all setup lint test clean help

# Default target
all: lint test

# Help target
help:
	@echo "Available commands:"
	@echo "  make setup     - Set up virtual environment and install dependencies"
	@echo "  make lint      - Run lint checks on the source code"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Clean up temporary files and virtual environment"

# Create virtual environment and install dependencies
setup:
	@echo "Setting up the virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	source $(VENV_DIR)/bin/activate && pip install --upgrade pip && pip install -r $(REQUIREMENTS)
	@echo "Setup complete."

# Lint the source code
lint:
	@echo "Running lint checks..."
	source $(VENV_DIR)/bin/activate && flake8 $(SRC_DIR)
	@echo "Linting complete."

# Run tests
test:
	@echo "Running tests..."
	source $(VENV_DIR)/bin/activate && pytest $(TEST_DIR)
	@echo "Testing complete."

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR) __pycache__ .pytest_cache *.pyc *.pyo
	@echo "Cleanup complete."
