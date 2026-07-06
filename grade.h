/**
 * grade.h - 学生成绩管理系统 C 语言头文件
 * 
 * 定义成绩数据结构和所有数据操作的函数接口。
 * 编译为动态库 libgrade.so 供 Python 通过 ctypes 调用。
 */

#ifndef GRADE_H
#define GRADE_H

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 数据结构定义
 * ================================================================ */

/* 成绩记录结构体 */
typedef struct {
    char id[10];        /* 学号，如 "2021001" */
    char name[20];      /* 姓名 */
    char course[20];    /* 课程名称 */
    float score;        /* 分数，范围 0~100 */
} Grade;

/* ================================================================
 * 函数接口声明
 * ================================================================ */

/**
 * 添加一条成绩记录
 * @param grade  指向成绩结构体的指针
 * @return       0=成功, 1=记录重复(学号+课程已存在), -1=文件操作错误
 */
int add_grade(const Grade* grade);

/**
 * 按学号查询该学生的所有课程成绩
 * @param student_id  学号字符串
 * @param result      输出参数，指向动态分配的成绩数组（调用者需调用 free_query_result 释放）
 * @return            找到的记录数(>=0), -1=读取错误
 */
int query_by_student(const char* student_id, Grade** result);

/**
 * 释放 query_by_student 分配的动态内存
 * @param data  由 query_by_student 返回的数组指针
 */
void free_query_result(Grade* data);

/**
 * 按课程统计平均分和最高分
 * @param course  课程名称
 * @param avg     输出参数，平均分
 * @param max     输出参数，最高分
 * @return        0=成功, -1=没有该课程记录或读取错误
 */
int stat_course(const char* course, float* avg, float* max);

/**
 * 修改指定学号+课程的成绩
 * @param id         学号
 * @param course     课程名称
 * @param new_score  新分数
 * @return           0=成功, 1=未找到记录, -1=文件操作错误
 */
int update_grade(const char* id, const char* course, float new_score);

/**
 * 删除指定学号+课程的记录
 * @param id      学号
 * @param course  课程名称
 * @return        0=成功, 1=未找到记录, -1=文件操作错误
 */
int delete_grade(const char* id, const char* course);

#ifdef __cplusplus
}
#endif

#endif /* GRADE_H */
