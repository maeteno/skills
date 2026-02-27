---
name: glab-resolve
description: Resolve GitLab MR review threads interactively. Use when the user wants to address MR comments, fix review feedback, resolve discussion threads, or work through code review issues on a GitLab merge request. Triggers on requests like "resolve MR comments", "fix review feedback", "address MR threads", "/glab-resolve", or "/glab-resolve <MR_ID>".
---

# GitLab Resolve

## Overview

逐一处理 GitLab MR 中的评论线程，按难易程度排序，用户确认后依次解决。

## Workflow

### Step 1: 获取 MR 评论

```bash
glab mr view <MR_ID> --comments --per-page 100 --output json
```

若未提供 MR ID，询问用户。若命令失败，提示用户检查权限和 `glab` 配置。

### Step 2: 分析并分类问题

过滤掉已解决的线程，对未解决问题分类：

| 难度 | 描述 | 示例 |
|------|------|------|
| 简单 | 直接回答或小改动 | typo、添加注释、重命名 |
| 中等 | 需要分析，涉及逻辑调整 | 函数修改、逻辑重构 |
| 复杂 | 需深入分析，可能影响架构 | 设计变更、跨模块改动 |

### Step 3: 合并关联问题

将可以一起处理的问题合并（如同一文件的多个 typo，或逻辑上关联的修改），以减少来回切换。

### Step 4: 展示处理计划

向用户展示分类后的问题列表，按难度分组展示为独立表格：

**简单问题**

| # | Thread ID | 问题摘要 | 解决方案 |
|---|-----------|---------|---------|
| 1 | #<id> | <摘要> | <方案，如：直接修正、添加注释> |

**中等问题**

| # | Thread ID | 问题摘要 | 解决方案 |
|---|-----------|---------|---------|
| 1 | #<id> | <摘要> | <方案，如：需要深入分析、重构逻辑> |

**复杂问题**

| # | Thread ID | 问题摘要 | 解决方案 |
|---|-----------|---------|---------|
| 1 | #<id> | <摘要> | <方案，如：需继续讨论、涉及架构调整> |

**其他问题**

| # | Thread ID | 问题摘要 | 解决方案 |
|---|-----------|---------|---------|
| 1 | #<id> | <摘要> | <方案，如：已过期、无需处理> |

所有难度组必须展示，无对应问题时显示"暂无"，例如：

| # | Thread ID | 问题摘要 | 解决方案 |
|---|-----------|---------|---------|
| - | - | 暂无 | - |

### Step 5: 逐一处理问题

按 **简单 → 中等 → 复杂 → 其他** 的顺序处理：

1. 展示问题详情和建议的解决方案
2. 等待用户确认（可选择跳过）
3. 实施修改
4. 询问是否提交 commit

**每个问题处理后**，提示用户是否提交：
- 优先使用 `git-commit` skill 生成 commit 信息；若不可用，直接运行 `git commit`
- Footer 添加：`Resolve #<thread_id> <问题描述>`
- 示例：`Resolve #42 修复空指针异常处理`

用户可以选择跳过 commit，继续处理下一个问题后统一提交。

## 错误处理

- `glab` 命令失败：提示检查 `glab auth status` 和网络连接
- 无未解决线程：告知用户所有线程已解决
- 权限不足：提示用户确认是否有该项目的访问权限
