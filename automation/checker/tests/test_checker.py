import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

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


if __name__ == "__main__":
    unittest.main()
