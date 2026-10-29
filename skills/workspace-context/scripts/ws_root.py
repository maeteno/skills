"""Locate the work-dir root and the workspace that contains a path."""

import os
from pathlib import Path

ENV_ROOT = "WORKSPACES_ROOT"
CONFIG_FILE = "~/.config/workspaces/config"


class WsError(ValueError):
    pass


def first_line(path):
    try:
        if path.is_symlink() or not path.is_file():
            return None
        with path.open(encoding="utf-8") as stream:
            return stream.readline().strip()
    except (OSError, UnicodeDecodeError):
        return None


def below_home(path):
    resolved = Path(path).expanduser().resolve()
    home = Path.home().resolve()
    if resolved == home or not resolved.is_relative_to(home):
        raise WsError(f"路径必须是当前用户主目录的严格下级: {resolved}")
    return resolved


def is_root(path):
    return first_line(path / "AGENTS.md") == "# ROOT"


def configured_root():
    try:
        text = Path(CONFIG_FILE).expanduser().read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "root" and value.strip():
            return value.strip()
    return None


def locate_root(start, explicit=None, environ=None):
    """Priority: explicit option, env var, nearest '# ROOT' above start, config file."""
    environ = os.environ if environ is None else environ
    declared = explicit or environ.get(ENV_ROOT)
    if declared:
        root = below_home(declared)
        if not is_root(root):
            raise WsError(f"指定的目录没有声明 # ROOT 的 AGENTS.md: {root}")
        return root
    home = Path.home().resolve()
    for parent in (start, *start.parents):
        if parent == home or not parent.is_relative_to(home):
            break
        if is_root(parent):
            return parent
    fallback = configured_root()
    if fallback:
        root = below_home(fallback)
        if is_root(root):
            return root
    raise WsError(f"找不到根目录: 从 {start} 向上没有 # ROOT，且未设置 {ENV_ROOT} 或 {CONFIG_FILE}")


def workspace_of(root, path):
    """Return the workspace directory containing path, or None when path is the root itself."""
    if not path.is_relative_to(root):
        raise WsError(f"路径不在根目录内: {path}")
    parts = path.relative_to(root).parts
    if not parts:
        return None
    candidate = root / parts[0]
    kind = first_line(candidate / "AGENTS.md")
    if kind == "# KNOWLEDGE" or parts[0] == "knowledge":
        raise WsError("根目录级 KNOWLEDGE 不属于任何工作区，须由用户明确指定路径和范围后访问")
    if kind != "# WORKSPACE":
        raise WsError(f"{candidate} 没有声明 # WORKSPACE 的 AGENTS.md，不是工作区")
    return candidate
