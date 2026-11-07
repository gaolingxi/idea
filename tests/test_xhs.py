import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

spec=importlib.util.spec_from_file_location("collector",Path(__file__).resolve().parents[1]/"scripts"/"xhs_approved_ingest.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CollectorTests(unittest.TestCase):
    def test_reject_untrusted_url(self):
        with self.assertRaises(ValueError): mod.normalize("https://example.com")
    def test_reject_missing_permission(self):
        with self.assertRaises(PermissionError): mod.authorization({"allow_collect":"no"})
    def test_date(self):
        self.assertEqual(mod.date_scope("2020-01-01"),"outside_24m")
        self.assertEqual(mod.date_scope(""),"unknown_date")
    def test_sqlite_dedup(self):
        with TemporaryDirectory() as d:
            db=mod.connect(Path(d)/"test.db")
            row={"source_url":"https://www.xiaohongshu.com/explore/test",
                 "published_at":"2026-10-01","allow_collect":"yes",
                 "rights_basis":"written consent",
                 "authorization_reference":"ref-001"}
            self.assertEqual(mod.write_note(db,row,"authorized_export")[0],1)
            self.assertEqual(mod.write_note(db,row,"authorized_export")[0],0)
            db.close()
    def test_meta(self):
        p=mod.MetaParser()
        p.feed('<html><head><meta property="og:title" content="Test"></head></html>')
        self.assertEqual(p.extract()[0],"Test")

if __name__=="__main__": unittest.main()
