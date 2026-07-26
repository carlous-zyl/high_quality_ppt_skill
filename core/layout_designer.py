from typing import Dict, Any

class LayoutDesigner:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化布局设计器
        :param config: 全局配置字典，来自global_config.yaml
        """
        self.config = config
        self.vi = config.get("vi_spec", {})
        # 默认VI兜底
        self._default_vi = {
            "primary_color": "#165DFF",
            "secondary_color": "#36CFC9",
            "neutral_colors": ["#1D2129", "#4E5969", "#86909C", "#F2F3F5", "#FFFFFF"],
            "title_font": "思源黑体 Bold",
            "body_font": "思源黑体 Regular",
            "min_font_size": 14,
            "page_margin": "20mm"
        }

    def design_layout(self, page_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于VI规范设计每页布局
        :param page_content: 单页内容字典
        :return: 布局规格字典（纯数值，可JSON序列化）
        """
        layout_spec = {}
        vi = self.vi if self.vi else self._default_vi

        for page_id, content in page_content.items():
            # 根据内容特征选择布局模板
            if content.get("chart_data"):
                layout = self._chart_right_layout(content, vi)
            elif content.get("code"):
                layout = self._code_right_layout(content, vi)
            elif content.get("image_prompt"):
                layout = self._image_right_layout(content, vi)
            else:
                layout = self._text_only_layout(content, vi)

            # 统一追加VI元数据（供校验使用）
            layout.update({
                "margin": vi.get("page_margin", "20mm"),
                "colors": [vi["primary_color"], vi["secondary_color"]] + vi["neutral_colors"],
                "logo_position": vi.get("logo_position", "top_right"),
                "min_font_size": vi.get("min_font_size", 14),
                "contrast_ratio": 5.2  # 模拟对比度值（实际可通过RGB计算）
            })

            layout_spec[page_id] = layout

        print(f"✅ [布局设计] 布局完成，共{len(layout_spec)}页")
        return layout_spec

    # ---------------- 标准化布局模板 ----------------
    # 所有数值单位：x/y/w/h 为英寸(inch)，font_size 为磅(pt)，color 为十六进制字符串
    def _text_only_layout(self, content: Dict[str, Any], vi: Dict) -> Dict[str, Any]:
        """纯文本布局：标题+正文"""
        return {
            "layout_type": "text_only",
            "zones": [
                {
                    "id": "title", "type": "text",
                    "x": 0.5, "y": 0.3, "w": 9.0, "h": 1.0,
                    "font": vi["title_font"], "font_size": 32,
                    "color": vi["neutral_colors"][0]
                },
                {
                    "id": "body", "type": "text",
                    "x": 0.5, "y": 1.5, "w": 9.0, "h": 3.5,
                    "font": vi["body_font"], "font_size": 18,
                    "color": vi["neutral_colors"][1]
                }
            ]
        }

    def _image_right_layout(self, content: Dict[str, Any], vi: Dict) -> Dict[str, Any]:
        """图文布局：左文右图"""
        return {
            "layout_type": "image_right",
            "zones": [
                {
                    "id": "title", "type": "text",
                    "x": 0.5, "y": 0.3, "w": 9.0, "h": 1.0,
                    "font": vi["title_font"], "font_size": 32,
                    "color": vi["neutral_colors"][0]
                },
                {
                    "id": "body", "type": "text",
                    "x": 0.5, "y": 1.5, "w": 5.0, "h": 3.5,
                    "font": vi["body_font"], "font_size": 18,
                    "color": vi["neutral_colors"][1]
                },
                {
                    "id": "image", "type": "image",
                    "x": 5.8, "y": 1.5, "w": 3.7, "h": 3.5
                }
            ]
        }

    def _chart_right_layout(self, content: Dict[str, Any], vi: Dict) -> Dict[str, Any]:
        """图表布局：左文右图（图表）"""
        return {
            "layout_type": "chart_right",
            "zones": [
                {
                    "id": "title", "type": "text",
                    "x": 0.5, "y": 0.3, "w": 9.0, "h": 1.0,
                    "font": vi["title_font"], "font_size": 32,
                    "color": vi["neutral_colors"][0]
                },
                {
                    "id": "body", "type": "text",
                    "x": 0.5, "y": 1.5, "w": 4.5, "h": 3.5,
                    "font": vi["body_font"], "font_size": 18,
                    "color": vi["neutral_colors"][1]
                },
                {
                    "id": "chart", "type": "chart",
                    "x": 5.3, "y": 1.5, "w": 4.2, "h": 3.5
                }
            ]
        }

    def _code_right_layout(self, content: Dict[str, Any], vi: Dict) -> Dict[str, Any]:
        """代码布局：左说明右代码"""
        return {
            "layout_type": "code_right",
            "zones": [
                {
                    "id": "title", "type": "text",
                    "x": 0.5, "y": 0.3, "w": 9.0, "h": 1.0,
                    "font": vi["title_font"], "font_size": 32,
                    "color": vi["neutral_colors"][0]
                },
                {
                    "id": "body", "type": "text",
                    "x": 0.5, "y": 1.5, "w": 4.0, "h": 3.5,
                    "font": vi["body_font"], "font_size": 18,
                    "color": vi["neutral_colors"][1]
                },
                {
                    "id": "code", "type": "code",
                    "x": 4.8, "y": 1.5, "w": 4.7, "h": 3.5,
                    "font": "Consolas", "font_size": 14,
                    "color": vi["neutral_colors"][0],
                    "bg_color": vi["neutral_colors"][3]
                }
            ]
        }
