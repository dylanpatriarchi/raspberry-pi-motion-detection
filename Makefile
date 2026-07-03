# Makefile for Raspberry Pi Motion Detection System
# Professional motion detection system for Raspberry Pi

.PHONY: help install install-dev install-pi test lint format clean run diagnostics docker build-docker run-docker

# Default target
help:
	@echo "Raspberry Pi Motion Detection System - Professional Edition"
	@echo "==========================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  install-pi       Install with Raspberry Pi optimizations"
	@echo "  test             Run tests"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black"
	@echo "  clean            Clean build artifacts"
	@echo "  run              Run motion detection system"
	@echo "  diagnostics      Run system diagnostics"
	@echo "  docker           Build and run Docker container"
	@echo "  build-docker     Build Docker image"
	@echo "  run-docker       Run Docker container"
	@echo ""
	@echo "Configuration:"
	@echo "  CONFIG_FILE      Path to config file (default: config/settings.json)"
	@echo "  PYTHON          Python executable (default: python3)"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make run"
	@echo "  make run CONFIG_FILE=custom.json"
	@echo "  make diagnostics"

# Configuration
PYTHON ?= python3
PIP ?= pip3
CONFIG_FILE ?= config/settings.json

# Installation targets
install:
	@echo "📦 Installing production dependencies..."
	$(PIP) install -r requirements.txt
	@echo "✅ Installation complete"

install-dev: install
	@echo "📦 Installing development dependencies..."
	$(PIP) install -e ".[dev]"
	@echo "✅ Development installation complete"

install-pi: install
	@echo "📦 Installing Raspberry Pi specific dependencies..."
	$(PIP) install -e ".[raspberry-pi]"
	@echo "✅ Raspberry Pi installation complete"

# Development targets
test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v --cov=src/motion_detector --cov-report=html
	@echo "✅ Tests complete"

LINT_PATHS ?= src tests scripts main.py setup.py

lint:
	@echo "🔍 Running linting checks..."
	$(PYTHON) -m black --check --line-length=100 $(LINT_PATHS)
	$(PYTHON) -m flake8 $(LINT_PATHS)
	$(PYTHON) -m mypy src/motion_detector --ignore-missing-imports
	@echo "✅ Linting complete"

format:
	@echo "🎨 Formatting code..."
	$(PYTHON) -m black --line-length=100 $(LINT_PATHS)
	@echo "✅ Formatting complete"

# Cleanup targets
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# Runtime targets
run:
	@echo "🚀 Starting motion detection system..."
	$(PYTHON) main.py --config $(CONFIG_FILE)

run-debug:
	@echo "🐛 Starting motion detection system in debug mode..."
	$(PYTHON) main.py --config $(CONFIG_FILE) --debug

run-headless:
	@echo "🖥️  Starting motion detection system in headless mode..."
	$(PYTHON) main.py --config $(CONFIG_FILE) --no-preview

diagnostics:
	@echo "🔍 Running system diagnostics..."
	$(PYTHON) main.py --diagnostics

# Docker targets
build-docker:
	@echo "🐳 Building Docker image..."
	docker build -t motion-detector:latest .
	@echo "✅ Docker image built"

run-docker:
	@echo "🐳 Running Docker container..."
	docker run -it --rm \
		--device=/dev/video0 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/logs:/app/logs \
		motion-detector:latest
	@echo "✅ Docker container stopped"

docker: build-docker run-docker

# System service targets
install-service:
	@echo "🔧 Installing systemd service..."
	sudo cp scripts/motion-detector.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable motion-detector.service
	@echo "✅ Service installed. Use 'sudo systemctl start motion-detector' to start"

uninstall-service:
	@echo "🔧 Removing systemd service..."
	sudo systemctl stop motion-detector.service || true
	sudo systemctl disable motion-detector.service || true
	sudo rm -f /etc/systemd/system/motion-detector.service
	sudo systemctl daemon-reload
	@echo "✅ Service removed"

# Utility targets
setup-dev:
	@echo "🛠️  Setting up development environment..."
	$(PYTHON) -m venv venv
	@echo "Activate virtual environment with: source venv/bin/activate"
	@echo "Then run: make install-dev"

create-config:
	@echo "⚙️  Creating default configuration..."
	mkdir -p config
	$(PYTHON) -c "from src.motion_detector.config.settings import Settings; s = Settings(); s.save_config()"
	@echo "✅ Configuration created at config/settings.json"

backup-data:
	@echo "💾 Creating data backup..."
	mkdir -p backups
	tar -czf backups/data_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/ logs/
	@echo "✅ Backup created in backups/"

# Performance targets
benchmark:
	@echo "⚡ Running performance benchmark..."
	$(PYTHON) scripts/benchmark.py
	@echo "✅ Benchmark complete"

profile:
	@echo "📊 Running performance profiling..."
	$(PYTHON) -m cProfile -o profile.stats main.py --config $(CONFIG_FILE) --no-preview
	$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
	@echo "✅ Profiling complete"

# Documentation targets
docs:
	@echo "📚 Generating documentation..."
	mkdir -p docs/html
	$(PYTHON) -m pdoc src/motion_detector --html --force --output-dir docs/html
	@echo "✅ Documentation generated in docs/html/"

# Validation targets
validate-config:
	@echo "✅ Validating configuration..."
	$(PYTHON) -c "from src.motion_detector.config.settings import Settings; s = Settings('$(CONFIG_FILE)'); print('✅ Configuration valid' if s.validate() else '❌ Configuration invalid')"

check-system:
	@echo "🔍 Checking system requirements..."
	$(PYTHON) -c "from src.motion_detector.utils.validators import run_system_diagnostics; run_system_diagnostics()" 