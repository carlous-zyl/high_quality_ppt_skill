import re
from typing import Dict, Any

class ComplianceChecker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vi = config["vi_spec"]

    def check(self, page_content: Dict[str, Any], layout_spec: Dict[str, Any], materials: Dict[str, Any]) -> bool:
        """合规性校验"""
        checks = [
            self._check_contrast_ratio(layout_spec),
            self._check_information_density_return(page_content),
            self._check_brand_compliance(layout_spec)
        ]
        return all(checks)

    def check_information_density(self, page_content: Dict[str, Any]) -> bool:
        """
        信息密度即时校验（供pipeline步骤3调用）
        HarnessConfig: 单页正文≤300字
        修正：统计有效字数（去除换行和多余空白），而非原始字符长度
        """
        max_words = 300
        all_ok = True
        for page_id, content in page_content.items():
            if "body" in content and content["body"]:
                # 统计有效字数：去除换行和连续空白
                effective_text = re.sub(r'\s+', '', content["body"])
                word_count = len(effective_text)
                if word_count > max_words:
                    print(f"[警告] 页面 {page_id} 文字过多：{word_count}字，建议≤{max_words}字")
                    all_ok = False
        return all_ok

    def _check_information_density_return(self, page_content: Dict[str, Any]) -> bool:
        """合规校验内部调用（返回bool，不再恒返回True）"""
        return self.check_information_density(page_content)

    def _check_contrast_ratio(self, layout_spec: Dict[str, Any]) -> bool:
        """检查文字与背景对比度（简化版，实际需计算相对亮度）"""
        min_ratio = self.vi["min_contrast_ratio"]
        all_ok = True
        for page_id, spec in layout_spec.items():
            if "contrast_ratio" in spec:
                if spec["contrast_ratio"] < min_ratio:
                    print(f"[错误] 页面 {page_id} 对比度不足：{spec['contrast_ratio']}:1，要求≥{min_ratio}:1")
                    all_ok = False
        return all_ok

    def _check_brand_compliance(self, layout_spec: Dict[str, Any]) -> bool:
        """检查品牌合规性"""
        # 检查Logo位置
        required_logo_pos = self.vi["logo_position"]
        all_ok = True
        for page_id, spec in layout_spec.items():
            if "logo_position" in spec:
                if spec["logo_position"] != required_logo_pos:
                    print(f"[错误] 页面 {page_id} Logo位置错误：{spec['logo_position']}，要求：{required_logo_pos}")
                    all_ok = False
            # 检查最小字号
            if "min_font_size" in spec:
                if spec["min_font_size"] < self.vi["min_font_size"]:
                    print(f"[错误] 页面 {page_id} 字号过小：{spec['min_font_size']}pt，要求≥{self.vi['min_font_size']}pt")
                    all_ok = False
        return all_ok
