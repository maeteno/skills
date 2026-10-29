#!/usr/bin/env python3
"""ws: resolve where a path sits in the work-dir root and keep .docs links in sync."""

import argparse
import os
from pathlib import Path
import sys

from ws_index import normalize, parse
from ws_root import WsError, below_home, locate_root, workspace_of

KINDS = ("change", "wiki")


def load(workspace):
    """Read index.yaml into flat entries with absolute paths; raises WsError on bad input."""
    index = workspace / "index.yaml"
    if index.is_symlink() or not index.is_file():
        raise WsError(f"缺少 index.yaml: {index}")
    entries = []
    for project in parse(index.read_text(encoding="utf-8")):
        for repo in project["repos"]:
            entry = {"project": project["name"], "name": repo["name"]}
            for key in ("path", *KINDS):
                rel = normalize(repo[key])
                entry[key + "_rel"] = rel
                entry[key] = workspace / rel if rel else None
            entries.append(entry)
    return entries


def problems(workspace, entries):
    """Collect index violations; an empty list means the index is consistent."""
    found, names, paths = [], set(), set()
    real = workspace.resolve()
    repo_paths = [e["path"] for e in entries if e["path"]]
    for e in entries:
        label = f"{e['project']}/{e['name']}"
        if (e["project"], e["name"]) in names:
            found.append(f"重复的仓库名: {label}")
        names.add((e["project"], e["name"]))
        if not e["path"]:
            found.append(f"{label}: 缺少 path")
            continue
        if e["path_rel"] in paths:
            found.append(f"重复的仓库 path: {e['path_rel']}")
        paths.add(e["path_rel"])
        if not e["path"].is_dir():
            found.append(f"{label}: path 不存在: {e['path_rel']}")
        for other in repo_paths:
            if other != e["path"] and other.is_relative_to(e["path"]):
                found.append(f"仓库路径互相包含: {e['path_rel']} ⊃ {other.relative_to(workspace)}")
        for key in KINDS:
            target = e[key]
            if target is None:
                if key == "change":
                    found.append(f"{label}: 缺少 change 映射")
                continue
            if not target.resolve().is_relative_to(real):
                found.append(f"{label}: {key} 越出工作区: {e[key + '_rel']}")
            if any(target.is_relative_to(r) for r in repo_paths):
                found.append(f"{label}: {key} 位于已登记仓库之内: {e[key + '_rel']}")
    return found


def match(workspace, entries, path):
    """Longest-prefix repository match for a path inside the workspace."""
    hits = [e for e in entries if e["path"] and path.is_relative_to(e["path"])]
    return max(hits, key=lambda e: len(e["path"].parts), default=None)


def link_state(repo, key, target):
    link = repo["path"] / ".docs" / key
    if target is None:
        return "none"
    if not link.is_symlink():
        return "conflict" if link.exists() else "missing"
    expected = os.path.relpath(target, link.parent)
    if os.readlink(link) != expected:
        return "wrong"
    return "ok" if link.exists() else "dangling"


def context(args):
    start = below_home(args.path or Path.cwd())
    root = locate_root(start, args.root)
    workspace = workspace_of(root, start)
    return root, workspace, start


def rel(workspace, path):
    return path.relative_to(workspace).as_posix() if path else None


def show(value):
    return "null" if value is None else value


def cmd_where(args):
    root, workspace, start = context(args)
    print(f"root: {root}")
    if workspace is None:
        print("workspace: null  # 当前在根目录，不枚举工作区，请指定工作区")
        return 0
    entries = load(workspace)
    print(f"workspace: {workspace.name}")
    repo = match(workspace, entries, start)
    if repo is None:
        print("repo: null")
        print("repos:")
        for e in entries:
            print(f"  - {e['project']}/{e['name']}: {e['path_rel']}")
    else:
        print(f"project: {repo['project']}")
        print(f"repo: {repo['name']}")
        print(f"repo_path: {repo['path_rel']}")
        for key in KINDS:
            print(f"{key}: {show(repo[key + '_rel'])}  # .docs/{key}: {link_state(repo, key, repo[key])}")
        if repo["project"] != "_":
            print("siblings:")
            for e in entries:
                if e["project"] == repo["project"] and e is not repo:
                    print(f"  - {e['name']}: path={e['path_rel']} change={show(e['change_rel'])} wiki={show(e['wiki_rel'])}")
    print(f"searchable: [{workspace.name}]")
    print(f"excluded: [{workspace.name}/knowledge]")
    return 0


def cmd_check(args):
    _, workspace, _ = context(args)
    if workspace is None:
        raise WsError("请在某个工作区内运行，或用 --path 指定")
    entries = load(workspace)
    found = problems(workspace, entries)
    for e in entries:
        if e["path"] and e["path"].is_dir():
            for key in KINDS:
                state = link_state(e, key, e[key])
                if state in {"wrong", "dangling", "conflict"}:
                    found.append(f"{e['project']}/{e['name']}: .docs/{key} 状态 {state}")
    for line in found:
        print(f"问题: {line}")
    print("校验通过" if not found else f"共 {len(found)} 个问题")
    return 1 if found else 0


def cmd_sync_docs(args):
    root, workspace, start = context(args)
    if workspace is None:
        raise WsError("请在某个仓库内运行，或用 --path 指定仓库")
    entries = load(workspace)
    broken = problems(workspace, entries)
    repo = match(workspace, entries, start)
    if repo is None:
        raise WsError(f"{start} 不属于 index.yaml 登记的任何仓库")
    label = f"{repo['project']}/{repo['name']}"
    blocking = [p for p in broken if label in p or repo["path_rel"] in p]
    if blocking:
        raise WsError("索引存在问题，未建立链接: " + "; ".join(blocking))
    docs = repo["path"] / ".docs"
    if docs.is_symlink() or (docs.exists() and not docs.is_dir()):
        raise WsError(f".docs 不是普通目录，未覆盖: {docs}")
    for key in KINDS:
        target = repo[key]
        if target is None:
            print(f"{key}: 索引为 null，跳过")
            continue
        state = link_state(repo, key, target)
        if state == "ok":
            print(f"{key}: 已就绪")
            continue
        if state in {"conflict", "wrong"}:
            raise WsError(f".docs/{key} 已存在且不符合预期，未覆盖: {docs / key}")
        if args.dry_run:
            print(f"{key}: 将创建 {rel(workspace, target)} 并建立链接 ({state})")
            continue
        target.mkdir(parents=True, exist_ok=True)
        docs.mkdir(exist_ok=True)
        link = docs / key
        if state == "dangling":
            link.unlink()
        link.symlink_to(os.path.relpath(target, docs), target_is_directory=True)
        resolved = link.resolve(strict=True)
        if not resolved.is_relative_to(workspace.resolve()):
            link.unlink()
            raise WsError(f".docs/{key} 解析到工作区之外，已撤销: {resolved}")
        print(f"{key}: 已建立 -> {rel(workspace, target)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="显式指定根目录，优先于环境变量")
    parser.add_argument("--path", help="要解析的路径，默认当前目录")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("where", help="输出当前位置的工作区、项目、仓库与映射")
    commands.add_parser("check", help="校验 index.yaml 与 .docs 链接")
    sync = commands.add_parser("sync-docs", help="为当前仓库建立 .docs 链接")
    sync.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    handler = {"where": cmd_where, "check": cmd_check, "sync-docs": cmd_sync_docs}[args.command]
    try:
        return handler(args)
    except (OSError, WsError) as error:
        print(f"错误: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
