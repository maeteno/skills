"""Strict reader for the fixed workspace index.yaml schema (no third-party YAML)."""

from pathlib import PurePosixPath

from ws_root import WsError

PROJECT_KEYS = {"name", "repos"}
REPO_KEYS = {"name", "path", "change", "wiki"}


def scalar(text, line_no):
    text = text.strip()
    if text in {"null", "~", ""}:
        return None
    if text[0] in "\"'":
        if len(text) < 2 or text[-1] != text[0]:
            raise WsError(f"index.yaml 第 {line_no} 行: 引号未闭合")
        return text[1:-1]
    return text.split(" #", 1)[0].strip()


def tokens(text):
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise WsError(f"index.yaml 第 {number} 行: 不支持制表符缩进")
        yield number, len(raw) - len(raw.lstrip()), raw.strip()


def split_pair(body, number):
    key, sep, value = body.partition(":")
    if not sep:
        raise WsError(f"index.yaml 第 {number} 行: 需要 key: value")
    return key.strip(), value.strip()


def parse(text):
    """Return [{'name', 'repos': [{'name','path','change','wiki'}]}]; reject duplicates."""
    projects, project, repo, seen = [], None, None, set()
    header = False
    for number, indent, body in tokens(text):
        if indent == 0:
            key, value = split_pair(body, number)
            if key != "project" or header:
                raise WsError(f"index.yaml 第 {number} 行: 顶层只允许一个 project")
            if value not in {"", "[]"}:
                raise WsError(f"index.yaml 第 {number} 行: project 必须是列表")
            header = True
        elif indent == 2 and body.startswith("- "):
            key, value = split_pair(body[2:], number)
            if key != "name":
                raise WsError(f"index.yaml 第 {number} 行: 项目条目须以 name 开头")
            project, repo = {"name": scalar(value, number), "repos": []}, None
            projects.append(project)
            seen = {"name"}
        elif indent == 4 and project is not None and not body.startswith("- "):
            key, value = split_pair(body, number)
            if key not in PROJECT_KEYS or key in seen:
                raise WsError(f"index.yaml 第 {number} 行: 项目字段无效或重复: {key}")
            seen.add(key)
            if key == "repos" and value not in {"", "[]"}:
                raise WsError(f"index.yaml 第 {number} 行: repos 必须是列表")
            if key == "name":
                project["name"] = scalar(value, number)
        elif indent == 6 and project is not None and body.startswith("- "):
            key, value = split_pair(body[2:], number)
            if key != "name":
                raise WsError(f"index.yaml 第 {number} 行: 仓库条目须以 name 开头")
            repo = {"name": scalar(value, number), "path": None, "change": None, "wiki": None}
            project["repos"].append(repo)
            seen = {"name"}
        elif indent == 8 and repo is not None:
            key, value = split_pair(body, number)
            if key not in REPO_KEYS or key in seen:
                raise WsError(f"index.yaml 第 {number} 行: 仓库字段无效或重复: {key}")
            seen.add(key)
            repo[key] = scalar(value, number)
        else:
            raise WsError(f"index.yaml 第 {number} 行: 缩进或结构不符合固定 schema")
    if not header:
        raise WsError("index.yaml 缺少顶层 project")
    return projects


def normalize(value):
    """Collapse './', repeated and trailing separators; reject absolute and '..' paths."""
    if value is None:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise WsError(f"路径必须是工作区内的相对路径，不能含绝对路径或 '..': {value}")
    return path.as_posix()
