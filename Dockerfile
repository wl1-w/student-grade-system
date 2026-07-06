# ================================================================
# Dockerfile - Railway 部署
# ================================================================

FROM python:3.11-slim-bookworm

# 安装 gcc 及编译工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目全部文件
COPY . .

# 编译 C 动态库
RUN gcc -shared -fPIC -o libgrade.so grade.c \
    && echo "✅ libgrade.so compiled successfully" \
    && ls -lh libgrade.so

# 启动命令
CMD sh -c "gunicorn app:app --bind 0.0.0.0:\${PORT:-8000} --workers 2 --timeout 120"
