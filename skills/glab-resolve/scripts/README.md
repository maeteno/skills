# Scripts 使用文档

本目录包含用于获取和处理 GitLab MR 讨论线程的辅助脚本。

## 📋 脚本列表

| 脚本 | 用途 | 输入 | 输出 |
|------|------|------|------|
| [get_project_name.sh](#get_project_namesh) | 获取项目路径 | 无 | URL 编码的项目路径 |
| [filter_unprocessed.py](#filter_unprocessedpy) | 过滤未处理线程 | discussions JSON | 简化的线程 JSON |
| [fetch_discussions.sh](#fetch_discussionssh) | 获取 MR 未处理线程 | MR ID | 简化的线程 JSON |

---

## 🔧 详细说明

### get_project_name.sh

**用途**: 获取当前 GitLab 项目的 URL 编码路径（用于 API 调用）

**用法**:
```bash
./get_project_name.sh
```

**输出示例**:
```
maeteno%2Fskills
```

**工作原理**:
1. 使用 `glab repo view` 获取项目信息
2. 提取 `path_with_namespace` 字段
3. 对路径进行 URL 编码（保留 `/` 字符）

**依赖**:
- `glab` - GitLab CLI 工具
- `jq` - JSON 处理工具
- `uv` - Python 运行环境

---

### filter_unprocessed.py

**用途**: 从 GitLab discussions API 响应中过滤出未处理的 diff 评论线程

**用法**:
```bash
# 从文件读取
./filter_unprocessed.py discussions.json

# 从标准输入读取
glab api "projects/xxx/merge_requests/123/discussions" | ./filter_unprocessed.py -
```

**输入**: GitLab discussions API 返回的 JSON 数组

**过滤条件**:
- `type == "DiffNote"` - 只保留 diff 评论
- `resolvable == true` - 可解决的线程
- `resolved == false` - 未解决的线程

**输出格式**:
```json
[
  {
    "discussion_id": "abc123",
    "author": "张三",
    "comment": "这里有个 typo",
    "position": {
      "new_path": "src/main.py",
      "new_line": 42,
      "old_path": "src/main.py",
      "old_line": null
    },
    "replies": [
      {
        "author": "李四",
        "comment": "同意，需要修正"
      }
    ]
  }
]
```

**字段说明**:
- `discussion_id`: 讨论 ID（用于后续 resolve API）
- `author`: 评论作者
- `comment`: 评论内容
- `position`: 文件位置信息
- `replies`: 回复列表

**依赖**:
- Python 3.6+

---

### fetch_discussions.sh

**用途**: 获取指定 MR 的所有未处理讨论线程（组合脚本）

**用法**:
```bash
./fetch_discussions.sh <MR_ID>
```

**参数**:
- `MR_ID`: GitLab Merge Request ID（必需）

**示例**:
```bash
# 获取 MR #123 的未处理讨论
./fetch_discussions.sh 123
```

**输出**: 与 `filter_unprocessed.py` 相同的 JSON 格式

**工作流程**:
1. 调用 `get_project_name.sh` 获取项目路径
2. 使用 `glab api --paginate` 获取所有 discussions（自动处理分页）
3. 合并分页结果（`jq -s 'add'`）
4. 通过 `filter_unprocessed.py` 过滤未处理线程

**依赖**:
- `glab` - GitLab CLI 工具
- `jq` - JSON 处理工具
- `uv` - Python 运行环境
- `get_project_name.sh` - 项目路径脚本
- `filter_unprocessed.py` - 过滤脚本

---

## 🚀 快速开始

### 前置要求

确保已安装以下工具：

```bash
# 检查 glab
glab --version

# 检查 jq
jq --version

# 检查 uv
uv --version

# 检查 GitLab 认证状态
glab auth status
```

### 基本使用

```bash
# 1. 进入项目目录
cd /path/to/your/gitlab/project

# 2. 获取 MR 未处理讨论
./scripts/fetch_discussions.sh 123

# 3. 保存到文件（可选）
./scripts/fetch_discussions.sh 123 > discussions.json
```

---

## 🔍 故障排查

### 错误: `glab: command not found`

**原因**: 未安装 GitLab CLI

**解决**:
```bash
# macOS
brew install glab

# Linux
# 参考: https://gitlab.com/gitlab-org/cli#installation
```

### 错误: `jq: command not found`

**原因**: 未安装 jq

**解决**:
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

### 错误: `uv: command not found`

**原因**: 未安装 uv

**解决**:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 错误: `glab auth status: not authenticated`

**原因**: 未认证 GitLab

**解决**:
```bash
glab auth login
```

### 错误: `404 Not Found`

**原因**: MR ID 不存在或无权限访问

**解决**:
1. 确认 MR ID 是否正确
2. 检查是否有项目访问权限
3. 确认当前目录是否为正确的 GitLab 项目

### 输出为空数组 `[]`

**原因**: MR 中没有未处理的 diff 评论线程

**说明**: 这是正常情况，表示所有线程已解决或没有 diff 评论

---

## 📝 开发说明

### 脚本设计原则

1. **单一职责**: 每个脚本只做一件事
2. **可组合性**: 脚本之间可以组合使用
3. **标准化输出**: 统一使用 JSON 格式
4. **错误处理**: 使用 `set -euo pipefail` 确保错误时退出

### 扩展建议

如需扩展功能，建议：

1. 创建新的独立脚本
2. 保持与现有脚本的接口一致
3. 更新本文档说明新脚本的用法

---

## 📚 相关链接

- [GitLab Discussions API](https://docs.gitlab.com/ee/api/discussions.html)
- [GitLab CLI (glab) 文档](https://gitlab.com/gitlab-org/cli)
- [jq 手册](https://stedolan.github.io/jq/manual/)
