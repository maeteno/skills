---
name: workspace-context
description: 在任何目录感知本机“工作目录根”（含 # ROOT 的 AGENTS.md）的结构：当前位置属于哪个工作区、项目、仓库，同项目有哪些兄弟仓库，change/wiki 存放在哪，以及哪些目录允许搜索。用于在仓库内读写 change/wiki 或过程记录、查找同项目其他仓库以理解上下文、登记或移动仓库、维护 index.yaml、建立或修复 .docs 链接，或不确定某文件应存放何处时。不用于初始化根目录或添加工作区（用 work-dir）。
---

# 工作目录上下文

根目录由 `# ROOT` 的 `AGENTS.md` 标识，不等于当前打开的目录。先让脚本定位，再按输出行事，不凭印象遍历目录。

```sh
uv run --no-project "<skill-dir>/scripts/ws.py" where
```

`<skill-dir>` 是本技能的绝对路径。脚本只用标准库。`where` 输出根目录、工作区、项目、仓库、change/wiki 映射、`.docs` 链接状态、同项目兄弟仓库，以及允许搜索与必须排除的范围。示例：

```text
root: /Users/me/Workspaces
workspace: maeteno
project: maeteno
repo: skills
change: change/maeteno/skills  # .docs/change: ok
wiki: null  # .docs/wiki: none
siblings: ...
searchable: [maeteno]
excluded: [maeteno/knowledge]
```

根目录定位顺序：`--root` 参数、环境变量 `WORKSPACES_ROOT`、从目标路径向上找最近的 `# ROOT`、`~/.config/workspaces/config` 中的 `root=`。找不到就停下，询问用户，不猜测。

## 红线

1. 主动执行的文件操作（列目录、搜索、读、写、移动、删除、生成）只限根目录内，不用绝对路径、`..`、符号链接绕过。例外仅两种：工作区 `knowledge` 链接和仓库 `.docs/` 链接。
2. 工作区相互隔离，读、搜、写都适用。只处理 `searchable` 中的工作区；位于根目录时不枚举工作区，目标不明就问。
3. 写入服务当前任务。同一 `PROJECT` 的仓库可以联动读写，其他项目须在用户要求的范围内。`_` 只是索引分组，不是项目，不授予跨仓库权限。
4. `KNOWLEDGE` 默认不搜索、不读、不写；用户明确指定路径和范围后才访问。搜索时排除 `excluded` 中的路径。
5. SDD、需求分析、设计、计划、任务清单、审查记录的实体不得写入代码仓库（含 `docs/`、隐藏目录、临时文件），统一写入 `where` 给出的 change 目录，通过 `.docs/change` 访问。README、接口说明等产品正式文档不受此限。
6. 临时文件、导出和索引等任务产物留在根目录内，归属当前工作区。仓库既有构建与测试的输出、工具缓存、会话文件按既定位置。
7. 子目录的 `AGENTS.md` 只能补充或收紧，不能放宽以上规则；冲突且无法判断时暂停并询问。
8. 这些是行为约定，不是系统沙箱。

## 按需读取细则

触发下列操作时，先读对应文件，再动手：

| 操作 | 先读 |
| --- | --- |
| 新增、移动、重命名仓库，修改或校验 `index.yaml` | [references/index.md](references/index.md) |
| 建立、修复 `.docs` 链接；写 change 或 wiki | [references/docs.md](references/docs.md) |
| 创建、登记或访问 knowledge | [references/knowledge.md](references/knowledge.md) |

## 常用命令

```sh
uv run --no-project "<skill-dir>/scripts/ws.py" sync-docs [--dry-run]   # 为当前仓库建立 .docs 链接
uv run --no-project "<skill-dir>/scripts/ws.py" check                   # 校验索引与链接
uv run --no-project "<skill-dir>/scripts/ws.py" --path <路径> where     # 解析指定路径
```

`sync-docs` 会创建缺失的 change 目录和链接。wiki 为 `null` 时跳过。已有同名真实文件或目录时拒绝覆盖，此时询问用户。索引有问题时拒绝建链，先修索引。退出码：0 正常，1 `check` 发现问题，2 参数或环境错误。

## 同项目上下文

要理解跨仓库背景时，用 `where` 的 `siblings` 找到同项目其他仓库，读它们的代码、change 与 wiki。这只在同一 `PROJECT` 内成立，`_` 分组没有兄弟仓库。其他项目与其他工作区不在范围内。

## 报告

说明修改范围和实际验证结果，列出各仓库的变化，不宣称未执行的检查已通过。有值得复用的知识时，建议记录到对应 wiki，写入前按 [references/docs.md](references/docs.md) 的规则确认。
