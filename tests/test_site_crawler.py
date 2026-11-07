import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("site",Path(__file__).resolve().parents[1]/"scripts"/"crawl_official_sites.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

class TestSiteCrawler(unittest.TestCase):
    def test_status(self):
        self.assertEqual(site.classify("2026年度项目立项公示","funded_project"),"proposed")
        self.assertEqual(site.classify("2026年度项目立项公告","funded_project"),"formal_or_reported_award")
        self.assertEqual(site.classify("2026年项目申报指南","funded_project"),"call_or_guidance")
    def test_dates(self):
        self.assertEqual(site.date_from("发布日期：2026/09/08 10:35"),"2026-09-08")
        self.assertEqual(site.date_from("2025年9月2日"),"2025-09-02")
        self.assertEqual(site.date_from("2026年14月1日"),"")
    def test_host_security(self):
        self.assertTrue(site.allowed("https://jkw.mof.gov.cn/index.html",["mof.gov.cn"]))
        self.assertFalse(site.allowed("https://mof.gov.cn.attacker.com/",["mof.gov.cn"]))
    def test_h1(self):
        soup,title,text=site.html_data('<html><body><h1>2026年度科研立项公告</h1><p>2026年9月8日</p></body></html>'.encode('utf-8'),"utf-8")
        self.assertEqual(title,"2026年度科研立项公告")
        self.assertEqual(site.extract_dates(soup,text)[0],"2026-09-08")
if __name__ == "__main__":
    unittest.main()
