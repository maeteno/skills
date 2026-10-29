# Skills

A collection of Claude Code skills for common development workflows.

## Available Skills

### git-commit

生成规范的 Git commit 信息，遵循 Conventional Commits 标准。分析暂存区变更，自动推断 commit 类型和范围，生成清晰准确的提交信息。

**触发方式：** `/commit`、"帮我提交"、"write a commit message"

---

### glab-resolve

交互式处理 GitLab MR 评论线程。按难易度分类问题，规划执行步骤，用户逐步确认后依次修复并提交，全程附带验证和汇总。

**触发方式：** `/glab-resolve`、`/glab-resolve <MR_ID>`、"resolve MR comments"、"处理 MR 评论"

---

### workspace-context

在任意目录感知本机工作目录根：当前位置所属的工作区、项目、仓库，同项目兄弟仓库，change/wiki 存放位置与搜索边界。附带 `ws.py`（`where`、`check`、`sync-docs`），可建立仓库内 `.docs/` 链接以免跨目录授权。红线常驻，细则按需读取，不依赖特定工具。

**触发方式：** "这个仓库的 change 放哪"、"同项目其他仓库"、"登记仓库"、"修复 .docs 链接"

---

### translate

中英文翻译与语法教学。支持纯中文、纯英文或中英混合输入，提供翻译结果并附语法分析，帮助学习和提升英文表达。

**触发方式：** "翻译"、"translate"、"帮我翻译"、"这句话语法对吗"

## Dev Tools

### skill-reviewer

代码审查工具，基于 Claude 分析代码变更，提供代码质量建议和改进方向。

**触发方式：** `/skill-reviewer`

**安装：**

```bash
pnpx skills add https://github.com/alienzhou/skill-reviewer --skill skill-reviewer
```
