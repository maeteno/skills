#!/usr/bin/env python3
"""Create the work-dir layout without overwriting existing content."""

import argparse
import os
from pathlib import Path
import sys


ASSETS = Path(__file__).resolve().parent.parent / "assets"

KNOWLEDGE_RULES = """# KNOWLEDGE

本目录用于人工整理、独立管理的通用知识，不纳入工作区 index.yaml。
仅在用户明确指定内容和范围后读取；仅在明确要求编辑时写入。
不得自动扫描、索引、迁移或同步业务内容。创建约定的目录和规则不授权访问已有知识。
工作区级内容仅服务于同名工作区，遵守根目录规则和工作区隔离。
"""

WORKSPACE_RULES = """# WORKSPACE

继承 [根目录约定](../AGENTS.md)。本文件及同级资源仅适用于当前工作区，不访问其他工作区。

## 资源索引

使用同级 [index.yaml](index.yaml) 维护项目、仓库及 change/wiki 映射，不设置独立 index 目录。
AI 按任务核实并增量维护；顶层 project 为列表，项目使用 name、repos，仓库使用 name、path、change、wiki。
所有路径相对于本工作区；项目名、项目内仓库名和规范化后的仓库路径分别唯一，仓库路径不得互相包含。
仓库 path 必须真实存在；change/wiki 位于所有已登记仓库之外，可为已约定的待创建目录，wiki 未确定时为 null。
特殊分组 _ 仅用于索引归类，不授予跨仓库修改权限。按相对仓库路径匹配条目，不只按名称定位。
更新后检查 YAML 语法、重复键、唯一性、真实路径及访问边界；完整规则见根目录 AGENTS.md。

## KNOWLEDGE 登记

knowledge/ 为软链接，指向根目录 knowledge/workspaces/ 下的同名目录。
工作区搜索须排除 knowledge/；仅在用户明确指定范围后读取，仅在明确要求编辑时写入。
"""

CONTAINER_RULES = {
    "repos": "# REPOS\n\n本目录容纳项目及仓库，遵守根目录及所属工作区规则；不授予跨项目修改权限。\n",
    "change": "# CHANGE\n\n按工作区 index.yaml 映射存放需求、设计和审查记录；每项变更维护一份主记录，注明 change_id、project_id 和 repo_id。\n不将过程记录写入代码仓库，不擅自改变需求与验收条件。\n",
    "wiki": "# WIKI\n\n按工作区 index.yaml 映射存放项目或仓库知识，注明归属、来源及适用范围。\n区分核实事实与推测；按用户要求或已有维护约定记录，不自动扩展成无关批量改写。\n",
}


class Conflict(ValueError):
    pass


def physical_below_home(path):
    resolved = Path(path).expanduser().resolve()
    home = Path.home().resolve()
    if resolved == home or not resolved.is_relative_to(home):
        raise Conflict(f"目标必须是当前用户主目录的严格下级: {resolved}")
    return resolved


class Plan:
    def __init__(self, root):
        self.root = root
        self.entries = {}

    def directory(self, path):
        if path != self.root:
            self.directory(path.parent)
        self.entries[path] = ("directory", None)

    def file(self, path, content):
        self.directory(path.parent)
        self.entries[path] = ("file", content)

    def link(self, path, target):
        self.directory(path.parent)
        self.entries[path] = ("link", target)

    def exists(self, path):
        return path.exists() or path.is_symlink()

    def check(self, path, kind, content):
        if not self.exists(path):
            return
        if kind == "link":
            valid = path.is_symlink() and os.readlink(path) == content
        elif kind == "directory":
            valid = not path.is_symlink() and path.is_dir()
        else:
            valid = (not path.is_symlink() and path.is_file()
                     and path.read_text(encoding="utf-8") == content)
        if not valid:
            raise Conflict(f"已有内容或路径类型冲突，未覆盖: {path}")

    def apply(self):
        # Preflight every planned path before making any filesystem changes.
        for path, (kind, content) in self.entries.items():
            self.check(path, kind, content)
        created = 0
        for path, (kind, content) in self.entries.items():
            self.check(path, kind, content)
            if self.exists(path):
                continue
            if kind == "directory":
                path.mkdir(parents=path == self.root, exist_ok=False)
            elif kind == "file":
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(content)
            else:
                path.symlink_to(content, target_is_directory=True)
            created += 1
        for path, (kind, content) in self.entries.items():
            self.check(path, kind, content)
            if not self.exists(path):
                raise Conflict(f"创建后校验失败: {path}")
            if kind == "link" and not path.resolve(strict=True).is_relative_to(self.root):
                raise Conflict(f"链接目标越过根目录: {path}")
        return created, len(self.entries) - created


def knowledge(plan):
    plan.file(plan.root / "knowledge" / "AGENTS.md", KNOWLEDGE_RULES)
    plan.file(plan.root / "knowledge" / "workspaces" / "AGENTS.md", KNOWLEDGE_RULES)


def init(root):
    plan = Plan(root)
    plan.file(root / "AGENTS.md", (ASSETS / "root-AGENTS.md").read_text(encoding="utf-8"))
    knowledge(plan)
    return plan


def add_workspace(root, name):
    if (not name or name in {".", ".."} or "/" in name or "\\" in name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise Conflict("工作区名称必须是单个非空目录名，不能包含路径分隔符或控制字符")
    if name.casefold() in {"knowledge", "agents.md"}:
        raise Conflict(f"工作区名称与根目录保留资源冲突: {name}")
    root_rules = root / "AGENTS.md"
    if (root_rules.is_symlink() or not root_rules.is_file()
            or root_rules.read_text(encoding="utf-8").splitlines()[:1] != ["# ROOT"]):
        raise Conflict(f"请先初始化根目录；需要声明 # ROOT 的规则文件: {root_rules}")
    plan = Plan(root)
    knowledge(plan)
    workspace = root / name
    plan.file(workspace / "AGENTS.md", WORKSPACE_RULES)
    plan.file(workspace / "index.yaml", "project: []\n")
    for directory, rules in CONTAINER_RULES.items():
        plan.file(workspace / directory / "AGENTS.md", rules)
    plan.file(root / "knowledge" / "workspaces" / name / "AGENTS.md", KNOWLEDGE_RULES)
    plan.link(workspace / "knowledge", f"../knowledge/workspaces/{name}")
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("init", help="初始化工作目录根目录")
    initialize.add_argument("path")
    workspace = subparsers.add_parser("add-workspace", help="添加一个工作区")
    workspace.add_argument("name")
    workspace.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        physical_below_home(Path.cwd())
        root = physical_below_home(args.path if args.command == "init" else args.root)
        plan = init(root) if args.command == "init" else add_workspace(root, args.name)
        created, reused = plan.apply()
    except (OSError, ValueError) as error:
        print(f"错误: {error}\n未覆盖已有内容；若创建过程中失败，请检查已创建项。", file=sys.stderr)
        return 1
    print(f"根目录: {root}")
    if args.command == "add-workspace":
        print(f"工作区: {root / args.name}")
    print(f"校验通过；创建 {created} 项，复用 {reused} 项。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
