# ================================================================
# Dockerfile - Railway 部署
#
# Railway 自动检测此文件，用它构建镜像并部署。
# ================================================================

FROM python:3.11-slim

# 安装 gcc（编译 C 动态库）
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目全部文件
COPY . .

# 编译 C 动态库
RUN bash compile.sh

# 暴露端口（Railway 通过 PORT 环境变量分配）
EXPOSE 8000

# 启动命令
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
