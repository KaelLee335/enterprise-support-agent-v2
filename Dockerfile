FROM python:3.12-slim

# 国内镜像源 + 放宽超时，避免构建时 pip 拉包超时
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_DEFAULT_TIMEOUT=120 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/support_agent.db

WORKDIR /app

# 第一层：只装第三方依赖（只依赖 pyproject.toml，改源码不触发重装）
COPY pyproject.toml README.md ./
RUN python -c "import tomllib, subprocess, sys; \
    deps = tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; \
    sys.exit(subprocess.call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', *deps]))"

# 第二层：装本地包（--no-deps 秒级完成）
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps .

COPY data/seed ./data/seed
COPY data/policies ./data/policies
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "support_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
