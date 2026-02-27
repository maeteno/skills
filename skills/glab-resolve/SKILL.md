---
name: glab-resolve
description: Resolve GitLab MR review threads interactively. Use when the user wants to address MR comments, fix review feedback, resolve discussion threads, or work through code review issues on a GitLab merge request. Triggers on requests like "resolve MR comments", "fix review feedback", "address MR threads", "/glab-resolve", or "/glab-resolve <MR_ID>".
---

# GitLab Resolve

## Overview

逐一处理 GitLab MR 中的评论线程，按难易程度分类后规划执行步骤，用户确认计划后按步骤依次解决并提交。

## Workflow

### Step 1: 获取 MR 评论

使用 `glab api --paginate` 确保拉取所有评论（自动处理分页）：

```bash
# 获取项目路径（URL 编码的 namespace/project）
PROJECT=$(glab repo view --output json | jq -r '.fullPath' | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip(), safe=''))")

# 拉取所有 discussions（包含线程结构）
glab api --paginate "projects/${PROJECT}/merge_requests/<MR_ID>/discussions"
```

过滤掉系统消息（`system: true`）和机器人评论，只保留真实用户的评论线程。

若未提供 MR ID，询问用户。若命令失败，提示用户检查 `glab auth status` 和项目权限。

### Step 2: 分析并分类问题

过滤掉已解决的线程，对未解决问题按难度分类：

| 难度 | 描述 | 示例 |
|------|------|------|
| 简单 | 直接回答或小改动 | typo、添加注释、重命名 |
| 中等 | 需要分析，涉及逻辑调整 | 函数修改、逻辑重构 |
| 复杂 | 需深入分析，可能影响架构 | 设计变更、跨模块改动 |
| 其他 | 无需代码修改 | 已过期、需继续讨论 |

### Step 3: 规划执行步骤

难度和合并是两个独立维度：

- **合并只能发生在同一难度内**，跨难度问题不可合并
- 将同一难度下关联紧密的问题合并为一个执行步骤（如同一文件的多个 typo、同一模块的相关修改）
- **复杂问题默认不合并**，除非关联极为明显且改动范围确定
- 每个执行步骤对应一次 commit

### Step 4: 展示分类概览

按难度分组展示所有问题，供用户了解全貌：

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

### Step 5: 展示执行步骤计划

将问题组织为有序的执行步骤，每步对应一次 commit：

| 步骤 | 难度 | 包含问题 | 修复说明 |
|------|------|---------|---------|
| Step 1 | 简单 | #12, #15 | 修正两处 typo |
| Step 2 | 简单 | #18 | 添加缺失注释 |
| Step 3 | 中等 | #22 | 重构校验逻辑 |
| Step 4 | 复杂 | #31 | 调整错误处理架构 |
| Step 5 | 复杂 | #35 | 优化模块依赖关系 |

**展示后等待用户确认或调整**，用户可以：
- 拆分某个步骤（将合并的问题分开）
- 合并某些步骤（前提：同一难度）
- 调整执行顺序

### Step 6: 按步骤顺序执行

用户确认计划后，**严格按步骤顺序逐一执行，不得跳跃或乱序**。每步完成后再进入下一步。

每个步骤的执行流程：

1. 展示当前步骤的问题详情
2. 等待用户确认（可选择跳过当前步骤）
3. 实施修改
4. 使用 `git-commit` skill 生成 commit 信息；若不可用，直接运行 `git commit`
   - Footer 添加所有关联 thread：`Resolve #<id1>, #<id2> <简要描述>`
   - 示例：`Resolve #12, #15 修正两处 typo`
5. 确认 commit 后，继续执行下一步骤

### Step 7: 展示执行汇总

所有步骤执行完毕后，展示汇总表格：

| 步骤 | 难度 | 包含问题 | 状态 | 备注 |
|------|------|---------|------|------|
| Step 1 | 简单 | #12, #15 | ✅ 已完成 | commit abc1234 |
| Step 2 | 简单 | #18 | ⏭️ 已跳过 | 用户跳过 |
| Step 3 | 中等 | #22 | ✅ 已完成 | commit def5678 |
| Step 4 | 复杂 | #31 | ✅ 已完成 | commit ghi9012 |

**汇总统计：**
- 已完成：X 步（涉及 N 个问题）
- 已跳过：X 步（涉及 N 个问题）
- 总计：X 步

## 错误处理

- `glab` 命令失败：提示检查 `glab auth status` 和网络连接
- 无未解决线程：告知用户所有线程已解决
- 权限不足：提示用户确认是否有该项目的访问权限
