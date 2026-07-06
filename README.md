# 学生成绩管理系统

> **C 语言底层 + Flask API + 原生前端** 三层架构实训项目

## 📁 项目结构

```
Project_stu_grade/
├── grade.h              # C 头文件（Grade 结构体 & 函数声明）
├── grade.c              # C 实现（二进制文件 CRUD 操作）
├── app.py               # Flask 服务端（ctypes → C 动态库 + REST API）
├── templates/
│   └── index.html       # 前端（标签页 SPA，原生 HTML+CSS+JS）
├── compile.sh           # 编译脚本（gcc → libgrade.so）
├── libgrade.so          # 编译产物（C 动态链接库）
├── grades.dat           # 二进制数据文件（运行时自动生成）
└── README.md            # 本文件
```

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│  浏览器 (HTML + CSS + JavaScript)               │
│  标签页切换 · 表单验证 · Toast 提示 · 模态框      │
│  智能查询（纯数字→学号 / 含汉字→姓名）             │
└───────────────────┬─────────────────────────────┘
                    │ HTTP JSON (fetch / async-await)
┌───────────────────▼──────────────────────────────┐
│  Flask (Python)                                  │
│  7 个 RESTful API · ctypes 调用 C 函数            │
│  JSON 序列化 · struct 解析二进制文件               │
└───────────────────┬──────────────────────────────┘
                    │ ctypes (动态库调用) / struct (直接读文件)
┌───────────────────▼──────────────────────────────┐
│  libgrade.so (C 动态库)                           │
│  fread / fwrite 二进制文件读写                    │
│  增删改查 + 统计全部由 C 实现                      │
└───────────────────┬──────────────────────────────┘
                    │ 文件 I/O
┌───────────────────▼──────────────────────────────┐
│  grades.dat (56 字节/条 定长二进制记录)            │
└──────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 1. 编译 C 动态库

```bash
cd Project_stu_grade
bash compile.sh
```

### 2. 安装 Python 依赖

```bash
pip install flask
```

### 3. 启动 Flask 服务

```bash
python3 app.py
```

### 4. 打开浏览器

| 访问方式 | 地址 |
|----------|------|
| 局域网其他设备 | `http://<本机IP>:5000`（服务监听 `0.0.0.0`） |

## 🖥️ 前端功能

| 标签页 | 功能 | 亮点 |
|--------|------|------|
| ➕ 添加成绩 | 录入学号/姓名/课程/分数 | 前端验证（学号非空、分数 0-100）、提交后自动刷新查询 |
| 🔍 查询成绩 | 单输入框智能查询 | 输入纯数字→按学号查，输入汉字→按姓名模糊查，结果表格带序号+操作按钮 |
| 📊 课程统计 | 统计平均分/最高分 + 全表 | 📊🏆 渐变卡片展示，下方自动列出该课程全部学生成绩（按学号排序） |

### 交互特性

- **Toast 轻提示**：右上角弹出，3 秒自动消失，替代 alert
- **模态框**：修改成绩弹窗输入新分数，删除弹出确认对话框（确认/取消）
- **按钮加载态**：提交时显示"处理中…"，防止重复提交
- **键盘快捷键**：Enter 提交表单，Esc 关闭弹窗
- **响应式布局**：小屏自动适配

## 📡 API 接口文档

所有接口返回统一 JSON 格式：

```json
{ "code": 200, "data": {...}, "msg": "提示信息" }
```

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| `POST` | `/api/add` | 添加成绩 | JSON: `{id, name, course, score}` |
| `GET` | `/api/query` | 按学号精确查询 | Query: `?student_id=xxx` |
| `GET` | `/api/query_by_name` | 按姓名模糊查询 | Query: `?name=xxx` |
| `GET` | `/api/stats` | 课程统计（平均分+最高分） | Query: `?course=xxx` |
| `GET` | `/api/course_records` | 课程全部学生成绩表 | Query: `?course=xxx` |
| `PUT` | `/api/update` | 修改成绩 | JSON: `{id, course, score}` |
| `DELETE` | `/api/delete` | 删除记录 | JSON: `{id, course}` |

## 🔧 C 函数接口（grade.h）

| 函数 | 返回值 | 说明 |
|------|--------|------|
| `add_grade(Grade*)` | 0 / 1 / -1 | 添加（成功 / 重复 / 错误） |
| `query_by_student(id, **result)` | count ≥0 | 按学号查，动态分配数组 |
| `free_query_result(Grade*)` | void | 释放 query 分配的内存 |
| `stat_course(course, *avg, *max)` | 0 / -1 | 统计平均分和最高分 |
| `update_grade(id, course, score)` | 0 / 1 / -1 | 修改（成功 / 未找到 / 错误） |
| `delete_grade(id, course)` | 0 / 1 / -1 | 删除（成功 / 未找到 / 错误） |

## 📝 数据结构

```c
typedef struct {
    char id[10];      // 学号，如 "2021001"
    char name[20];    // 姓名
    char course[20];  // 课程名称
    float score;      // 分数（0~100）
} Grade;
// 磁盘占用：56 字节/条（含 2 字节对齐填充）
```

## 🛠️ 环境要求

- **GCC** — 编译 C 动态库
- **Python 3.6+** — 运行 Flask
- **Flask** — `pip install flask`
- **Linux / macOS**（Windows 需 WSL 或调整 `compile.sh`）
