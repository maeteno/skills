---
name: release-note
description: Generate a structured release note by comparing two git refs (tags, branches, or commit SHAs). Use whenever the user wants to generate release notes, create a changelog between versions, summarize changes between two git tags or branches, or invokes /release-note. Triggers on phrases like "generate release note", "create release notes for v1.0 to v2.0", "what changed between these two versions", or "帮我生成 release note".
---

# Release Note

## Overview

通过比较两个 git ref（tag、branch、commit SHA），分析提交记录与文件变更，依据项目的**目录/模块结构**生成格式化的 release note。

模块名来源于项目实际结构（如 Maven submodule、npm workspace、Go 子模块目录），而非 commit message 的 scope 字段。

## When to Use

Use this skill when users:
- Want to generate release notes between two versions
- Ask to summarize changes between two git tags or branches
- Use `/release-note` command
- Want a changelog for a new release

## Workflow

### Step 1: 确认版本范围

如果用户未提供版本范围，询问：
- **From**（起始版本）：上一个 tag、branch 或 commit SHA，例如 `v1.2.0`
- **To**（结束版本）：新版本的 tag、branch 或 commit SHA，例如 `v1.3.0`（默认为 `HEAD`）

获取后，运行以下命令验证 ref 存在且有效：

```bash
git log <from>..<to> --oneline --no-merges | head -5
```

若命令失败，提示用户检查 ref 是否正确。

### Step 2: 检测项目模块结构

在项目根目录运行以下命令，识别构建系统与模块划分方式：

**Maven（Java）**
```bash
# 列出所有 pom.xml，识别多模块结构
find . -name "pom.xml" -not -path "*/target/*" | sort
# 从根 pom.xml 读取 <modules> 列表，获取子模块目录名
```

**npm / Node.js**
```bash
# 检查是否为 workspace（monorepo）
cat package.json | grep -A5 '"workspaces"'
ls packages/ 2>/dev/null || ls apps/ 2>/dev/null
```

**Go**
```bash
find . -name "go.mod" -not -path "*/vendor/*" | sort
```

**Python**
```bash
find . -name "pyproject.toml" -o -name "setup.py" | sort
```

**通用回退**：若无法识别构建系统，以顶层目录（depth=1）作为模块边界：
```bash
ls -d */ | grep -v -E "^\.|target|node_modules|dist|build|vendor|\.git"
```

**目标：得到一张模块名 → 目录路径的映射表**，例如：

| 模块名 | 目录路径 |
|--------|---------|
| api-gateway | `api-gateway/` |
| user-service | `user-service/` |
| common | `common/` |

若项目是单模块（只有一个根模块），则不做模块分组，直接按分类列出条目即可。

### Step 3: 收集提交记录与文件变更

并行运行以下命令：

```bash
# 获取每条提交的 SHA、subject，以及改动的文件列表
git log <from>..<to> --no-merges --name-only --format="COMMIT|||%H|||%s|||%b"

# 检查依赖文件变更
git diff <from>..<to> -- \
  pom.xml "*/pom.xml" \
  package.json "*/package.json" \
  requirements.txt build.gradle "*.gradle" \
  go.mod go.sum
```

`--name-only` 与 `--format` 同时使用时，每条提交输出为：`COMMIT|||<sha>|||<subject>|||<body>`，之后跟着改动的文件名列表，以空行分隔。

### Step 4: 将提交映射到模块

对每条提交，根据其改动文件路径判断所属模块：

- 将文件路径与 Step 2 得到的模块目录映射表对比
- 若一条提交涉及多个模块，在 release note 中每个模块下各列一条
- 若文件路径不属于任何已知模块目录（如根目录配置文件、CI 脚本），归入 **Root / 项目级别** 或忽略（视变更重要性决定）

**示例映射：**
```
Changed files: user-service/src/main/UserService.java
               user-service/src/test/UserServiceTest.java
→ 模块: user-service

Changed files: api-gateway/config/routes.yml
               common/utils/StringHelper.java
→ 模块: api-gateway, common (各自在对应模块下列一条)
```

### Step 5: 分类提交

将提交按以下规则分类，**分类依据来自 commit subject 和 body，不依赖 scope 字段**：

| 分类 | Conventional Commit 类型 | 关键词匹配（无规范时） |
|------|--------------------------|----------------------|
| ⭐ New Features | `feat` | add、new、implement、support、introduce |
| 🐞 Bug Fixes | `fix`、`hotfix` | fix、resolve、correct、patch |
| 📔 Documentation | `docs` | doc、readme、changelog、guide |
| 🔨 Dependency Upgrades | `chore(deps)`、`build(deps)` | upgrade、bump、update ... to |

- 同一 commit 只归入一个分类，以主要变更类型为准
- `refactor`、`chore`、`style`、`test` 等不直接暴露给用户的类型默认不输出；若用户明确要求包含，则归入对应类别或单独展示

**依赖升级处理：**
- 从 `git diff` 结果中提取依赖名称和版本号变化
- 格式：`Upgrade <dependency> to <version>`

### Step 6: 生成 Release Note

按以下模板生成最终内容，日期使用 release 当天日期（或用户指定日期）：

```
# YYYY-MM-DD

## ⭐ New Features

- module-name
    - 功能描述 [#issue-number](link)（如有）

- another-module
    - 功能描述

## 🐞 Bug Fixes

- module-name
    - 修复描述 [#issue-number](link)（如有）

## 📔 Documentation

- 文档更新描述（单模块项目无需分组）

## 🔨 Dependency Upgrades

- Upgrade <dependency> to <version>
```

**格式规则：**
- 若某分类没有对应内容，显示 `None`（一行即可）
- Features 和 Bug Fixes **按模块分组**（模块名来自 Step 2 的项目结构），每个模块下列出具体条目（缩进 4 空格）
- 单模块项目不需要模块层级，直接列出条目
- Documentation 和 Dependency Upgrades 无需按模块分组，直接列出条目
- 如果 commit message 中含 issue 编号（如 `#123` 或 `PROJ-456`），在条目末尾附上链接
- 语言：默认使用中文描述，若用户明确要求英文则使用英文

### Step 7: 输出并确认

将生成的 release note 以 markdown 代码块呈现，询问用户是否需要调整。

## Examples

### Example 1: Maven 多模块项目

项目结构：
```
api-gateway/
user-service/
payment-service/
common/
pom.xml
```

生成的 release note：
```
# 2025-05-26

## ⭐ New Features

- api-gateway
    - 新增 OAuth2 登录支持 [#234](https://github.com/xxx/issues/234)

- payment-service
    - 支持支付宝扫码支付

## 🐞 Bug Fixes

- user-service
    - 修复删除用户后关联订单状态未更新的问题 [#189](https://github.com/xxx/issues/189)

## 📔 Documentation

None

## 🔨 Dependency Upgrades

- Upgrade spring-boot to 3.4.2
- Upgrade netty to 4.2.11.Final
```

### Example 2: 单模块项目

```
# 2026-03-27

## ⭐ New Features

- 新增用户导出功能，支持 CSV 和 Excel 格式

## 🐞 Bug Fixes

None

## 📔 Documentation

None

## 🔨 Dependency Upgrades

- Upgrade netty to 4.2.11.Final
```

### Example 3: npm Workspace 项目

项目结构（packages/app, packages/ui, packages/api）：
```
# 2026-01-15

## ⭐ New Features

- packages/ui
    - 新增 DatePicker 组件，支持范围选择模式

- packages/api
    - 新增 /v2/users 批量查询接口

## 🐞 Bug Fixes

- packages/app
    - 修复移动端登录页面布局溢出问题

## 📔 Documentation

None

## 🔨 Dependency Upgrades

- Upgrade react to 19.1.0
```

## Notes

- 若项目有 CHANGELOG.md 或类似文件，可参考其风格调整输出格式
- 若提交记录过多（>100条），先汇报数量，询问用户是否继续
- 若发现提交信息质量参差不齐（大量无信息提交），如实告知用户，并尽力从文件变更推断含义
- 若一个模块下条目过多（>10条），可考虑对同类小改动进行适度合并
