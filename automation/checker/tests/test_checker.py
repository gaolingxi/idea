import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("canonical_checker", HERE / "checker.py")
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(checker)


class CheckerTemplateTests(unittest.TestCase):
    def test_normalize_github_urls(self):
        expected = "gaolingxi/demo"
        self.assertEqual(checker.normalize_slug("https://github.com/gaolingxi/demo.git"), expected)
        self.assertEqual(checker.normalize_slug("git@github.com:gaolingxi/demo.git"), expected)
        self.assertEqual(checker.normalize_slug("ssh://git@github.com/gaolingxi/demo.git"), expected)

    def test_headers_first_occurrence_wins(self):
        text = "TASK_ID: T1\nSTATUS: PENDING\n\n## body\nSTATUS: BLOCKED\n"
        fields = checker.headers(text)
        self.assertEqual(fields["TASK_ID"], "T1")
        self.assertEqual(fields["STATUS"], "PENDING")

    def test_report_only_blocks_same_task_version(self):
        report = {"TASK_ID": "T1", "TASK_VERSION": "1", "STATUS": "BLOCKED"}
        self.assertTrue(checker.report_blocks(report, "T1", "1"))
        self.assertFalse(checker.report_blocks(report, "T1", "2"))
        self.assertFalse(checker.report_blocks(report, "T2", "1"))

    def test_split_required_files(self):
        self.assertEqual(checker.split_paths("a.do;b.md|c.csv"), ["a.do", "b.md", "c.csv"])

    def test_stale_lock_is_recovered(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "checker.lock"
            path.write_text(json.dumps({"pid": 99999999, "created_epoch": time.time() - 9999}), encoding="utf-8")
            lock = checker.LeaseLock(path, stale_seconds=60)
            self.assertTrue(lock.acquire())
            self.assertTrue(path.exists())
            lock.release()
            self.assertFalse(path.exists())

    def test_live_recent_lock_is_not_stolen(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "checker.lock"
            path.write_text(json.dumps({"pid": os.getpid(), "created_epoch": time.time()}), encoding="utf-8")
            lock = checker.LeaseLock(path, stale_seconds=180)
            self.assertFalse(lock.acquire())

    def test_orca_list_fallback_never_sends_to_other_repo(self):
        with tempfile.TemporaryDirectory() as d:
            idea = Path(d) / "idea"
            other = Path(d) / "consump"
            idea.mkdir()
            other.mkdir()

            def response(repo, args, timeout=30):
                if "--worktree" in args:
                    raise checker.NotReady("ORCA_CLI_FAILED:unknown_option")
                return {"ok": True, "result": {"terminals": [
                    {"handle": "other", "agentIdentity": "opencode",
                     "connected": True, "writable": True, "worktreePath": str(other)},
                    {"handle": "mine", "agentIdentity": "opencode",
                     "connected": True, "writable": True, "worktreePath": str(idea)}
                ]}}

            with mock.patch.object(checker, "orca_json", side_effect=response):
                self.assertEqual(checker.choose_terminal(idea, None), "mine")

            def only_other(repo, args, timeout=30):
                if "--worktree" in args:
                    raise checker.NotReady("ORCA_CLI_FAILED:unknown_option")
                return {"ok": True, "result": {"terminals": [
                    {"handle": "other", "agentIdentity": "opencode",
                     "connected": True, "writable": True, "worktreePath": str(other)}
                ]}}

            with mock.patch.object(checker, "orca_json", side_effect=only_other):
                with self.assertRaisesRegex(checker.NotReady, "ORCA_OPENCODE_NOT_FOUND"):
                    checker.choose_terminal(idea, None)

    def test_orca_cli_failure_reports_safe_code(self):
        with mock.patch.object(checker, "orca_raw", return_value=(1, {"ok":False,"error":{"code":"invalid_arguments","message":"secret local path"}})):
            with self.assertRaisesRegex(checker.NotReady, "^ORCA_CLI_FAILED:invalid_arguments$"):
                checker.orca_json(Path("."), ["terminal","list"])

    def test_explicit_parent_workspace_matches_only_idea(self):
        with tempfile.TemporaryDirectory() as d:
            idea = Path(d) / "idea"
            root = idea / "repo"
            root.mkdir(parents=True)
            sibling = Path(d) / "consump"
            sibling.mkdir()

            def response(repo, args, timeout=30):
                if "--worktree" in args:
                    selected = args[args.index("--worktree") + 1].split("path:", 1)[1]
                    terms = [
                        {"handle": "idea-parent", "agentIdentity": "opencode",
                         "connected": True, "writable": True, "orphaned": False,
                         "worktreePath": str(idea)},
                        {"handle": "consump", "agentIdentity": "opencode",
                         "connected": True, "writable": True, "orphaned": False,
                         "worktreePath": str(sibling)}
                    ]
                    # Even a buggy unfiltered Orca reply cannot cross project boundaries.
                    return {"ok": True, "result": {"terminals": terms}}
                return {"ok": True, "result": {"terminals": []}}
            with mock.patch.object(checker, "orca_json", side_effect=response):
                with self.assertRaisesRegex(checker.NotReady, "ORCA_OPENCODE_NOT_FOUND"):
                    checker.choose_terminal(root, None)
                self.assertEqual(checker.choose_terminal(root, None, idea), "idea-parent")

    def test_two_valid_idea_opencode_terminals_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "idea" / "repo"
            root.mkdir(parents=True)
            idea = root.parent
            def response(repo, args, timeout=30):
                if "--worktree" in args and str(idea) in args[args.index("--worktree")+1]:
                    return {"ok": True, "result": {"terminals": [
                        {"handle": handle, "agentIdentity": "opencode", "connected": True,
                         "writable": True, "worktreePath": str(idea)} for handle in ("a", "b")
                    ]}}
                return {"ok": True, "result": {"terminals": []}}
            with mock.patch.object(checker, "orca_json", side_effect=response):
                with self.assertRaisesRegex(checker.NotReady, "ORCA_OPENCODE_AMBIGUOUS"):
                    checker.choose_terminal(root, None, idea)
                self.assertEqual(checker.choose_terminal(root, "b", idea), "b")


if __name__ == "__main__":
    unittest.main()
