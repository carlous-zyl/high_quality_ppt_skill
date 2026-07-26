import requests
import os
import json
import base64
from typing import Dict, Any, Optional

class ImageGenerator:
    """
    PPT配图生成器 - 支持三种模式：
    1. placeholder: 仅生成占位图（模拟模式，保证PPTX不报错）
    2. api: 调用外部文生图API（如OpenAI DALL-E、通义万相等）
    3. workbuddy: 调用WorkBuddy内置ImageGen工具（推荐，通过manifest桥接）

    使用方式：
    - pipeline自动调用：根据config中toolchain.image_mode选择模式
    - WorkBuddy模式：AI助手读取generate_manifest.json后逐个调用ImageGen工具
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        toolchain = config.get("toolchain", {})
        self.api_url = toolchain.get("text_to_image_api", "")
        self.image_mode = toolchain.get("image_mode", "placeholder")  # placeholder / api / workbuddy
        self.vi = config.get("vi_spec", {})
        self.output_dir = "output/images"
        os.makedirs(self.output_dir, exist_ok=True)

    # ================ 构图动态映射 ================
    # 不同页面类型使用不同构图策略（2.10 HarnessConfig）
    COMPOSITION_MAP = {
        # 按layout_type映射（5种核心布局）
        "cover": "全景居中构图，上方留白给标题，底部空间给副标题区域",
        "toc": "四宫格排列构图，每格对应一项议程",
        "agenda": "四宫格排列构图，每格对应一项议程",  # toc的别名
        "bullets": "左侧主体文字区域，右侧配图或数据可视化",
        "steps": "时间轴或流程图式构图，从上到下或从左到右",
        "closing": "居中感谢语，背景简洁大气",
        # 按page_id映射（细粒度，用于content_generator生成的特定页面）
        "background": "左侧数据可视化，右侧文字阐述",
        "solution_core": "中心辐射式拓扑构图，核心居中",
        "solution_ext": "上下分层构图，上层总览下层细节",
        "tech_detail": "左侧文字右侧架构图的对比构图",
        "result": "左右对比式构图，优化前后并列展示",
        "risk_plan": "时间轴构图，从左到右展示规划路径",
        "summary": "居中感谢语，背景简洁大气",
    }

    # ================ 配图风格模板 ================
    # 为不同主题类别提供prompt增强模板
    STYLE_TEMPLATES = {
        "business": "商务科技风格，扁平化设计，专业简洁",
        "finance": "金融数据风格，深色背景配亮色数据，专业质感",
        "tech": "科技互联网风格，蓝色科技光效，现代感",
        "education": "教育培训风格，温暖色调，亲和力强",
        "strategy": "战略规划风格，高级商务感，深色系配金色点缀",
    }

    def generate_images(self, page_content: Dict[str, Any]) -> Dict[str, str]:
        """
        为每页生成配套图片
        返回 {page_id: image_path} 映射
        """
        images = {}
        for page_id, content in page_content.items():
            image_prompt = content.get("image_prompt")
            if not image_prompt:
                continue

            # 获取构图策略
            layout_type = content.get("layout_type", "bullets")
            composition = self.COMPOSITION_MAP.get(page_id,
                          self.COMPOSITION_MAP.get(layout_type, "简洁居中"))

            # 构建完整prompt
            prompt = self._build_prompt(image_prompt, composition)

            # 根据模式生成图片
            if self.image_mode == "api":
                image_path = self._call_api(prompt, page_id)
            elif self.image_mode == "workbuddy":
                # workbuddy模式：写入manifest供AI助手调用ImageGen
                image_path = self._write_to_manifest(prompt, page_id)
            else:
                # placeholder模式：生成占位图
                image_path = self._create_placeholder(page_id, prompt)

            if image_path:
                images[page_id] = image_path

        # 如果是workbuddy模式，最终合并manifest
        if self.image_mode == "workbuddy":
            self._finalize_manifest()

        return images

    def generate_all_prompts(self, page_content: Dict[str, Any]) -> Dict[str, str]:
        """
        为所有页面生成配图prompt（供AI助手调用ImageGen时使用）
        即使没有image_prompt字段，也基于title+body智能生成
        返回 {page_id: full_prompt} 映射
        """
        prompts = {}
        for page_id, content in page_content.items():
            # 优先使用显式image_prompt
            image_prompt = content.get("image_prompt")
            if not image_prompt:
                # 自动根据页面内容生成prompt
                image_prompt = self._auto_generate_prompt(content)

            if not image_prompt:
                continue

            layout_type = content.get("layout_type", "bullets")
            composition = self.COMPOSITION_MAP.get(page_id,
                          self.COMPOSITION_MAP.get(layout_type, "简洁居中"))
            full_prompt = self._build_prompt(image_prompt, composition)
            prompts[page_id] = full_prompt

        return prompts

    def _auto_generate_prompt(self, content: Dict[str, Any]) -> Optional[str]:
        """
        当页面没有显式image_prompt时，根据标题和内容智能生成配图提示词
        """
        title = content.get("title", "")
        layout_type = content.get("layout_type", "bullets")

        # 封面和结尾页不自动生成配图（有专用视觉设计）
        if layout_type in ("cover", "closing"):
            return None

        # 基于标题关键词匹配场景
        keyword_scenes = {
            "市场": "市场规模增长趋势图，向上箭头和数据柱状图",
            "竞争": "商业竞争格局示意图，多个企业棋子在对弈棋盘上",
            "技术": "AI技术架构图，神经网络节点连接，蓝绿色光效",
            "风险": "风险管控示意图，警示标志与防护盾牌",
            "路线": "战略路线图，从A点到B点的路径，里程碑标记",
            "转型": "企业数字化转型场景，齿轮和电路板融合",
            "AI": "AI人工智能概念图，大脑与电路融合，蓝绿光效",
            "Agent": "AI Agent协同工作场景，多个智能体节点网络",
            "SWOT": "SWOT分析四象限示意图",
            "合规": "合规审查场景，天平与法律文书",
            "投资": "投资组合分析场景，K线图与数据面板",
            "数据": "大数据分析场景，数据流与可视化面板",
            "客户": "客户服务体系场景，360度客户视图",
        }

        # 关键词匹配
        for keyword, scene in keyword_scenes.items():
            if keyword in title:
                return scene

        # 默认：根据标题生成商务配图
        if title:
            return f"商务场景配图，与「{title}」主题相关，抽象概念可视化"

        return None

    def _build_prompt(self, core_prompt: str, composition: str = "简洁居中") -> str:
        """
        构建符合VI规范的完整Prompt
        HarnessConfig mandatory_prompt_template:
        [核心主题]，[风格]，配色：主色{primary_color}，辅助色{secondary_color}，
        [构图]，无水印，无文字，300DPI，可商用
        """
        primary = self.vi.get("primary_color", "#047857")
        secondary = self.vi.get("secondary_color", "#10B981")
        style = self.STYLE_TEMPLATES.get(
            self.config.get("toolchain", {}).get("default_style", "business"),
            self.STYLE_TEMPLATES["business"]
        )

        return (
            f"{core_prompt}，"
            f"{style}，"
            f"配色：主色{primary}，辅助色{secondary}，"
            f"构图：{composition}，"
            f"无水印，无文字，高分辨率，可商用"
        )

    # ================ API模式 ================
    def _call_api(self, prompt: str, page_id: str) -> Optional[str]:
        """
        调用外部文生图API（OpenAI DALL-E / 通义万相 / Stable Diffusion等）
        配置在 toolchain.text_to_image_api
        """
        try:
            image_path = os.path.join(self.output_dir, f"{page_id}_image.png")

            # 如果已有真实图片（非占位图），跳过
            if os.path.exists(image_path) and os.path.getsize(image_path) > 1024:
                print(f"  ⏭️ 图片已存在，跳过：{image_path}")
                return image_path

            # 调用API
            response = requests.post(
                self.api_url,
                json={
                    "prompt": prompt,
                    "size": "1024x1024",
                    "n": 1,
                },
                timeout=60
            )
            response.raise_for_status()

            # 解析响应（兼容多种API格式）
            data = response.json()

            # OpenAI DALL-E格式
            if "data" in data and len(data["data"]) > 0:
                image_url = data["data"][0].get("url")
                image_b64 = data["data"][0].get("b64_json")

                if image_b64:
                    with open(image_path, "wb") as f:
                        f.write(base64.b64decode(image_b64))
                elif image_url:
                    img_response = requests.get(image_url, timeout=30)
                    with open(image_path, "wb") as f:
                        f.write(img_response.content)
            # 通义万相格式
            elif "output" in data:
                results = data["output"].get("results", [])
                if results:
                    img_url = results[0].get("url", "")
                    if img_url:
                        img_response = requests.get(img_url, timeout=30)
                        with open(image_path, "wb") as f:
                            f.write(img_response.content)
            else:
                print(f"  ⚠️ 未识别的API响应格式：{list(data.keys())}")
                return None

            # 验证图片
            if os.path.exists(image_path) and os.path.getsize(image_path) > 1024:
                print(f"  🖼️ 图片生成成功：{image_path} ({os.path.getsize(image_path)//1024}KB)")
                return image_path
            else:
                print(f"  ⚠️ 图片文件异常：{image_path}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"  ❌ API调用失败：{e}")
            return self._create_placeholder(page_id, prompt)
        except Exception as e:
            print(f"  ❌ 图片生成异常：{e}")
            return self._create_placeholder(page_id, prompt)

    # ================ WorkBuddy模式 ================
    def _write_to_manifest(self, prompt: str, page_id: str) -> str:
        """
        WorkBuddy模式：将图片生成请求写入manifest文件
        AI助手在生成PPT后读取manifest，逐个调用ImageGen工具生成图片
        """
        manifest_path = os.path.join(self.output_dir, "generate_manifest.json")

        # 读取已有manifest（兼容纯列表和带meta的格式）
        manifest = []
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                manifest = data
            elif isinstance(data, dict):
                manifest = data.get("items", [])

        # 添加新条目
        image_path = os.path.join(self.output_dir, f"{page_id}_image.png")
        entry = {
            "page_id": page_id,
            "prompt": prompt,
            "output_path": os.path.abspath(image_path),
            "size": "1024x1024",
            "status": "pending"
        }

        # 更新已存在的条目
        existing_ids = {e["page_id"] for e in manifest}
        if page_id in existing_ids:
            manifest = [entry if e["page_id"] == page_id else e for e in manifest]
        else:
            manifest.append(entry)

        # 写回manifest（写入时使用带meta的格式）
        output = {
            "meta": {
                "total": len(manifest),
                "pending": len([e for e in manifest if e["status"] == "pending"]),
                "description": "PPT配图生成清单，AI助手请逐个调用ImageGen工具完成生成",
            },
            "items": manifest
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"  📋 已写入manifest：{page_id}")
        return image_path

    def _finalize_manifest(self):
        """完成manifest写入，添加元信息"""
        manifest_path = os.path.join(self.output_dir, "generate_manifest.json")
        if not os.path.exists(manifest_path):
            return

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 兼容两种格式
        if isinstance(data, dict):
            manifest = data.get("items", [])
        else:
            manifest = data

        # 写入完整manifest（元信息+条目列表合并为单个JSON对象）
        output = {
            "meta": {
                "total": len(manifest),
                "pending": len([e for e in manifest if isinstance(e, dict) and e.get("status") == "pending"]),
                "description": "PPT配图生成清单，AI助手请逐个调用ImageGen工具完成生成",
                "how_to_use": (
                    "1. 读取此文件获取待生成图片列表 "
                    "2. 对每个pending条目，使用ImageGen工具生成图片 "
                    "3. 将生成结果保存到output_path指定路径 "
                    "4. 更新status为completed "
                    "5. 重新运行PPT生成以嵌入图片"
                )
            },
            "items": manifest
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"  📋 Manifest已就绪：{manifest_path}（{len(manifest)}张待生成）")

    # ================ Placeholder模式 ================
    def _create_placeholder(self, page_id: str, prompt: str = "") -> str:
        """创建占位图（模拟模式，确保PPTX可正常嵌入）"""
        image_path = os.path.join(self.output_dir, f"{page_id}_image.png")
        self._create_placeholder_png(image_path)
        print(f"  [占位] 生成占位图：{image_path}" + (f"，Prompt：{prompt[:50]}..." if prompt else ""))
        return image_path

    def _create_placeholder_png(self, path: str):
        """创建1x1像素PNG占位图（最小有效PNG，python-pptx可正常嵌入）"""
        import struct
        import zlib

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

        with open(path, 'wb') as f:
            f.write(signature + ihdr + idat + iend)
