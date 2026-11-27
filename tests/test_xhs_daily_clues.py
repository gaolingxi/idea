import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_xhs_daily_clues", ROOT / "scripts" / "prepare_xhs_daily_clues.py"
)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
TZ = timezone(timedelta(hours=8))


class XhsDailyCluesTests(unittest.TestCase):
    def test_load_registry_has_four_active_accounts(self):
        accounts, categories = MOD.load_registry(ROOT / "sources" / "xhs_account_registry.json")
        self.assertEqual(
            set(accounts.keys()),
            {"Kenny思享", "大山经管资料", "iiiiop", "土豆学姐（研究ing）"},
        )
        self.assertIn("policy_macro", categories)
        self.assertIn("empirical_data", categories)

    def test_init_templates_creates_both_files(self):
        with TemporaryDirectory() as d:
            created = MOD.init_templates(Path(d))
            self.assertEqual(len(created), 2)
            self.assertTrue((Path(d) / "daily_approved_clues.template.csv").is_file())
            self.assertTrue((Path(d) / "public_clue_leads.template.csv").is_file())

    def test_build_approved_clues_and_snapshot(self):
        now = datetime(2026, 11, 27, 20, 0, tzinfo=TZ)
        with TemporaryDirectory() as d:
            tmp = Path(d)
            csv_path = tmp / "daily_approved_clues.csv"
            csv_path.write_text(
                "account,published_at,source_url,concept,topic_category,primary_source_url,allow_collect,allow_public_share,authorization_reference\n"
                "Kenny思享,2026-11-26T10:00:00+08:00,https://www.xiaohongshu.com/explore/0123456789abcdef01234567?xsec_token=secret,统一大市场与跨区要素流动实证设计,policy_macro,https://www.gov.cn/zhengce/example.htm?ref=1,yes,yes,user-export-20261127\n"
                "未核实账号,2026-11-26T10:00:00+08:00,https://www.xiaohongshu.com/explore/0123456789abcdef01234568,会被拒绝的账号,policy_macro,,yes,yes,user-export-20261127\n"
                "大山经管资料,2026-11-26T10:00:00+08:00,https://www.xiaohongshu.com/explore/0123456789abcdef01234569,无授权行,empirical_data,,no,yes,user-export-20261127\n",
                encoding="utf-8-sig",
            )
            out_path = tmp / "sources" / "xhs_daily" / "latest.json"
            payload = MOD.build_approved_clues(
                src=csv_path,
                registry_path=ROOT / "sources" / "xhs_account_registry.json",
                out=out_path,
                window_days=14,
                now=now,
            )
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["rejected"], 2)
            self.assertEqual(payload["records"][0]["source_url"], "https://www.xiaohongshu.com/explore/0123456789abcdef01234567")
            self.assertEqual(payload["records"][0]["primary_source_url"], "https://www.gov.cn/zhengce/example.htm")
            snapshot = tmp / "sources" / "xhs_daily" / "snapshots" / "2026-11-27.json"
            self.assertTrue(snapshot.is_file())
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["count"], 1)

    def test_build_public_leads_rejects_xhs_url_as_primary(self):
        now = datetime(2026, 11, 27, 20, 0, tzinfo=TZ)
        with TemporaryDirectory() as d:
            tmp = Path(d)
            csv_path = tmp / "public_clue_leads.csv"
            csv_path.write_text(
                "discovered_date,topic_category,concept,primary_source_type,primary_source_title,primary_source_url,primary_published_date,related_account_hint\n"
                "2026-11-27,policy_macro,绿色金融改革试验区与企业绿色创新,policy,关于深化绿色金融改革的通知,https://www.mof.gov.cn/example/2026.htm,2026-10-15,Kenny思享\n"
                "2026-11-27,policy_macro,不能拿小红书当一手源,policy,假一手源,https://www.xiaohongshu.com/explore/0123456789abcdef01234567,2026-10-15,Kenny思享\n",
                encoding="utf-8-sig",
            )
            out_path = tmp / "verified_public_leads.json"
            payload = MOD.build_public_leads(
                src=csv_path,
                registry_path=ROOT / "sources" / "xhs_account_registry.json",
                out=out_path,
                now=now,
            )
            self.assertIsNotNone(payload)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
