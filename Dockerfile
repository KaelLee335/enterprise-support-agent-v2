FROM python:3.12-slim

# 阿里云 PyPI 镜像 + 放宽超时，避开 TUNA 对 pip 请求的 403 响应
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple \
    PIP_DEFAULT_TIMEOUT=120 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/support_agent.db

WORKDIR /app

# 第一层：按提交的锁文件安装依赖；改源码不会触发重装。
# Docker 构建使用 --frozen，避免构建时按镜像源元数据重新解析；CI 使用 --locked 校验锁文件是否过期。
COPY pyproject.toml uv.lock README.md ./
RUN python -m pip install --no-cache-dir uv==0.11.11 \
    && uv sync --frozen --no-install-project --no-dev

# 第二层：安装本地包并继续使用既有锁文件，不重新解析依赖。
COPY src ./src
RUN uv sync --frozen --no-dev

COPY data/seed ./data/seed
COPY data/policies ./data/policies
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "support_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
