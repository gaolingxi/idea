import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"scripts"))
path=HERE/"scripts"/"collect_nsfc_awards_from_universities.py"
spec=importlib.util.spec_from_file_location("nsfc_awards_seed",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class NsfcPublicAwardsParserTest(unittest.TestCase):
    def test_real_world_university_header_formats(self):
        sample={
            "id":"nankai_economics_2026","year":2026,
            "institution":"南开大学","unit":"经济学院",
            "url":"https://economics.nankai.edu.cn/2026/0827/c15998a601524/page.htm",
        }
        html="""<html><body><table>
        <tr><td>项目批准号</td><td>负责人</td><td>项目名称</td><td>项目类别</td></tr>
        <tr><td>72673088</td><td>丁思华</td><td>连接的生产与网络的形成：微观理论研究</td><td>面上项目</td></tr>
        </table></body></html>"""
        rows=module.parse_tables(html,sample)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["approval_number"],"72673088")
        self.assertEqual(rows[0]["principal_investigator"],"丁思华")
        self.assertEqual(rows[0]["award_year"],"2026")
        self.assertEqual(rows[0]["collection_scope"],"partial_institution_records_not_nationwide")

    def test_undecorated_utf8_response_with_latin1_fallback(self):
        sample={"id":"nankai_economics_2026","year":2026,
                "institution":"南开大学","unit":"经济学院",
                "url":"https://economics.nankai.edu.cn/2026/0827/c15998a601524/page.htm"}
        html="""<table><tr><th>项目批准号</th><th>负责人</th><th>项目名称</th><th>项目类别</th></tr>
        <tr><td>72673088</td><td>丁思华</td><td>连接的生产与网络的形成：微观理论研究</td><td>面上项目</td></tr></table>"""
        raw=html.encode("utf-8")
        soup=module.parse_html_response(raw,"ISO-8859-1")
        result=module.parse_tables(str(soup),sample)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["project_title"],"连接的生产与网络的形成：微观理论研究")

    def test_sequence_number_not_used_as_approval_number(self):
        sample={
            "id":"hunnu_physics_2025","year":2025,
            "institution":"湖南师范大学","unit":"物理与电子科学学院",
            "url":"https://wdy.hunnu.edu.cn/info/1041/9024.htm",
        }
        html="""<table>
        <tr><th>序号</th><th>项目批准号</th><th>负责人</th><th>项目名称</th><th>项目类别</th></tr>
        <tr><td>1</td><td>92576206</td><td>彭智慧</td><td>微波单光子探测及其在轴子和暗光子研究中的应用</td><td>重大研究计划项目</td></tr>
        </table>"""
        rows=module.parse_tables(html,sample)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["approval_number"],"92576206")

    def test_announcement_without_project_numbers_not_counted(self):
        sample={"id":"notice","year":2026,"institution":"甲大学","unit":"乙学院",
                "url":"https://example.edu.cn/notice"}
        html="""<table><tr><td>项目名称</td><td>负责人</td><td>项目类别</td></tr>
        <tr><td>2026国家自然科学基金合计69563项</td><td>公示</td><td>综合</td></tr></table>"""
        self.assertEqual(module.parse_tables(html,sample),[])

if __name__=="__main__":
    unittest.main()
