from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
WS = SCRIPTS / "ws.py"
sys.path.insert(0, str(SCRIPTS))

import ws_index  # noqa: E402
import ws_root  # noqa: E402

INDEX = """project:
  - name: "app"
    repos:
      - name: "front"
        path: "repos/app/front"
        change: "change/app"
        wiki: null
      - name: "back"
        path: "repos/app/back"
        change: "change/app"
        wiki: "wiki/app/back"
  - name: _
    repos:
      - name: "solo"
        path: "repos/solo"
        change: "change/solo"
        wiki: null
"""


class Base(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix=".ws-test-", dir=SKILL)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "root"
        self.workspace = self.root / "w1"
        (self.root / "knowledge" / "workspaces" / "w1").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("# ROOT\n")
        (self.workspace / "AGENTS.md").parent.mkdir(parents=True)
        (self.workspace / "AGENTS.md").write_text("# WORKSPACE\n")
        (self.workspace / "index.yaml").write_text(INDEX)
        for repo in ("app/front", "app/back", "solo"):
            (self.workspace / "repos" / repo).mkdir(parents=True)

    def run_ws(self, *arguments, cwd=None):
        return subprocess.run([sys.executable, str(WS), "--root", str(self.root), *arguments],
                              cwd=cwd or self.workspace / "repos/app/front",
                              capture_output=True, text=True)


class IndexTests(unittest.TestCase):
    def test_parses_projects_and_nulls(self):
        projects = ws_index.parse(INDEX)
        self.assertEqual([p["name"] for p in projects], ["app", "_"])
        self.assertIsNone(projects[0]["repos"][0]["wiki"])
        self.assertEqual(projects[0]["repos"][1]["wiki"], "wiki/app/back")

    def test_empty_project_list(self):
        self.assertEqual(ws_index.parse("project: []\n"), [])

    def test_duplicate_keys_rejected(self):
        broken = INDEX.replace('        wiki: null\n', '        wiki: null\n        wiki: null\n', 1)
        with self.assertRaises(ws_root.WsError):
            ws_index.parse(broken)

    def test_escaping_paths_rejected(self):
        for value in ("../x", "/abs/x", "a/../../x"):
            with self.assertRaises(ws_root.WsError):
                ws_index.normalize(value)
        self.assertEqual(ws_index.normalize("./a//b/"), "a/b")


class RootTests(Base):
    def test_finds_root_from_nested_path(self):
        found = ws_root.locate_root(self.workspace / "repos/app/front", environ={})
        self.assertEqual(found, self.root)

    def test_env_overrides_probe(self):
        found = ws_root.locate_root(Path("/tmp"), environ={"WORKSPACES_ROOT": str(self.root)})
        self.assertEqual(found, self.root)

    def test_workspace_resolution(self):
        self.assertEqual(ws_root.workspace_of(self.root, self.workspace / "repos"), self.workspace)
        self.assertIsNone(ws_root.workspace_of(self.root, self.root))

    def test_knowledge_is_not_a_workspace(self):
        with self.assertRaises(ws_root.WsError):
            ws_root.workspace_of(self.root, self.root / "knowledge" / "workspaces" / "w1")


class CliTests(Base):
    def test_where_reports_siblings_and_isolation(self):
        result = self.run_ws("where")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("project: app", result.stdout)
        self.assertIn("repo: front", result.stdout)
        self.assertIn("- back:", result.stdout)
        self.assertIn("wiki: null", result.stdout)
        self.assertIn("excluded: [w1/knowledge]", result.stdout)
        self.assertNotIn("solo", result.stdout)

    def test_ungrouped_repo_has_no_siblings(self):
        result = self.run_ws("where", cwd=self.workspace / "repos/solo")
        self.assertNotIn("siblings", result.stdout)

    def test_where_at_root_does_not_enumerate_workspaces(self):
        result = self.run_ws("where", cwd=self.root)
        self.assertIn("workspace: null", result.stdout)
        self.assertNotIn("w1", result.stdout.replace("root:", ""))

    def test_sync_docs_creates_dirs_and_relative_link_idempotently(self):
        first = self.run_ws("sync-docs")
        self.assertEqual(first.returncode, 0, first.stderr)
        link = self.workspace / "repos/app/front/.docs/change"
        self.assertTrue(link.is_symlink())
        self.assertFalse(Path(link.readlink()).is_absolute())
        self.assertEqual(link.resolve(), (self.workspace / "change/app").resolve())
        self.assertFalse((self.workspace / "repos/app/front/.docs/wiki").exists())
        self.assertFalse((self.workspace / "wiki").exists())
        second = self.run_ws("sync-docs")
        self.assertEqual(second.returncode, 0)
        self.assertIn("已就绪", second.stdout)

    def test_sync_docs_refuses_to_overwrite_real_directory(self):
        real = self.workspace / "repos/app/front/.docs/change"
        real.mkdir(parents=True)
        result = self.run_ws("sync-docs")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(real.is_dir() and not real.is_symlink())

    def test_sync_docs_repairs_dangling_link(self):
        self.run_ws("sync-docs")
        (self.workspace / "change/app").rmdir()
        self.assertEqual(self.run_ws("check").returncode, 1)
        self.assertEqual(self.run_ws("sync-docs").returncode, 0)
        self.assertEqual(self.run_ws("check").returncode, 0)

    def test_dry_run_writes_nothing(self):
        self.run_ws("sync-docs", "--dry-run")
        self.assertFalse((self.workspace / "change").exists())
        self.assertFalse((self.workspace / "repos/app/front/.docs").exists())

    def test_check_flags_mapping_inside_repo(self):
        (self.workspace / "index.yaml").write_text(
            INDEX.replace('change: "change/solo"', 'change: "repos/solo/notes"'))
        result = self.run_ws("check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("位于已登记仓库之内", result.stdout)

    def test_check_flags_escaping_path(self):
        (self.workspace / "index.yaml").write_text(INDEX.replace("change/solo", "../other/solo"))
        self.assertEqual(self.run_ws("check").returncode, 2)


if __name__ == "__main__":
    unittest.main()
