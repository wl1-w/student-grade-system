#include "grade.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ================================================================
 * 常量与宏定义
 * ================================================================ */

#define DATA_FILE "grades.dat"           /* 数据存储文件名 */
#define TEMP_FILE "grades.tmp"           /* 临时文件（用于更新/删除操作） */

/* ================================================================
 * 内部辅助函数
 * ================================================================ */

/**
 * 判断两条成绩记录是否属于同一"学号+课程"组合
 * 用于去重和查找
 */
static int is_same_record(const Grade* a, const Grade* b) {
    return (strcmp(a->id, b->id) == 0 && strcmp(a->course, b->course) == 0);
}

/* ================================================================
 * 对外接口实现
 * ================================================================ */

/**
 * 添加一条成绩记录
 * 流程：先检查是否已有重复记录（学号+课程相同），如无则追加写入
 */
int add_grade(const Grade* grade) {
    FILE* fp;
    Grade existing;

    /* 先打开文件检查重复（如果文件不存在则跳过检查） */
    fp = fopen(DATA_FILE, "rb");
    if (fp != NULL) {
        while (fread(&existing, sizeof(Grade), 1, fp) == 1) {
            if (is_same_record(&existing, grade)) {
                fclose(fp);
                return 1;   /* 记录重复 */
            }
        }
        fclose(fp);
    }

    /* 以追加模式打开，写入新记录 */
    fp = fopen(DATA_FILE, "ab");
    if (fp == NULL) {
        return -1;  /* 文件打开失败 */
    }

    if (fwrite(grade, sizeof(Grade), 1, fp) != 1) {
        fclose(fp);
        return -1;  /* 写入失败 */
    }

    fclose(fp);
    return 0;   /* 成功 */
}

/**
 * 按学号查询所有课程成绩
 * 遍历数据文件，筛选匹配学号的记录，动态分配数组返回
 */
int query_by_student(const char* student_id, Grade** result) {
    FILE* fp;
    Grade temp;
    Grade* buffer = NULL;
    int capacity = 0;
    int count = 0;

    fp = fopen(DATA_FILE, "rb");
    if (fp == NULL) {
        *result = NULL;
        return 0;   /* 文件不存在视为0条记录 */
    }

    /* 先统计匹配记录数，分配空间 */
    while (fread(&temp, sizeof(Grade), 1, fp) == 1) {
        if (strcmp(temp.id, student_id) == 0) {
            count++;
        }
    }

    if (count == 0) {
        fclose(fp);
        *result = NULL;
        return 0;
    }

    /* 分配内存 */
    buffer = (Grade*)malloc(count * sizeof(Grade));
    if (buffer == NULL) {
        fclose(fp);
        *result = NULL;
        return -1;
    }

    /* 重新遍历，填充结果 */
    rewind(fp);
    capacity = 0;
    while (fread(&temp, sizeof(Grade), 1, fp) == 1) {
        if (strcmp(temp.id, student_id) == 0) {
            buffer[capacity++] = temp;
        }
    }

    fclose(fp);
    *result = buffer;
    return count;
}

/**
 * 释放 query_by_student 分配的动态内存
 */
void free_query_result(Grade* data) {
    if (data != NULL) {
        free(data);
    }
}

/**
 * 按课程统计平均分和最高分
 * 遍历数据文件，累加分数并跟踪最大值
 */
int stat_course(const char* course, float* avg, float* max) {
    FILE* fp;
    Grade temp;
    float sum = 0.0f;
    float max_score = -1.0f;
    int count = 0;

    fp = fopen(DATA_FILE, "rb");
    if (fp == NULL) {
        return -1;
    }

    while (fread(&temp, sizeof(Grade), 1, fp) == 1) {
        if (strcmp(temp.course, course) == 0) {
            sum += temp.score;
            if (temp.score > max_score) {
                max_score = temp.score;
            }
            count++;
        }
    }

    fclose(fp);

    if (count == 0) {
        return -1;  /* 没有该课程记录 */
    }

    *avg = sum / count;
    *max = max_score;
    return 0;
}

/**
 * 修改指定学号+课程的成绩
 * 流程：读取所有记录到临时文件，修改目标记录，替换原文件
 */
int update_grade(const char* id, const char* course, float new_score) {
    FILE* fp_in;
    FILE* fp_out;
    Grade temp;
    int found = 0;

    fp_in = fopen(DATA_FILE, "rb");
    if (fp_in == NULL) {
        return -1;  /* 文件不存在 */
    }

    fp_out = fopen(TEMP_FILE, "wb");
    if (fp_out == NULL) {
        fclose(fp_in);
        return -1;
    }

    while (fread(&temp, sizeof(Grade), 1, fp_in) == 1) {
        if (strcmp(temp.id, id) == 0 && strcmp(temp.course, course) == 0) {
            temp.score = new_score;   /* 修改分数 */
            found = 1;
        }
        fwrite(&temp, sizeof(Grade), 1, fp_out);
    }

    fclose(fp_in);
    fclose(fp_out);

    if (!found) {
        remove(TEMP_FILE);   /* 未找到记录，删除临时文件 */
        return 1;
    }

    /* 用临时文件替换原文件 */
    if (remove(DATA_FILE) != 0 || rename(TEMP_FILE, DATA_FILE) != 0) {
        return -1;
    }

    return 0;
}

/**
 * 删除指定学号+课程的记录
 * 流程：读取所有记录到临时文件（跳过要删除的记录），替换原文件
 */
int delete_grade(const char* id, const char* course) {
    FILE* fp_in;
    FILE* fp_out;
    Grade temp;
    int found = 0;

    fp_in = fopen(DATA_FILE, "rb");
    if (fp_in == NULL) {
        return -1;  /* 文件不存在 */
    }

    fp_out = fopen(TEMP_FILE, "wb");
    if (fp_out == NULL) {
        fclose(fp_in);
        return -1;
    }

    while (fread(&temp, sizeof(Grade), 1, fp_in) == 1) {
        if (strcmp(temp.id, id) == 0 && strcmp(temp.course, course) == 0) {
            found = 1;
            /* 跳过此记录 = 不写入 = 删除 */
        } else {
            fwrite(&temp, sizeof(Grade), 1, fp_out);
        }
    }

    fclose(fp_in);
    fclose(fp_out);

    if (!found) {
        remove(TEMP_FILE);
        return 1;
    }

    if (remove(DATA_FILE) != 0 || rename(TEMP_FILE, DATA_FILE) != 0) {
        return -1;
    }

    return 0;
}
