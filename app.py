"""
app.py - 学生成绩管理系统 Flask 服务端

通过 ctypes 调用 C 语言编译的动态库 libgrade.so 来操作数据。
所有数据库操作均由 C 层完成，Python 层仅负责 HTTP 路由和 JSON 序列化。

启动方式：
    python3 app.py
"""

import os
import struct
import ctypes
from flask import Flask, request, jsonify, render_template

# ================================================================
# Flask 应用初始化
# ================================================================
app = Flask(__name__)

# ================================================================
# ctypes 加载 C 动态库
# ================================================================

# 获取当前脚本所在目录，确保能找到 libgrade.so
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(LIB_DIR, "libgrade.so")
DATA_FILE = os.path.join(LIB_DIR, "grades.dat")

# 加载动态库
try:
    lib = ctypes.CDLL(LIB_PATH)
except OSError as e:
    print(f"[错误] 无法加载动态库: {LIB_PATH}")
    print(f"  请先运行 compile.sh 编译 C 代码: bash compile.sh")
    print(f"  详细错误: {e}")
    exit(1)

# Grade 结构体: char[10]+char[20]+char[20]+2pad+float = 56 字节（float 需 4 字节对齐）
GRADE_STRUCT_SIZE = 56
GRADE_STRUCT_FMT = "10s20s20sf"  # 使用默认对齐（与 C 编译器一致）

# ================================================================
# 定义 ctypes 结构体 — 与 grade.h 中的 Grade 结构体对应
# ================================================================
class Grade(ctypes.Structure):
    _fields_ = [
        ("id",      ctypes.c_char * 10),
        ("name",    ctypes.c_char * 20),
        ("course",  ctypes.c_char * 20),
        ("score",   ctypes.c_float),
    ]

# ================================================================
# 设置 C 函数签名（参数类型和返回值类型）
# ================================================================

# int add_grade(const Grade* grade);
lib.add_grade.argtypes = [ctypes.POINTER(Grade)]
lib.add_grade.restype = ctypes.c_int

# int query_by_student(const char* student_id, Grade** result);
lib.query_by_student.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(Grade))]
lib.query_by_student.restype = ctypes.c_int

# void free_query_result(Grade* data);
lib.free_query_result.argtypes = [ctypes.POINTER(Grade)]
lib.free_query_result.restype = None

# int stat_course(const char* course, float* avg, float* max);
lib.stat_course.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
lib.stat_course.restype = ctypes.c_int

# int update_grade(const char* id, const char* course, float new_score);
lib.update_grade.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float]
lib.update_grade.restype = ctypes.c_int

# int delete_grade(const char* id, const char* course);
lib.delete_grade.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.delete_grade.restype = ctypes.c_int


# ================================================================
# 辅助函数：将 C 的 Grade 结构体转换为 Python 字典
# ================================================================
def grade_to_dict(g):
    """将 ctypes Grade 结构体转为 Python 字典"""
    return {
        "id":     g.id.decode("utf-8").strip("\x00"),
        "name":   g.name.decode("utf-8").strip("\x00"),
        "course": g.course.decode("utf-8").strip("\x00"),
        "score":  round(g.score, 1),
    }

# ================================================================
# 辅助函数：构建统一 JSON 响应
# ================================================================
def make_response(code, data=None, msg=""):
    """构建标准 JSON 响应"""
    return jsonify({"code": code, "data": data, "msg": msg}), code


# ================================================================
# 页面路由
# ================================================================
@app.route("/")
def index():
    """返回前端页面"""
    return render_template("index.html")


# ================================================================
# RESTful API 路由
# ================================================================

@app.route("/api/add", methods=["POST"])
def api_add():
    """添加成绩: POST /api/add
    请求体 JSON: { "id": "学号", "name": "姓名", "course": "课程", "score": 分数 }
    """
    data = request.get_json(silent=True)
    if not data:
        return make_response(400, msg="请求体不能为空，请提供 JSON 数据")

    # 字段校验
    student_id = (data.get("id") or "").strip()
    name       = (data.get("name") or "").strip()
    course     = (data.get("course") or "").strip()
    try:
        score = float(data.get("score", -1))
    except (TypeError, ValueError):
        return make_response(400, msg="分数必须是数字")

    # 非空校验
    if not student_id or not name or not course:
        return make_response(400, msg="学号、姓名、课程均不能为空")
    if score < 0 or score > 100:
        return make_response(400, msg="分数必须在 0 到 100 之间")

    # 构造 C 结构体
    grade = Grade()
    grade.id      = student_id.encode("utf-8")
    grade.name    = name.encode("utf-8")
    grade.course  = course.encode("utf-8")
    grade.score   = score

    # 调用 C 函数
    ret = lib.add_grade(ctypes.byref(grade))
    if ret == 0:
        return make_response(200, msg="成绩添加成功")
    elif ret == 1:
        return make_response(400, msg=f"记录重复：学号 {student_id} 的课程 {course} 已存在")
    else:
        return make_response(500, msg="服务器内部错误：文件操作失败")


@app.route("/api/query", methods=["GET"])
def api_query():
    """按学号查询: GET /api/query?student_id=xxx"""
    student_id = (request.args.get("student_id") or "").strip()
    if not student_id:
        return make_response(400, msg="请提供学号参数 student_id")

    # 调用 C 函数查询
    result_ptr = ctypes.POINTER(Grade)()
    count = lib.query_by_student(student_id.encode("utf-8"), ctypes.byref(result_ptr))

    if count < 0:
        return make_response(500, msg="服务器内部错误：读取文件失败")

    # 将 C 数组转为 Python 列表
    records = []
    if count > 0 and result_ptr:
        for i in range(count):
            records.append(grade_to_dict(result_ptr[i]))
        lib.free_query_result(result_ptr)  # 释放 C 层分配的内存

    return make_response(200, data={"count": count, "records": records}, msg="查询成功")


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """按课程统计: GET /api/stats?course=xxx"""
    course = (request.args.get("course") or "").strip()
    if not course:
        return make_response(400, msg="请提供课程参数 course")

    avg = ctypes.c_float(0.0)
    max_score = ctypes.c_float(0.0)

    ret = lib.stat_course(course.encode("utf-8"), ctypes.byref(avg), ctypes.byref(max_score))
    if ret == 0:
        return make_response(200, data={
            "course": course,
            "average": round(avg.value, 2),
            "max": round(max_score.value, 1)
        }, msg="统计成功")
    else:
        return make_response(404, msg=f"没有找到课程「{course}」的记录")


@app.route("/api/update", methods=["PUT"])
def api_update():
    """修改成绩: PUT /api/update
    请求体 JSON: { "id": "学号", "course": "课程", "score": 新分数 }
    """
    data = request.get_json(silent=True)
    if not data:
        return make_response(400, msg="请求体不能为空")

    student_id = (data.get("id") or "").strip()
    course     = (data.get("course") or "").strip()
    try:
        score = float(data.get("score", -1))
    except (TypeError, ValueError):
        return make_response(400, msg="分数必须是数字")

    if not student_id or not course:
        return make_response(400, msg="学号和课程不能为空")
    if score < 0 or score > 100:
        return make_response(400, msg="分数必须在 0 到 100 之间")

    ret = lib.update_grade(student_id.encode("utf-8"), course.encode("utf-8"), score)
    if ret == 0:
        return make_response(200, msg="成绩修改成功")
    elif ret == 1:
        return make_response(404, msg=f"未找到学号 {student_id} 课程 {course} 的记录")
    else:
        return make_response(500, msg="服务器内部错误：文件操作失败")


@app.route("/api/delete", methods=["DELETE"])
def api_delete():
    """删除成绩: DELETE /api/delete
    请求体 JSON: { "id": "学号", "course": "课程" }
    """
    data = request.get_json(silent=True)
    if not data:
        return make_response(400, msg="请求体不能为空")

    student_id = (data.get("id") or "").strip()
    course     = (data.get("course") or "").strip()

    if not student_id or not course:
        return make_response(400, msg="学号和课程不能为空")

    ret = lib.delete_grade(student_id.encode("utf-8"), course.encode("utf-8"))
    if ret == 0:
        return make_response(200, msg="成绩删除成功")
    elif ret == 1:
        return make_response(404, msg=f"未找到学号 {student_id} 课程 {course} 的记录")
    else:
        return make_response(500, msg="服务器内部错误：文件操作失败")


# ================================================================
# 辅助函数：读取全部记录（Python 层直接解析二进制文件）
# 用于按姓名查询和按课程返回全表
# ================================================================
def read_all_records():
    """读取 grades.dat 中所有记录，返回列表"""
    records = []
    if not os.path.exists(DATA_FILE):
        return records
    with open(DATA_FILE, "rb") as f:
        while True:
            data = f.read(GRADE_STRUCT_SIZE)
            if len(data) < GRADE_STRUCT_SIZE:
                break
            # 解析二进制: 10s + 20s + 20s + f
            rid, name, course, score = struct.unpack(GRADE_STRUCT_FMT, data)
            records.append({
                "id":     rid.decode("utf-8").rstrip("\x00"),
                "name":   name.decode("utf-8").rstrip("\x00"),
                "course": course.decode("utf-8").rstrip("\x00"),
                "score":  round(score, 1),
            })
    return records


# ================================================================
# API：按姓名查询
# ================================================================
@app.route("/api/query_by_name", methods=["GET"])
def api_query_by_name():
    """按姓名查询: GET /api/query_by_name?name=xxx"""
    name_query = (request.args.get("name") or "").strip()
    if not name_query:
        return make_response(400, msg="请提供姓名参数 name")

    all_records = read_all_records()
    # 模糊匹配（包含关系）
    matched = [r for r in all_records if name_query in r["name"]]

    return make_response(200, data={
        "count": len(matched),
        "records": matched
    }, msg="查询成功")


# ================================================================
# API：按课程返回所有学生成绩表（按学号排序）
# ================================================================
@app.route("/api/course_records", methods=["GET"])
def api_course_records():
    """按课程获取全表: GET /api/course_records?course=xxx"""
    course = (request.args.get("course") or "").strip()
    if not course:
        return make_response(400, msg="请提供课程参数 course")

    all_records = read_all_records()
    matched = [r for r in all_records if r["course"] == course]

    # 按学号排序
    matched.sort(key=lambda r: r["id"])

    return make_response(200, data={
        "course": course,
        "count": len(matched),
        "records": matched
    }, msg="查询成功")


# ================================================================
# 启动入口
# ================================================================
if __name__ == "__main__":
    # 确保 templates 目录存在
    os.makedirs(os.path.join(LIB_DIR, "templates"), exist_ok=True)

    # 优先使用环境变量 PORT（Render 等云平台要求），默认 5000
    port = int(os.environ.get("PORT", 5000))

    print("=" * 50)
    print("  学生成绩管理系统服务端")
    print("  C语言底层 + Flask API")
    print("=" * 50)
    print(f"  动态库路径: {LIB_PATH}")
    print(f"  数据文件: {os.path.join(LIB_DIR, 'grades.dat')}")
    print(f"  访问地址: http://0.0.0.0:{port}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=False)
