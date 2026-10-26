import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "work_dir.py"
SPEC = importlib.util.spec_from_file_location("work_dir", SCRIPT)
work_dir = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(work_dir)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".work-dir-test-", dir=SKILL)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "工作目录 with spaces"

    def initialize(self):
        work_dir.init(self.root).apply()

    def test_cli_creates_complete_layout_and_relative_link(self):
        for arguments in (["init", str(self.root)],
                          ["add-workspace", "团队 alpha", "--root", str(self.root)]):
            result = subprocess.run([sys.executable, str(SCRIPT), *arguments],
                                    cwd=self.base, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        workspace = self.root / "团队 alpha"
        self.assertEqual((workspace / "index.yaml").read_text(), "project: []\n")
        for path, kind in [(self.root, "ROOT"), (workspace, "WORKSPACE"),
                           (workspace / "repos", "REPOS"),
                           (workspace / "change", "CHANGE"),
                           (workspace / "wiki", "WIKI"),
                           (workspace / "knowledge", "KNOWLEDGE")]:
            self.assertEqual((path / "AGENTS.md").read_text().splitlines()[0], f"# {kind}")
        link = workspace / "knowledge"
        self.assertEqual(str(link.readlink()), "../knowledge/workspaces/团队 alpha")
        self.assertEqual(link.resolve(), self.root / "knowledge/workspaces/团队 alpha")

    def test_repeated_runs_preserve_unmanaged_content(self):
        self.initialize()
        work_dir.add_workspace(self.root, "team").apply()
        untouched = self.root / "knowledge/workspaces/team/private.txt"
        untouched.write_text("人工知识")
        rule = self.root / "team/AGENTS.md"
        previous = rule.stat().st_mtime_ns
        self.assertEqual(work_dir.init(self.root).apply()[0], 0)
        self.assertEqual(work_dir.add_workspace(self.root, "team").apply()[0], 0)
        self.assertEqual(untouched.read_text(), "人工知识")
        self.assertEqual(rule.stat().st_mtime_ns, previous)

    def test_existing_root_rules_are_not_overwritten(self):
        self.root.mkdir()
        rules = self.root / "AGENTS.md"
        rules.write_text("# ROOT\n\n定制规则\n")
        with self.assertRaises(work_dir.Conflict):
            work_dir.init(self.root).apply()
        self.assertEqual(rules.read_text(), "# ROOT\n\n定制规则\n")
        self.assertFalse((self.root / "knowledge").exists())

    def test_nonempty_index_stops_before_creating_missing_nodes(self):
        self.initialize()
        workspace = self.root / "team"
        workspace.mkdir()
        index = workspace / "index.yaml"
        index.write_text("project:\n  - name: existing\n    repos: []\n")
        with self.assertRaises(work_dir.Conflict):
            work_dir.add_workspace(self.root, "team").apply()
        self.assertEqual(list(workspace.iterdir()), [index])
        self.assertFalse((self.root / "knowledge/workspaces/team").exists())

    def test_workspace_symlink_is_rejected_without_writing_target(self):
        self.initialize()
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "team").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(work_dir.Conflict):
            work_dir.add_workspace(self.root, "team").apply()
        self.assertEqual(list(outside.iterdir()), [])

    def test_knowledge_container_symlink_is_rejected(self):
        self.root.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "knowledge").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(work_dir.Conflict):
            work_dir.init(self.root).apply()
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_incorrect_knowledge_link_is_preserved_and_rejected(self):
        self.initialize()
        workspace = self.root / "team"
        workspace.mkdir()
        link = workspace / "knowledge"
        link.symlink_to("../missing")
        with self.assertRaises(work_dir.Conflict):
            work_dir.add_workspace(self.root, "team").apply()
        self.assertEqual(str(link.readlink()), "../missing")
        self.assertFalse((workspace / "AGENTS.md").exists())

    def test_workspace_requires_initialized_root(self):
        with self.assertRaises(work_dir.Conflict):
            work_dir.add_workspace(self.root, "team")
        self.assertFalse(self.root.exists())

    def test_rejects_invalid_and_reserved_workspace_names(self):
        self.initialize()
        for name in ["", ".", "..", "../escape", "/absolute", "a/b", "a\\b",
                     "team\n", "knowledge", "KNOWLEDGE", "AGENTS.md"]:
            with self.subTest(name=name), self.assertRaises(work_dir.Conflict):
                work_dir.add_workspace(self.root, name)

    def test_physical_home_boundary(self):
        home = Path.home().resolve()
        for path in [home, home.parent, home.parent / (home.name + "-other")]:
            with self.subTest(path=path), self.assertRaises(work_dir.Conflict):
                work_dir.physical_below_home(path)
        alias = self.base / "home-alias"
        alias.symlink_to(home, target_is_directory=True)
        with self.assertRaises(work_dir.Conflict):
            work_dir.physical_below_home(alias)
        self.assertEqual(work_dir.physical_below_home(self.root), self.root)


if __name__ == "__main__":
    unittest.main()
