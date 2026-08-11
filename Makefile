.PHONY: install test lint format clean docker-test help

PYTHON ?= python3
PIP ?= pip3

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	$(PIP) install -r requirements.txt

install-dev: ## 安装开发依赖
	$(PIP) install -r requirements-dev.txt

test: ## 运行测试
	PYTHONPATH=scripts:scripts/restore_pipeline:scripts/utils $(PYTHON) -m pytest tests/ -v --tb=short

test-cov: ## 运行测试并生成覆盖率报告
	PYTHONPATH=scripts:scripts/restore_pipeline:scripts/utils $(PYTHON) -m pytest tests/ -v \
		--cov=scripts --cov-report=term-missing --cov-report=html

lint: ## 代码检查
	$(PYTHON) -m flake8 scripts/ tests/ --max-line-length=120 --exclude=__pycache__

format: ## 格式化代码
	$(PYTHON) -m black scripts/ tests/

format-check: ## 检查代码格式
	$(PYTHON) -m black --check scripts/ tests/

type-check: ## 类型检查
	$(PYTHON) -m mypy scripts/ --ignore-missing-imports

docker-build: ## 构建 Docker 镜像
	docker build -t pm-workstation .

docker-test: ## 在 Docker 中运行测试
	docker compose run --rm test

clean: ## 清理构建产物
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	rm -rf *.egg-info dist build

check: lint format-check test ## 完整检查（lint + format + test）