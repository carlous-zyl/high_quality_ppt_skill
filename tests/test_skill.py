import unittest
import sys
import os
import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pipeline import OpenClawPPTSkill
from validators.consistency_checker import ConsistencyChecker
from validators.compliance_checker import ComplianceChecker

class TestOpenClawPPTSkill(unittest.TestCase):
    def setUp(self):
        """测试前初始化"""
        self.config_path = "config/global_config.yaml"
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.skill = OpenClawPPTSkill(config_path=self.config_path)
        # human_confirm 模式下注入自动确认回调，避免测试阻塞在终端 input()
        self.skill.set_confirm_callback(lambda check_point, details: True)
        self.consistency_checker = ConsistencyChecker(self.config)
        self.compliance_checker = ComplianceChecker(self.config)

    def test_step1_requirement_alignment_success(self):
        """测试需求对齐成功"""
        valid_requirement = {
            "核心主题": "测试主题",
            "目标受众": "测试受众",
            "汇报时长": "10分钟",
            "总页数": 5,
            "交付格式": ".pptx",
            "品牌VI": "默认咨询科技风",
            "内容禁忌": "无"
        }
        result = self.skill._step1_requirement_alignment(valid_requirement)
        self.assertIsNotNone(result)

    def test_step1_requirement_alignment_failure(self):
        """测试需求对齐失败（缺少参数）"""
        invalid_requirement = {
            "核心主题": "测试主题",
            "目标受众": "测试受众"
        }
        result = self.skill._step1_requirement_alignment(invalid_requirement)
        self.assertIsNone(result)

    def test_consistency_checker(self):
        """测试一致性校验"""
        mock_page_content = {
            "page1": {"font": {"title": self.config["vi_spec"]["title_font"], "body": self.config["vi_spec"]["body_font"]}}
        }
        mock_layout_spec = {
            "page1": {"colors": [self.config["vi_spec"]["primary_color"]], "margin": self.config["vi_spec"]["page_margin"]}
        }
        result = self.consistency_checker.check(mock_page_content, mock_layout_spec)
        self.assertTrue(result)

    def test_compliance_checker(self):
        """测试合规性校验"""
        mock_page_content = {
            "page1": {"body": "这是一段测试文字，字数较少"}
        }
        mock_layout_spec = {
            "page1": {"contrast_ratio": 5.0, "min_font_size": 16, "logo_position": self.config["vi_spec"]["logo_position"]}
        }
        mock_materials = {}
        result = self.compliance_checker.check(mock_page_content, mock_layout_spec, mock_materials)
        self.assertTrue(result)

    def test_content_generator_template_fallback_no_fake_data(self):
        """未注入宿主AI回调时：走模板兜底，含占位水印，且不含旧版编造假数据"""
        from core.content_generator import ContentGenerator, PLACEHOLDER_MARK
        gen = ContentGenerator(self.config)
        outline = gen.generate_outline({
            "核心主题": "智慧供应链平台", "总页数": 8, "目标受众": "技术负责人"
        })
        pages = gen.generate_page_content(outline, {
            "核心主题": "智慧供应链平台", "目标受众": "技术负责人", "内容禁忌": ""
        })
        # 至少一页是核心方案页，应带占位水印且标记 template_fallback
        solution = [c for c in pages.values() if c.get("generation_mode") == "template_fallback"]
        self.assertTrue(len(solution) > 0)
        joined = "".join(str(c.get("body", "")) for c in pages.values())
        self.assertIn(PLACEHOLDER_MARK, joined)
        # 关键：不再输出旧版硬编码假数据
        for fake in ("Kafka+Flink", "83% → 98.5%", "年节省约¥200万", "TensorRT"):
            self.assertNotIn(fake, joined, f"仍残留旧版假数据: {fake}")

    def test_content_generator_host_ai_callback(self):
        """注入宿主AI回调时：内容被真实回填，generation_mode=host_ai，无占位残留"""
        from core.content_generator import ContentGenerator, PLACEHOLDER_MARK
        gen = ContentGenerator(self.config)

        def fake_host_ai(page_type, theme, audience, title):
            # 模拟宿主AI：产出与主题强相关的真实内容
            return {"body": f"针对{theme}面向{audience}的真实内容-{page_type}"}

        gen.set_content_callback(fake_host_ai)
        outline = gen.generate_outline({
            "核心主题": "智慧供应链平台", "总页数": 8, "目标受众": "技术负责人"
        })
        pages = gen.generate_page_content(outline, {
            "核心主题": "智慧供应链平台", "目标受众": "技术负责人", "内容禁忌": ""
        })
        # 走 _fill 的页面应为 host_ai 且内容含主题、无占位水印
        host_pages = [c for c in pages.values() if c.get("generation_mode") == "host_ai"]
        self.assertTrue(len(host_pages) > 0)
        for c in host_pages:
            self.assertIn("智慧供应链平台", c["body"])
            self.assertNotIn(PLACEHOLDER_MARK, c["body"])

    def test_full_pipeline_simulation(self):
        """测试完整链路（模拟）"""
        test_requirement = {
            "核心主题": "AI技术测试汇报",
            "目标受众": "技术测试人员",
            "汇报时长": "5分钟",
            "总页数": 3,
            "交付格式": ".pptx",
            "品牌VI": "默认咨询科技风",
            "内容禁忌": "无"
        }
        # content_generator 已完善，链路应可端到端跑通；验证不抛异常并清理产物
        try:
            result = self.skill.execute_pipeline(test_requirement)
            self.assertIsNotNone(result)
        finally:
            # 清理本次链路生成的中间产物，保持 output/ 干净
            import glob
            for pattern in ("output/*.pptx", "output/images/*", "output/charts/*"):
                for f in glob.glob(pattern):
                    try:
                        os.remove(f)
                    except OSError:
                        pass

if __name__ == "__main__":
    unittest.main()
