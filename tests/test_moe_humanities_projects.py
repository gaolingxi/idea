import importlib.util
from pathlib import Path
import unittest

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("moe_humanities",root/"scripts"/"collect_moe_humanities_projects.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestMoeHumanities(unittest.TestCase):
    def test_table_headers_2025(self):
        header=["序号","学科门类","项目名称","项目类别","项目批准号","申请人","学校名称"]
        pos,mapping=mod.columns_from_head([header,["1","应用经济学","示例题目","青年基金项目","25YJC790000","李某","某大学"]])
        self.assertEqual(pos,0)
        self.assertEqual(mapping["project_title"],2)
        self.assertEqual(mapping["principal_investigator"],5)
        self.assertEqual(mapping["project_approval_number"],4)
    def test_publicity_2026_no_approval_number_is_allowed_in_header(self):
        header=["序号","学科","项目名称","项目类别","负责人","学校名称"]
        pos,mapping=mod.columns_from_head([header])
        self.assertEqual(pos,0)
        self.assertNotIn("project_approval_number",mapping)
        self.assertEqual(mapping["university"],5)
    def test_total_expected_2025_2026(self):
        import json
        src=json.loads((root/"sources"/"moe_humanities_2025_2026_registry.json").read_text("utf-8"))
        groups=src["groups"]
        self.assertEqual(sum(x["expected"] for x in groups if x["year"]==2025),3267)
        self.assertEqual(sum(x["expected"] for x in groups if x["year"]==2026),2713)
        self.assertTrue(all(x["status"]=="formal_award" for x in groups if x["year"]==2025))
        self.assertTrue(all(x["status"]=="public_review_not_formal_award" for x in groups if x["year"]==2026))
    def test_disallows_extra_domains(self):
        import requests
        with self.assertRaisesRegex(PermissionError,"allowlist"):
            mod.get_url_with_policy(requests.Session(),"https://example.org/hidden.pdf",["www.moe.gov.cn"],{})

if __name__=="__main__":
    unittest.main()
