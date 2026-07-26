from typing import Dict, Any

class ConsistencyChecker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vi = config["vi_spec"]

    def check(self, page_content: Dict[str, Any], layout_spec: Dict[str, Any]) -> bool:
        """全稿一致性校验（实际返回校验结果，不再恒返回True）"""
        checks = [
            self._check_font_consistency(page_content),
            self._check_color_consistency(layout_spec),
            self._check_layout_consistency(layout_spec)
        ]
        return all(checks)

    def _check_font_consistency(self, page_content: Dict[str, Any]) -> bool:
        """检查字体一致性"""
        required_fonts = {self.vi["title_font"], self.vi["body_font"]}
        all_ok = True
        for page_id, content in page_content.items():
            if "font" in content:
                page_fonts = set(content["font"].values())
                if not page_fonts.issubset(required_fonts):
                    print(f"[错误] 页面 {page_id} 存在非规范字体：{page_fonts - required_fonts}")
                    all_ok = False
        return all_ok

    def _check_color_consistency(self, layout_spec: Dict[str, Any]) -> bool:
        """检查配色一致性"""
        required_colors = {self.vi["primary_color"], self.vi["secondary_color"]} | set(self.vi["neutral_colors"])
        all_ok = True
        for page_id, spec in layout_spec.items():
            if "colors" in spec:
                page_colors = set(spec["colors"])
                if not page_colors.issubset(required_colors):
                    print(f"[错误] 页面 {page_id} 存在非规范配色：{page_colors - required_colors}")
                    all_ok = False
        return all_ok

    def _check_layout_consistency(self, layout_spec: Dict[str, Any]) -> bool:
        """检查版式一致性"""
        if len(layout_spec) < 2:
            return True
        all_ok = True
        # 检查页边距是否一致
        first_margin = layout_spec.get(list(layout_spec.keys())[0], {}).get("margin", self.vi["page_margin"])
        for page_id, spec in layout_spec.items():
            if spec.get("margin", self.vi["page_margin"]) != first_margin:
                print(f"[错误] 页面 {page_id} 页边距与首页不一致")
                all_ok = False
        return all_ok
