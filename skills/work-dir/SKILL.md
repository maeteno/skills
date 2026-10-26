---
name: work-dir
description: 初始化本地工作目录根目录，或添加带有 AGENTS.md、资源索引及知识目录链接的工作区。用于 /work-dir init、/work-dir add-workspace 及同义请求，不用于普通项目脚手架或批量迁移现有目录。
---

# 工作目录管理

使用 [scripts/work_dir.py](scripts/work_dir.py) 创建结构；根目录规则模板为 [assets/root-AGENTS.md](assets/root-AGENTS.md)。仅初始化指定根目录或添加指定工作区，不顺带登记仓库、迁移旧目录或整理知识内容。

## 执行前

- 将当前目录及目标目录解析为物理路径，确保均为当前用户主目录的严格下级。目标尚不存在时解析已有父目录。先发现并遵循适用的 `AGENTS.md`，在 `ROOT` 或主目录之前停止向上发现，不读取主目录自身的规则。
- 根目录模板将文件操作限制在根目录内，工作区之间隔离。初始化不得绕过当前已生效的根目录或工作区边界；目标越界时停止受影响的操作，说明限制并请用户选择允许的位置。
- 添加工作区时，优先使用用户指定的根目录；否则从当前目录向上定位最近的 `# ROOT`。无法确定时询问，不遍历其他工作区。现有根目录规则与本技能结构冲突时先说明冲突，不用模板覆盖规则。
- 本次创建授权仅涵盖目录、规则、空索引和链接；不读取 `KNOWLEDGE` 的业务内容。

以下命令中的 `<skill-dir>` 是本技能的绝对路径，运行时替换占位符并正确引用路径。通过 `uv run --no-project` 运行脚本，不需要第三方依赖。

## 初始化根目录

收到 `/work-dir init 目录地址`（或 `$work-dir init 目录地址`）时，将相对地址按调用时的当前目录解析：

```sh
uv run --no-project "<skill-dir>/scripts/work_dir.py" init "目录地址"
```

创建根目录 `AGENTS.md`、`knowledge/AGENTS.md` 和 `knowledge/workspaces/AGENTS.md`；后两者声明 `KNOWLEDGE` 的独立访问规则。不会预建工作区。

## 添加工作区

收到 `/work-dir add-workspace xxx`（或 `$work-dir add-workspace xxx`）时：

```sh
uv run --no-project "<skill-dir>/scripts/work_dir.py" add-workspace "xxx" --root "已确定的根目录"
```

名称必须是单个目录名。脚本要求根目录已初始化，创建：

```text
根目录/
├── xxx/
│   ├── AGENTS.md                 # WORKSPACE，登记 index.yaml 和 knowledge/
│   ├── index.yaml                # project: []，不填虚构仓库
│   ├── repos/                    # REPOS，附 AGENTS.md
│   ├── change/                   # CHANGE，附 AGENTS.md
│   ├── wiki/                     # WIKI，附 AGENTS.md
│   └── knowledge -> ../knowledge/workspaces/xxx
└── knowledge/workspaces/xxx/
    └── AGENTS.md                 # KNOWLEDGE
```

`repos` 是仓库容器；`change` 和 `wiki` 位于仓库外。知识实体在根目录统一管理，链接入口在工作区内，不反向链接。

## 冲突与验证

脚本先检查全部计划路径，再创建缺失项。已有目录和内容完全一致的文件、链接可重复使用；文件内容不同、节点类型不符或出现非预期软链接时停止，不覆盖、不删除。已定制的规则或非空索引也保留；确需合并时先核对实际规则与内容，在用户任务范围内单独处理。脚本不提供强制覆盖选项。

成功后脚本检查文件、目录和链接目标；报告实际根目录、工作区及创建/复用数量。失败时说明冲突路径；运行中发生权限或 I/O 错误可能留下已创建项，保留这些项并报告，不自动删除或改权限。目录规则约束 Agent 行为，不构成系统安全沙箱。
