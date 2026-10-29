# index.yaml 规则

每个工作区只有一个 `index.yaml`，与该工作区的 `AGENTS.md` 同级，是项目、仓库及 change/wiki 映射的唯一维护入口。项目和仓库的 `AGENTS.md` 只写行为约定，不重复维护路径；如需定位标识，只记 `project_name`、`repo_name` 并指向这个索引。

## 格式

```yaml
project:
  - name: _                      # 保留分组名：未按项目管理的仓库
    repos:
      - name: standalone-repo
        path: repos/standalone-repo
        change: change/standalone-repo
        wiki: null
  - name: backbone
    repos:
      - name: backbone-java
        path: repos/backbone/backbone-java
        change: change/backbone/backbone-java
        wiki: wiki/backbone/backbone-java
```

- 顶层 `project` 必须是列表；项目用 `name`、`repos`，仓库用 `name`、`path`、`change`、`wiki`。不用重复 YAML 键表示多个项目。没有仓库时写 `project: []`，不写示例仓库。
- 项目名在工作区内唯一，仓库名在所属分组内唯一，仓库 `path` 在索引内唯一，且规范化后不得互相包含。不支持登记嵌套仓库或 submodule；遇到时先请用户明确登记范围。
- 路径都相对工作区根目录，规范化为相对形式，不含绝对路径、`..`、`./`、重复或末尾分隔符，不得经符号链接越出工作区。
- `path` 指向真实存在的仓库。`change` 指向该仓库的需求、设计、审查记录目录。`wiki` 指向可选知识库目录，没有确定目标时为 `null`。change/wiki 必须位于所有已登记仓库之外。
- 推荐路径：分组仓库用 `change/<项目>/<仓库>`、`wiki/<项目>/<仓库>`，未分组用 `change/<仓库>`、`wiki/<仓库>`。已有目录以核实后的映射为准，不为统一结构迁移内容。同项目的多个仓库可映射到同一个共享目录。

## 目录缺失

change/wiki 目录可以是约定的待创建目录。缺失时 Agent 可自行创建，用于写入内容或建立 `.docs` 链接，不必另行询问。范围限于当前任务涉及的仓库，创建后同步更新 `index.yaml`（如 `wiki: null` 改为实际路径）。不因索引条目批量预建目录，也不因此生成 wiki 内容。

## 维护

1. 发现新仓库、仓库移动或映射变化时自行更新索引，保留无关条目，路径未知时先核实，不编造关联。
2. 缺少索引时围绕当前任务建立必要条目，不遍历整个工作区。用户要求初始化或全面核对时，限定在指定工作区。
3. 更新后运行 `ws.py check`，它检查重复键、名称与路径唯一性、仓库路径是否存在与重叠、映射是否越界、change/wiki 是否位于仓库之外，以及 `.docs` 链接是否一致。不因目录尚未创建就判定路径无效。
4. 无法核实时说明条目和原因，不把未验证的映射当作事实。不收录其他工作区或未授权的 KNOWLEDGE 内容。
5. 从旧 `index/` 迁移必须是用户明确的迁移任务：先保留实际索引内容，把维护约定并入工作区 `AGENTS.md`，核对后才可清理确认无用途的旧说明文件和空目录；不凭目录为空或推断删除。
6. 索引只存定位信息，不存源码、需求正文或审查报告。目录状态须核对实际文件。

## 查询与重命名

- 从仓库查询时，按相对仓库路径匹配条目的 `path`，不能仅按 `name`。尚未收录时，只在当前工作区内核实并补充。
- 项目名和仓库名是稳定的关联标识，change 记录中的 `project_id`、`repo_id` 与之对应。确需重命名时，在对应 change 目录留下旧名、新名和原因，并核对索引与引用，不无说明地改写历史记录。
- 登记、移动或重命名仓库后，对受影响仓库运行 `ws.py sync-docs`。
