import os
import re
from typing import Dict, Any, List, Optional, Callable

# 占位水印：兜底内容统一前缀，便于 B3 占位残留检测识别
PLACEHOLDER_MARK = "[占位·请替换]"


class ContentGenerator:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化内容生成器
        :param config: 全局配置字典，来自global_config.yaml
        """
        self.config = config
        self.vi = config.get("vi_spec", {})
        # 宿主 AI 内容回填回调（B1）。签名: fn(page_type, theme, audience, title) -> dict|None
        # 由宿主环境（WorkBuddy/OpenClaw/Hermes 等）通过 set_content_callback 注入。
        # 注入 => 内容由宿主 AI 真实生成(host_ai)；未注入 => 模板兜底(template_fallback)。
        # 技能不含任何外部 LLM 配置(api_key/endpoint/model)，用户零感知。
        self._content_callback: Optional[Callable[[str, str, str, str], Optional[Dict[str, Any]]]] = None

    def set_content_callback(self, callback: Callable[[str, str, str, str], Optional[Dict[str, Any]]]):
        """
        注入宿主 AI 内容回填回调（对齐 pipeline.set_confirm_callback 的注入范式）。
        callback(page_type, theme, audience, title) -> content dict 或 None
        - 返回 dict：至少含 body，可含 subtitle/code/chart_data/speaker_notes/image_prompt
        - 返回 None 或抛异常：自动降级到模板兜底
        """
        self._content_callback = callback

    def _fill(self, page_type: str, theme: str, audience: str, title: str, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        两级内容供给（v1.2 精简：仅宿主AI / 模板兜底，无外部API）：
        1. 宿主 AI callback 回填成功 -> generation_mode=host_ai
        2. 否则用传入的 template 兜底 -> generation_mode=template_fallback
        兜底内容由各 _gen_* 方法用 PLACEHOLDER_MARK 标注，绝不冒充真实数据。
        """
        if self._content_callback is not None:
            try:
                filled = self._content_callback(page_type, theme, audience, title)
                if filled and isinstance(filled, dict) and filled.get("body"):
                    merged = dict(template)
                    merged.update({k: v for k, v in filled.items() if v is not None})
                    merged["generation_mode"] = "host_ai"
                    return merged
            except Exception as e:
                print(f"⚠️ [内容生成] 宿主AI回填失败({page_type})，降级模板兜底：{e}")
        template["generation_mode"] = "template_fallback"
        return template

    # ================ 受众分级模型 ================
    # 2.8 受众适配：三级分层（技术/混合/业务），而非简单字符串包含
    AUDIENCE_LEVELS = {
        "technical": {
            "keywords": ["技术", "研发", "工程师", "架构", "开发", "CTO", "运维", "SRE", "算法", "数据"],
            "depth": "deep",
            "style": "技术原理→实现路径→踩坑经验→优化空间"
        },
        "hybrid": {
            "keywords": ["产品", "负责人", "总监", "VP", "经理", "主管"],
            "depth": "medium",
            "style": "核心结论→关键指标→业务价值→下一步"
        },
        "business": {
            "keywords": ["CEO", "COO", "CFO", "业务", "运营", "市场", "销售", "高管"],
            "depth": "lite",
            "style": "做了什么→带来什么价值→投入产出比"
        }
    }

    def _classify_audience(self, audience: str) -> str:
        """将受众描述映射到技术深度等级"""
        for level, spec in self.AUDIENCE_LEVELS.items():
            for kw in spec["keywords"]:
                if kw in audience:
                    return level
        return "hybrid"  # 默认中等深度

    # ================ 步骤2：大纲与逻辑架构生成 ================
    def generate_outline(self, aligned_requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于金字塔原理生成全量大纲与叙事线
        :param aligned_requirement: 对齐后的用户需求
        :return: 包含叙事线和大纲结构的字典
        """
        theme = aligned_requirement["核心主题"]
        total_pages = aligned_requirement["总页数"]
        audience = aligned_requirement["目标受众"]

        # 2.6 叙事线通用化：遵循「是什么→为什么→怎么做→有什么效果→下一步」闭环逻辑
        narrative_line = (
            f"「{theme}」是什么 → 为什么需要「{theme}」 → 「{theme}」核心方案与实施路径 "
            f"→ 「{theme}」落地效果与数据验证 → 后续规划与下一步行动"
        )

        # 基础大纲结构（可根据页数动态扩展）
        base_outline = [
            {"page_id": "cover", "page_type": "封面页", "title": theme},
            {"page_id": "agenda", "page_type": "议程页", "title": "汇报议程"},
            {"page_id": "background", "page_type": "背景痛点页", "title": f"为什么需要「{theme}」"},
            {"page_id": "solution_core", "page_type": "核心方案页", "title": f"「{theme}」的核心架构"},
            {"page_id": "tech_detail", "page_type": "技术细节页", "title": "关键技术实现路径"},
            {"page_id": "result", "page_type": "成果验证页", "title": "效果验证与数据对比"},
            {"page_id": "risk_plan", "page_type": "风险规划页", "title": "风险应对与下一步规划"},
            {"page_id": "summary", "page_type": "总结Q&A页", "title": "总结与Q&A"}
        ]

        # 2.5 动态调整页数，确保核心方案页占60%
        final_outline = self._adjust_outline_pages(base_outline, total_pages, theme)

        print(f"✅ [内容生成] 大纲完成，叙事线：{narrative_line}，共{len(final_outline)}页")
        return {
            "叙事线": narrative_line,
            "大纲结构": final_outline,
            "目标受众": audience
        }

    def _adjust_outline_pages(self, base_outline: List[Dict], total_pages: int, theme: str = "") -> List[Dict]:
        """
        动态调整大纲页数
        - 核心方案/分论点页占60%页数（HarnessConfig mandatory_structure）
        - 截断时保留首尾必选项（封面+总结Q&A）
        - 扩展时在核心方案区插入分论点页
        """
        # 必选页面：封面(0) + 总结Q&A(末尾)
        MANDATORY_TAIL = ["总结Q&A页"]

        if total_pages <= len(base_outline):
            # 2.5 截断逻辑：保留首尾必选项，从中间删除
            result = list(base_outline)  # 浅拷贝，不修改原列表

            # 先保证总结Q&A页保留
            tail_pages = [p for p in result if p["page_type"] in MANDATORY_TAIL]
            core_pages = [p for p in result if p["page_type"] not in ["封面页"] + MANDATORY_TAIL]

            # 需要保留的总页数 = total_pages - 1(封面) - len(tail_pages)
            keep_from_middle = total_pages - 1 - len(tail_pages)
            if keep_from_middle < 0:
                keep_from_middle = 0

            result = [result[0]] + core_pages[:keep_from_middle] + tail_pages
            return result
        else:
            # 扩展：在核心方案页后插入分论点页，确保核心方案占比≥60%
            result = list(base_outline)  # 浅拷贝
            extra_pages = total_pages - len(base_outline)

            # 找到核心方案页的索引（动态计算，而非硬编码 insert_pos=4）
            core_idx = None
            for i, p in enumerate(result):
                if p["page_type"] == "核心方案页":
                    core_idx = i
                    break
            if core_idx is None:
                core_idx = 3  # 兜底

            for i in range(extra_pages):
                result.insert(
                    core_idx + 1 + i,
                    {
                        "page_id": f"solution_ext_{i+1}",
                        "page_type": "核心方案扩展页",
                        "title": f"核心方案细节：模块{i+1}"
                    }
                )

            # 验证核心方案页占比（核心方案页+扩展页+技术细节页 应占总页数60%）
            core_count = sum(1 for p in result if p["page_type"] in ["核心方案页", "核心方案扩展页", "技术细节页"])
            ratio = core_count / len(result)
            if ratio < 0.6:
                print(f"⚠️ [大纲调整] 核心方案页占比 {ratio:.0%}，低于60%要求，建议增加核心方案扩展页")

            return result

    # ================ 步骤3：单页内容设计 ================
    def generate_page_content(self, outline: Dict[str, Any], aligned_requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成单页内容与核心观点（结论式标题+分层内容）
        :param outline: 大纲字典
        :param aligned_requirement: 对齐后的用户需求
        :return: 单页内容字典
        """
        page_content = {}
        audience = outline["目标受众"]
        theme = aligned_requirement["核心主题"]
        audience_level = self._classify_audience(audience)
        taboos = aligned_requirement.get("内容禁忌", "")

        for page in outline["大纲结构"]:
            page_id = page["page_id"]
            page_type = page["page_type"]
            raw_title = page["title"]

            # 根据页面类型分发内容生成
            if page_type == "封面页":
                content = self._gen_cover(raw_title, aligned_requirement)
            elif page_type == "议程页":
                content = self._gen_agenda(raw_title, outline["大纲结构"])
            elif page_type == "背景痛点页":
                content = self._gen_background(raw_title, theme, audience, audience_level)
            elif page_type in ["核心方案页", "核心方案扩展页"]:
                content = self._gen_solution(raw_title, theme, audience, audience_level, page_id)
            elif page_type == "技术细节页":
                content = self._gen_tech_detail(raw_title, theme, audience, audience_level)
            elif page_type == "成果验证页":
                content = self._gen_result(raw_title, theme, audience, audience_level)
            elif page_type == "风险规划页":
                content = self._gen_risk_plan(raw_title, theme, audience, audience_level)
            elif page_type == "总结Q&A页":
                content = self._gen_summary(raw_title, theme, audience_level)
            else:
                content = self._gen_generic(raw_title)

            # 未经 _fill 的页面（封面/议程/总结/通用）标记为 template_fallback（结构性内容，非造假）
            content.setdefault("generation_mode", "template_fallback")
            page_content[page_id] = content

        print(f"✅ [内容生成] 单页内容完成，共{len(page_content)}页")
        return page_content

    # ================ 页面类型专属内容生成方法 ================
    def _gen_cover(self, title: str, req: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": title,
            "subtitle": f"汇报人：OpenClaw PPT Skill | 时间：2026年",
            "body": "",
            "image_prompt": f"商务科技风封面背景，主题为「{title}」，简洁大气",
            "chart_data": None,
            "speaker_notes": (
                f"【开场话术】各位好，今天我将为大家汇报「{title}」。\n"
                f"【停顿点】停顿2秒，环顾全场，确认听众注意力。\n"
                f"【互动设计】可以提问'在座有多少人接触过相关方案？'做破冰。\n"
                f"【补充细节】本次汇报预计{req.get('汇报时长', '15分钟')}，共{req.get('总页数', '10')}页。"
            )
        }

    def _gen_agenda(self, title: str, outline: List[Dict]) -> Dict[str, Any]:
        # 仅展示非封面/总结的议程，限制不超过4项
        agenda_items = [p["title"] for p in outline if p["page_type"] not in ["封面页", "总结Q&A页"]][:4]
        agenda_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(agenda_items)])
        return {
            "title": title,
            "body": agenda_text,
            "image_prompt": None,
            "chart_data": None,
            "speaker_notes": (
                "【话术】下面我将从以下几个方面展开：\n"
                + "\n".join([f"  第{i+1}点：{item}" for i, item in enumerate(agenda_items)])
                + "\n【停顿点】每项之间停顿1秒，让听众消化。"
            )
        }

    def _gen_background(self, title: str, theme: str, audience: str, audience_level: str) -> Dict[str, Any]:
        # 结论式标题（结构性，非造假，可保留主题相关表述）
        conclusion_title = title
        # 模板兜底：给出结构引导，不编造任何具体数字/技术栈
        template = {
            "title": conclusion_title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的背景与核心痛点（建议 3 条，每条含量化数据支撑）：\n"
                "1. 现状痛点一（附可溯源数据）\n"
                "2. 现状痛点二（附可溯源数据）\n"
                "3. 现状痛点三（附可溯源数据）"
            ),
            "image_prompt": f"{theme} 业务痛点可视化概念图，科技风",
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」实际背景撰写话术；\n"
                "【停顿点】讲完每个数据点后停顿1秒；\n"
                "【互动设计】可问听众是否有类似痛点。"
            )
        }
        return self._fill("背景痛点页", theme, audience, title, template)

    def _gen_solution(self, title: str, theme: str, audience: str, audience_level: str, page_id: str) -> Dict[str, Any]:
        template = {
            "title": title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的核心方案（建议 3 个分论点，逻辑递进）：\n"
                "1. 分论点一\n"
                "2. 分论点二\n"
                "3. 分论点三"
            ),
            "image_prompt": f"{theme} 核心方案架构示意图，科技风",
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」讲解核心方案，每个分论点停顿1秒。"
            )
        }
        return self._fill("核心方案页", theme, audience, title, template)

    def _gen_tech_detail(self, title: str, theme: str, audience: str, audience_level: str) -> Dict[str, Any]:
        template = {
            "title": title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的关键技术实现（技术受众可含技术栈/优化点，业务受众讲价值）：\n"
                "• 关键点一\n• 关键点二\n• 关键点三"
            ),
            "code": None,
            "image_prompt": f"{theme} 技术架构图",
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」讲解技术实现路径；完整代码/部署细节放附录。"
            )
        }
        return self._fill("技术细节页", theme, audience, title, template)

    def _gen_result(self, title: str, theme: str, audience: str, audience_level: str) -> Dict[str, Any]:
        template = {
            "title": title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的落地效果（建议用前后对比+量化指标）：\n"
                "• 指标一：改造前 → 改造后\n"
                "• 指标二：改造前 → 改造后\n"
                "• 指标三：改造前 → 改造后"
            ),
            "image_prompt": None,
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」真实数据讲解成效，核心数据后停顿2秒。"
            )
        }
        return self._fill("成果验证页", theme, audience, title, template)

    def _gen_risk_plan(self, title: str, theme: str, audience: str, audience_level: str) -> Dict[str, Any]:
        template = {
            "title": title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的风险应对与下一步规划：\n"
                "风险与应对：\n• 风险一 → 应对措施\n• 风险二 → 应对措施\n\n"
                "下一步规划：\n• 近期里程碑\n• 中期里程碑"
            ),
            "image_prompt": None,
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」讲解风险应对与规划，风险与规划之间停顿2秒过渡。"
            )
        }
        return self._fill("风险规划页", theme, audience, title, template)

    def _gen_summary(self, title: str, theme: str, audience_level: str) -> Dict[str, Any]:
        template = {
            "title": title,
            "body": (
                f"{PLACEHOLDER_MARK} 请填写「{theme}」的核心总结（3 条，呼应正文结论）：\n"
                "1. 核心结论一\n2. 核心结论二\n3. 核心结论三"
            ),
            "image_prompt": f"{theme} 总结/感谢的商务科技风配图",
            "chart_data": None,
            "speaker_notes": (
                f"{PLACEHOLDER_MARK} 结合「{theme}」总结三个核心要点，结束后停顿3秒进入 Q&A。"
            )
        }
        return self._fill("总结Q&A页", theme, self.vi.get("audience", ""), title, template)

    def _gen_generic(self, title: str) -> Dict[str, Any]:
        return {
            "title": title,
            "body": "此处为通用内容，可根据业务需求定制补充",
            "image_prompt": None,
            "chart_data": None,
            "speaker_notes": "【话术】本页为补充内容页，可根据实际需求自定义。"
        }
