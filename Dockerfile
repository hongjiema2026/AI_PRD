FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装开发依赖（测试用）
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# 复制项目文件
COPY . .

# 默认运行测试
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]