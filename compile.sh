#!/bin/bash
# ================================================================
# compile.sh - 编译 C 语言动态库
#
# 将 grade.c 编译为 libgrade.so，供 Python 通过 ctypes 调用。
# 使用方法：
#     chmod +x compile.sh
#     bash compile.sh
# ================================================================

set -e  # 遇到错误立即退出

echo "========================================="
echo "  编译学生成绩管理系统 C 语言动态库"
echo "========================================="

# 检查 gcc 是否存在
if ! command -v gcc &> /dev/null; then
    echo "[错误] 未找到 gcc，请先安装 GCC 编译器"
    echo "  Ubuntu/Debian: sudo apt install gcc"
    echo "  CentOS/RHEL:   sudo yum install gcc"
    exit 1
fi

echo "[信息] GCC 版本: $(gcc --version | head -1)"

# 编译为共享库（位置无关代码 + 动态库）
echo "[编译] gcc -shared -fPIC -o libgrade.so grade.c"
gcc -shared -fPIC -o libgrade.so grade.c

if [ -f "libgrade.so" ]; then
    echo "[成功] 动态库 libgrade.so 编译完成！"
    ls -lh libgrade.so
else
    echo "[错误] 编译失败，未生成 libgrade.so"
    exit 1
fi

echo ""
echo "========================================="
echo "  下一步：安装 Python 依赖并启动服务"
echo "========================================="
echo "  pip install flask"
echo "  python3 app.py"
echo ""
echo "  然后访问 http://127.0.0.1:5000"
echo "========================================="
