"""
SVG图标库 — Python Pipeline 图标生成模块

基于 SKILL.md / HarnessConfig 规范：
- 48x48 viewBox, stroke-width: 2.0
- 亮底图标色: #FF6F00 (琥珀橙) 或 STYLE['orange']
- 暗底图标色: #FFFFFF (纯白)
- Material Design 线性图标风格
- 关键词->图标映射 (ICON_MAP)
- icon_pair 输出: SVG + PNG 双格式

用法:
    from tools.icon_library import IconLibrary

    lib = IconLibrary()                       # 默认亮底主题色
    lib = IconLibrary(theme="dark")            # 暗底(白色图标)

    # 关键词查找
    svg = lib.get_icon_svg("市场")             # 返回 trending 图标SVG

    # 导出PNG (需安装 cairosvg)
    png_path = lib.export_png("市场", "output/icons/trending.png")

    # 生成 icon_pair (SVG + PNG)
    paths = lib.generate_icon_pair("市场", "output/icons")

    # 批量生成
    results = lib.batch_generate(["市场", "风险", "智能体"], "output/icons")
"""

import os
import json
import struct
import zlib
from typing import Dict, List, Optional, Tuple


# ================ 关键词->图标映射 ================
ICON_MAP: Dict[str, str] = {
    "网关": "gateway",
    "智能体": "agent",
    "技能": "plugin",
    "记忆": "memory",
    "风险": "shield",
    "安全": "lock",
    "凭证": "key",
    "攻击": "bug",
    "文件": "folder",
    "浏览器": "globe",
    "系统": "terminal",
    "API": "api",
    "市场": "trending",
    "用户": "person",
    "数据": "database",
    "自动化": "gear",
    "观察": "eye",
    "思考": "brain",
    "行动": "hand",
    "检查": "checkmark",
    "本地": "home",
    "开源": "code",
    "跨平台": "layers",
    "效率": "rocket",
    "增长": "chart-up",
    "下降": "chart-down",
    "目标": "target",
    "战略": "compass",
    "创新": "lightbulb",
    "协作": "people",
    "流程": "flow",
    "时间": "clock",
    "预警": "alert",
    "成功": "trophy",
    "连接": "link",
    "云": "cloud",
    "分析": "magnifier",
    "设置": "settings",
    "通知": "bell",
    "搜索": "search",
    "编辑": "edit",
    "删除": "trash",
    "添加": "plus",
    "关闭": "close",
    "箭头": "arrow-right",
    "下载": "download",
    "上传": "upload",
    "分享": "share",
    "刷新": "refresh",
    "锁定": "lock-closed",
    "解锁": "lock-open",
    "货币": "currency",
    "报告": "document",
    "趋势": "trending",
    "网络": "network",
    "服务器": "server",
    "数据库": "database",
    "AI": "brain",
    "转型": "transform",
    "合规": "shield-check",
    "投资": "currency",
    "客户": "people",
}


# ================ SVG 图标路径数据 ================
# Material Design 线性风格，48x48 viewBox
# 坐标系: 0-48, 留6px边距 -> 有效绘图区域 6-42

ICON_PATHS: Dict[str, list] = {
    "gateway": [
        "M24 6 L24 16",
        "M18 12 L30 12",
        "M14 18 L34 18",
        "M14 18 L14 38",
        "M34 18 L34 38",
        "M14 38 L34 38",
        "M24 18 L24 38",
    ],
    "agent": [
        "M24 8 L24 14",
        "M24 14 A8 8 0 1 1 24 14.01",
        "M10 42 L10 28 A14 14 0 0 1 38 28 L38 42",
        "M6 24 L12 24",
        "M36 24 L42 24",
    ],
    "plugin": [
        "M8 14 L8 8 L14 8",
        "M34 8 L40 8 L40 14",
        "M40 34 L40 40 L34 40",
        "M14 40 L8 40 L8 34",
        "M18 18 L30 18 L30 30 L18 30 Z",
    ],
    "memory": [
        "M8 12 L40 12 L40 36 L8 36 Z",
        "M16 12 L16 36",
        "M24 12 L24 36",
        "M32 12 L32 36",
        "M8 20 L40 20",
        "M8 28 L40 28",
    ],
    "shield": [
        "M24 6 L8 14 L8 26 C8 36 24 42 24 42 C24 42 40 36 40 26 L40 14 Z",
    ],
    "lock": [
        "M14 22 L14 16 A10 10 0 0 1 34 16 L34 22",
        "M10 22 L38 22 L38 40 L10 40 Z",
        "M22 30 L26 30 L26 34 L22 34 Z",
    ],
    "key": [
        "M18 18 A8 8 0 1 1 10 18",
        "M18 18 L38 18",
        "M32 18 L32 24",
        "M38 18 L38 24",
    ],
    "bug": [
        "M16 16 L32 16 L32 36 L16 36 Z",
        "M24 10 L24 16",
        "M16 22 L10 18",
        "M32 22 L38 18",
        "M16 28 L10 28",
        "M32 28 L38 28",
        "M16 34 L10 38",
        "M32 34 L38 38",
    ],
    "folder": [
        "M6 14 L6 38 L42 38 L42 18 L24 18 L20 14 Z",
    ],
    "globe": [
        "M24 8 A16 16 0 1 1 24 8.01",
        "M8 24 L40 24",
        "M24 8 L24 40",
        "M12 14 C18 18 30 18 36 14",
        "M12 34 C18 30 30 30 36 34",
    ],
    "terminal": [
        "M6 10 L42 10 L42 38 L6 38 Z",
        "M14 20 L22 26 L14 32",
        "M24 32 L34 32",
    ],
    "api": [
        "M24 8 L8 40",
        "M24 8 L40 40",
        "M14 28 L34 28",
        "M6 40 L42 40",
    ],
    "trending": [
        "M8 36 L18 22 L26 28 L40 10",
        "M32 10 L40 10 L40 18",
    ],
    "person": [
        "M24 12 A6 6 0 1 1 24 12.01",
        "M12 42 L12 28 C12 22 18 18 24 18 C30 18 36 22 36 28 L36 42",
    ],
    "database": [
        "M8 12 L40 12 L40 36 L8 36 Z",
        "M8 20 L40 20",
        "M8 28 L40 28",
        "M8 12 A16 4 0 0 0 40 12",
    ],
    "gear": [
        "M24 16 A8 8 0 1 1 24 16.01",
        "M22 6 L26 6",
        "M22 42 L26 42",
        "M6 22 L6 26",
        "M42 22 L42 26",
        "M11 11 L14 14",
        "M34 14 L37 11",
        "M11 37 L14 34",
        "M34 34 L37 37",
    ],
    "eye": [
        "M6 24 C14 12 34 12 42 24",
        "M6 24 C14 36 34 36 42 24",
        "M24 18 A6 6 0 1 1 24 18.01",
    ],
    "brain": [
        "M24 8 C16 8 10 14 10 22 C10 30 16 38 24 38",
        "M24 8 C32 8 38 14 38 22 C38 30 32 38 24 38",
        "M24 8 L24 42",
        "M10 22 L18 22",
        "M30 22 L38 22",
        "M14 16 L20 16",
        "M28 16 L34 16",
    ],
    "hand": [
        "M16 22 L16 8",
        "M22 20 L22 6",
        "M28 20 L28 8",
        "M34 22 L34 12",
        "M10 22 L10 32 C10 38 16 42 16 42 L38 42 L16 42 C12 42 10 38 10 32",
    ],
    "checkmark": [
        "M10 24 L20 34 L38 14",
    ],
    "home": [
        "M8 24 L24 10 L40 24",
        "M14 24 L14 40 L34 40 L34 24",
        "M20 40 L20 32 L28 32 L28 40",
    ],
    "code": [
        "M16 14 L6 24 L16 34",
        "M32 14 L42 24 L32 34",
        "M22 10 L26 38",
    ],
    "layers": [
        "M6 18 L24 10 L42 18",
        "M6 26 L24 18 L42 26",
        "M6 34 L24 26 L42 34",
    ],
    "rocket": [
        "M24 6 C24 6 16 14 16 26 L16 34 L32 34 L32 26 C32 14 24 6 24 6",
        "M16 34 L12 40 L20 36",
        "M32 34 L36 40 L28 36",
        "M24 20 A3 3 0 1 1 24 20.01",
    ],
    "chart-up": [
        "M8 40 L8 8",
        "M8 40 L40 40",
        "M14 34 L20 28 L26 30 L36 14",
        "M36 14 L36 20",
        "M36 14 L30 14",
    ],
    "chart-down": [
        "M8 40 L8 8",
        "M8 40 L40 40",
        "M14 14 L20 20 L26 18 L36 34",
        "M36 34 L36 28",
        "M36 34 L30 34",
    ],
    "target": [
        "M24 8 A16 16 0 1 1 24 8.01",
        "M24 16 A8 8 0 1 1 24 16.01",
        "M24 24 A2 2 0 1 1 24 24.01",
    ],
    "compass": [
        "M24 8 A16 16 0 1 1 24 8.01",
        "M24 18 L20 30 L24 26 L28 30 Z",
    ],
    "lightbulb": [
        "M18 34 L30 34",
        "M19 38 L29 38",
        "M20 30 L20 34 L28 34 L28 30",
        "M16 18 A10 10 0 1 1 32 18 C32 24 28 28 28 30 L20 30 C20 28 16 24 16 18",
    ],
    "people": [
        "M16 12 A4 4 0 1 1 16 12.01",
        "M32 12 A4 4 0 1 1 32 12.01",
        "M8 36 L8 28 C8 24 12 20 16 20 C20 20 22 22 24 24",
        "M40 36 L40 28 C40 24 36 20 32 20 C28 20 26 22 24 24",
        "M24 24 L24 36",
    ],
    "flow": [
        "M8 16 L28 16 L28 12 L38 18 L28 24 L28 20 L8 20 Z",
        "M8 32 L28 32 L28 28 L38 34 L28 40 L28 36 L8 36 Z",
    ],
    "clock": [
        "M24 8 A16 16 0 1 1 24 8.01",
        "M24 24 L24 14",
        "M24 24 L32 24",
    ],
    "alert": [
        "M24 8 L6 40 L42 40 Z",
        "M24 20 L24 28",
        "M24 32 L24 34",
    ],
    "trophy": [
        "M14 10 L34 10 L32 26 C30 32 18 32 16 26 Z",
        "M14 14 L8 14 L8 22 C8 26 12 26 14 24",
        "M34 14 L40 14 L40 22 C40 26 36 26 34 24",
        "M20 32 L28 32 L28 36 L20 36 Z",
        "M16 36 L32 36 L32 40 L16 40 Z",
    ],
    "link": [
        "M18 24 L14 24 A8 8 0 0 1 14 16",
        "M14 16 L18 16",
        "M30 24 L34 24 A8 8 0 0 0 34 16",
        "M34 16 L30 16",
        "M14 24 A8 8 0 0 0 14 32 L18 32",
        "M34 24 A8 8 0 0 1 34 32 L30 32",
    ],
    "cloud": [
        "M12 32 A8 8 0 0 1 12 20 A10 10 0 0 1 30 16 A8 8 0 0 1 38 28 A6 6 0 0 1 36 38 L14 38 A8 8 0 0 1 12 32",
    ],
    "magnifier": [
        "M22 10 A10 10 0 1 1 22 10.01",
        "M30 30 L40 40",
    ],
    "settings": [
        "M24 16 A8 8 0 1 1 24 16.01",
        "M22 6 L26 6",
        "M22 42 L26 42",
        "M6 22 L6 26",
        "M42 22 L42 26",
        "M10.5 10.5 L13.5 13.5",
        "M34.5 13.5 L37.5 10.5",
        "M10.5 37.5 L13.5 34.5",
        "M34.5 34.5 L37.5 37.5",
    ],
    "bell": [
        "M14 28 C14 18 18 10 24 10 C30 10 34 18 34 28 L36 34 L12 34 Z",
        "M20 34 A4 4 0 0 0 28 34",
    ],
    "search": [
        "M20 10 A10 10 0 1 1 20 10.01",
        "M28 28 L40 40",
    ],
    "edit": [
        "M8 40 L8 32 L30 10 L38 18 L16 40 Z",
        "M30 10 L34 6 L42 14 L38 18",
    ],
    "trash": [
        "M10 14 L38 14",
        "M16 14 L18 8 L30 8 L32 14",
        "M14 14 L16 40 L32 40 L34 14",
        "M22 20 L22 34",
        "M26 20 L26 34",
    ],
    "plus": [
        "M24 8 L24 40",
        "M8 24 L40 24",
    ],
    "close": [
        "M12 12 L36 36",
        "M36 12 L12 36",
    ],
    "arrow-right": [
        "M8 24 L36 24",
        "M28 16 L36 24 L28 32",
    ],
    "download": [
        "M24 8 L24 32",
        "M16 24 L24 32 L32 24",
        "M8 38 L40 38",
    ],
    "upload": [
        "M24 32 L24 8",
        "M16 16 L24 8 L32 16",
        "M8 38 L40 38",
    ],
    "share": [
        "M36 12 A4 4 0 1 1 36 12.01",
        "M12 22 A4 4 0 1 1 12 22.01",
        "M12 34 A4 4 0 1 1 12 34.01",
        "M33 14 L15 21",
        "M33 34 L15 27",
    ],
    "refresh": [
        "M36 16 A14 14 0 0 0 12 24",
        "M12 32 A14 14 0 0 0 36 24",
        "M36 10 L36 18 L28 16",
        "M12 38 L12 30 L20 32",
    ],
    "lock-closed": [
        "M14 22 L14 16 A10 10 0 0 1 34 16 L34 22",
        "M10 22 L38 22 L38 40 L10 40 Z",
        "M22 30 L26 30 L26 34 L22 34 Z",
    ],
    "lock-open": [
        "M34 22 L34 16 A10 10 0 0 0 14 16",
        "M10 22 L38 22 L38 40 L10 40 Z",
        "M22 30 L26 30 L26 34 L22 34 Z",
    ],
    "currency": [
        "M24 8 L24 40",
        "M16 14 L32 14",
        "M14 22 L34 22",
        "M16 30 L32 30",
    ],
    "document": [
        "M10 6 L30 6 L38 14 L38 42 L10 42 Z",
        "M30 6 L30 14 L38 14",
        "M16 22 L32 22",
        "M16 28 L32 28",
        "M16 34 L26 34",
    ],
    "network": [
        "M24 10 A4 4 0 1 1 24 10.01",
        "M10 22 A4 4 0 1 1 10 22.01",
        "M38 22 A4 4 0 1 1 38 22.01",
        "M10 38 A4 4 0 1 1 10 38.01",
        "M38 38 A4 4 0 1 1 38 38.01",
        "M22 12 L12 20",
        "M26 12 L36 20",
        "M10 26 L10 34",
        "M38 26 L38 34",
        "M14 24 L24 24",
        "M24 24 L34 24",
    ],
    "server": [
        "M8 8 L40 8 L40 18 L8 18 Z",
        "M8 20 L40 20 L40 30 L8 30 Z",
        "M8 32 L40 32 L40 42 L8 42 Z",
        "M14 13 L16 13",
        "M14 25 L16 25",
        "M14 37 L16 37",
    ],
    "transform": [
        "M10 14 L38 14 L38 28 L10 28 Z",
        "M14 32 L34 32 L34 42 L14 42 Z",
        "M24 28 L24 32",
    ],
    "shield-check": [
        "M24 6 L8 14 L8 26 C8 36 24 42 24 42 C24 42 40 36 40 26 L40 14 Z",
        "M16 24 L22 30 L34 18",
    ],
}


# ================ SVG 生成工具 ================

def _svg_wrap_multi(paths: list, stroke_color: str = "#FF6F00",
                    stroke_width: float = 2.0, fill: str = "none",
                    stroke_linecap: str = "round",
                    stroke_linejoin: str = "round") -> str:
    """多路径SVG包装器"""
    paths_xml = "".join(f'<path d="{p}"/>' for p in paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" '
        f'width="48" height="48" fill="{fill}" '
        f'stroke="{stroke_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="{stroke_linecap}" stroke-linejoin="{stroke_linejoin}">'
        f'{paths_xml}'
        f'</svg>'
    )


class IconLibrary:
    """
    SVG图标库 — Material Design 线性风格

    规范:
    - 48x48 viewBox, stroke-width: 2.0
    - 亮底图标色: #FF6F00 (琥珀橙)
    - 暗底图标色: #FFFFFF (纯白)
    - icon_pair 输出: SVG + PNG 双格式
    """

    THEMES = {
        "light": "#FF6F00",
        "dark": "#FFFFFF",
    }

    def __init__(self, theme: str = "light", custom_color: Optional[str] = None,
                 stroke_width: float = 2.0):
        self.theme = theme
        self.stroke_color = custom_color or self.THEMES.get(theme, self.THEMES["light"])
        self.stroke_width = stroke_width
        self._cairosvg_available = self._check_cairosvg()

    @staticmethod
    def _check_cairosvg() -> bool:
        try:
            import cairosvg  # noqa: F401
            # 尝试实际调用以检测底层 libcairo 是否可用
            cairosvg.SVGParser()
            return True
        except Exception:
            return False

    # ================ 图标查询 ================

    def get_icon_name(self, keyword: str) -> Optional[str]:
        """根据关键词查找图标名称"""
        return ICON_MAP.get(keyword)

    def get_icon_svg(self, keyword: str, color: Optional[str] = None,
                     size: int = 48) -> Optional[str]:
        """根据关键词获取图标SVG字符串"""
        icon_name = self.get_icon_name(keyword)
        if not icon_name:
            return None
        return self.render_icon_svg(icon_name, color, size)

    def render_icon_svg(self, icon_name: str, color: Optional[str] = None,
                        size: int = 48) -> Optional[str]:
        """根据图标名称渲染SVG字符串"""
        paths = ICON_PATHS.get(icon_name)
        if not paths:
            return None
        stroke_color = color or self.stroke_color
        svg = _svg_wrap_multi(paths, stroke_color=stroke_color,
                              stroke_width=self.stroke_width)
        if size != 48:
            svg = svg.replace('width="48" height="48"',
                              f'width="{size}" height="{size}"')
        return svg

    def list_icons(self) -> Dict[str, str]:
        """列出所有关键词->图标映射"""
        return dict(ICON_MAP)

    def list_icon_names(self) -> List[str]:
        """列出所有可用图标名称(去重)"""
        return sorted(set(ICON_MAP.values()))

    def search_icons(self, query: str) -> List[Tuple[str, str]]:
        """模糊搜索图标"""
        results = []
        for kw, icon_name in ICON_MAP.items():
            if query.lower() in kw.lower() or query.lower() in icon_name.lower():
                results.append((kw, icon_name))
        return results

    # ================ 文件导出 ================

    def export_svg(self, keyword: str, output_path: str,
                   color: Optional[str] = None, size: int = 48) -> Optional[str]:
        """导出图标为SVG文件"""
        svg = self.get_icon_svg(keyword, color, size)
        if not svg:
            return None
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)
        return output_path

    def export_png(self, keyword: str, output_path: str,
                   color: Optional[str] = None, size: int = 48,
                   dpi: int = 300) -> Optional[str]:
        """导出图标为PNG文件(需要cairosvg)"""
        if not self._cairosvg_available:
            print("  [icon_library] cairosvg 未安装，尝试Pillow回退。安装PNG支持: pip install cairosvg")
            return self._fallback_png(keyword, output_path, size)

        svg = self.get_icon_svg(keyword, color, size)
        if not svg:
            return None

        try:
            import cairosvg
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                             write_to=output_path,
                             output_width=size,
                             output_height=size,
                             dpi=dpi)
            return output_path
        except Exception as e:
            print(f"  [icon_library] PNG导出失败({keyword}): {e}")
            return self._fallback_png(keyword, output_path, size)

    def _fallback_png(self, keyword: str, output_path: str,
                      size: int = 48) -> Optional[str]:
        """PNG导出回退：尝试Pillow或生成占位图"""
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            margin = size // 6
            rgb = self._hex_to_rgb(self.stroke_color)
            draw.ellipse([margin, margin, size - margin, size - margin],
                         outline=rgb, width=2)
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            img.save(output_path)
            return output_path
        except ImportError:
            pass

        # 最终回退：最小有效PNG
        self._create_minimal_png(output_path)
        return output_path

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _create_minimal_png(path: str):
        """创建1x1像素占位PNG"""
        signature = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        raw_data = b'\x00\x00\x00\x00\x00'
        compressed = zlib.compress(raw_data)
        idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, 'wb') as f:
            f.write(signature + ihdr + idat + iend)

    # ================ icon_pair 生成 ================

    def generate_icon_pair(self, keyword: str, output_dir: str,
                           color: Optional[str] = None,
                           size: int = 48) -> Optional[Dict[str, str]]:
        """
        生成 icon_pair: SVG + PNG 双格式文件

        Returns: {"svg": path, "png": path, "name": icon_name, "keyword": keyword} or None
        """
        icon_name = self.get_icon_name(keyword)
        if not icon_name:
            return None

        os.makedirs(output_dir, exist_ok=True)
        svg_path = os.path.join(output_dir, f"{icon_name}.svg")
        png_path = os.path.join(output_dir, f"{icon_name}.png")

        svg_result = self.export_svg(keyword, svg_path, color, size=48)
        if not svg_result:
            return None

        png_result = self.export_png(keyword, png_path, color, size)

        return {
            "svg": svg_result,
            "png": png_result,
            "name": icon_name,
            "keyword": keyword,
        }

    def batch_generate(self, keywords: List[str], output_dir: str,
                       color: Optional[str] = None,
                       size: int = 48) -> Dict[str, Dict[str, str]]:
        """批量生成图标"""
        results = {}
        for keyword in keywords:
            result = self.generate_icon_pair(keyword, output_dir, color, size)
            if result:
                results[keyword] = result
                print(f"  [icon] {keyword} -> {result['name']}")
            else:
                print(f"  [icon] 未找到映射: {keyword}")
        return results

    # ================ 与 image_generator 集成 ================

    def generate_manifest_icons(self, manifest_path: str,
                                output_dir: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """从 manifest.json 中读取 icon_pair 条目，批量生成图标"""
        if not os.path.exists(manifest_path):
            print(f"  [icon] Manifest不存在: {manifest_path}")
            return {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data.get("items", data) if isinstance(data, dict) else data
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(manifest_path), "icons")

        results = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            if role != "icon_pair":
                continue

            page_id = item.get("page_id", "")
            keyword = item.get("keyword", item.get("prompt", ""))

            result = self.generate_icon_pair(keyword, output_dir)
            if result:
                results[page_id] = result
                item["status"] = "completed"
                item["svg_path"] = result["svg"]
                item["png_path"] = result["png"]

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return results

    # ================ 与 pptx_generator 集成 ================

    def get_icon_for_slide(self, keyword: str, bg_is_dark: bool = False) -> Optional[str]:
        """为幻灯片获取合适颜色的图标SVG"""
        if bg_is_dark:
            return self.get_icon_svg(keyword, color="#FFFFFF")
        return self.get_icon_svg(keyword)

    def export_icon_for_pptx(self, keyword: str, output_dir: str,
                             bg_is_dark: bool = False,
                             size: int = 128) -> Optional[str]:
        """为 python-pptx 导出图标PNG(尺寸适配PPT嵌入)"""
        color = "#FFFFFF" if bg_is_dark else None
        icon_name = self.get_icon_name(keyword)
        if not icon_name:
            return None
        output_path = os.path.join(output_dir, f"{icon_name}_pptx.png")
        return self.export_png(keyword, output_path, color, size)


# ================ 便捷函数 ================

def get_icon_svg(keyword: str, theme: str = "light") -> Optional[str]:
    """便捷函数：根据关键词获取图标SVG"""
    lib = IconLibrary(theme=theme)
    return lib.get_icon_svg(keyword)


def generate_icon_pair(keyword: str, output_dir: str,
                       theme: str = "light") -> Optional[Dict[str, str]]:
    """便捷函数：生成icon_pair"""
    lib = IconLibrary(theme=theme)
    return lib.generate_icon_pair(keyword, output_dir)


# ================ CLI入口 ================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OpenClaw PPT 图标库工具")
    parser.add_argument("action", choices=["list", "search", "generate", "batch"],
                        help="操作: list/search/generate/batch")
    parser.add_argument("--keyword", "-k", help="关键词")
    parser.add_argument("--keywords", "-K", help="批量关键词，逗号分隔")
    parser.add_argument("--output", "-o", default="output/icons", help="输出目录")
    parser.add_argument("--theme", "-t", choices=["light", "dark"], default="light")
    parser.add_argument("--color", "-c", help="自定义颜色(覆盖主题)")
    parser.add_argument("--size", "-s", type=int, default=48, help="PNG尺寸(px)")

    args = parser.parse_args()
    lib = IconLibrary(theme=args.theme, custom_color=args.color)

    if args.action == "list":
        print(f"可用图标 ({len(ICON_MAP)} 个关键词 -> {len(set(ICON_MAP.values()))} 个图标):")
        for kw, name in sorted(ICON_MAP.items(), key=lambda x: x[1]):
            print(f"  {kw:8s} -> {name}")

    elif args.action == "search":
        if not args.keyword:
            print("请指定 --keyword")
        else:
            results = lib.search_icons(args.keyword)
            if results:
                for kw, name in results:
                    print(f"  {kw} -> {name}")
            else:
                print(f"未找到匹配 '{args.keyword}' 的图标")

    elif args.action == "generate":
        if not args.keyword:
            print("请指定 --keyword")
        else:
            result = lib.generate_icon_pair(args.keyword, args.output, size=args.size)
            if result:
                print(f"生成成功: SVG={result['svg']}, PNG={result['png']}")
            else:
                print(f"未找到映射: {args.keyword}")

    elif args.action == "batch":
        if not args.keywords:
            print("请指定 --keywords (逗号分隔)")
        else:
            kws = [k.strip() for k in args.keywords.split(",")]
            results = lib.batch_generate(kws, args.output, size=args.size)
            print(f"\n生成完成: {len(results)}/{len(kws)} 个图标")
