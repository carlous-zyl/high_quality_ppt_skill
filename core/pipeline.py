import yaml
from typing import Dict, Any, Optional, Callable
from core.content_generator import ContentGenerator
from core.layout_designer import LayoutDesigner
from tools.image_generator import ImageGenerator
from tools.chart_generator import ChartGenerator
from tools.pptx_generator import PPTXGenerator
from validators.consistency_checker import ConsistencyChecker
from validators.compliance_checker import ComplianceChecker

class OpenClawPPTSkill:
    def __init__(self, config_path: str = "config/global_config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.content_gen = ContentGenerator(self.config)
        self.layout_designer = LayoutDesigner(self.config)
        self.image_gen = ImageGenerator(self.config)
        self.chart_gen = ChartGenerator(self.config)
        self.pptx_gen = PPTXGenerator(self.config)
        self.consistency_checker = ConsistencyChecker(self.config)
        self.compliance_checker = ComplianceChecker(self.config)

        # HarnessConfig: 执行模式与重试配置
        self.execution_mode = self.config.get("execution_mode", "human_confirm")
        self.max_retry_times = self.config.get("max_retry_times", 2)
        self.enable_force_requirement_check = self.config.get("enable_force_requirement_check", True)
        self.enable_step_by_step_execution = self.config.get("enable_step_by_step_execution", True)

        # 人工确认回调（默认为终端交互，可注入GUI/Web回调）
        self._confirm_callback: Optional[Callable[[str, str], bool]] = None

    def set_confirm_callback(self, callback: Callable[[str, str], bool]):
        """
        注入人工确认回调函数，用于 human_confirm 模式。
        回调签名: callback(check_point_name: str, details: str) -> bool
        """
        self._confirm_callback = callback

    def set_content_callback(self, callback: Callable[[str, str, str, str], Any]):
        """
        注入宿主 AI 内容回填回调（透传给 ContentGenerator）。
        宿主环境(WorkBuddy/OpenClaw/Hermes)注入后，单页内容由宿主 AI 真实生成；
        未注入则走模板兜底([占位·请替换])。技能不含任何外部 LLM 配置，用户零感知。
        回调签名: callback(page_type, theme, audience, title) -> content dict 或 None
        """
        self.content_gen.set_content_callback(callback)

    def execute_pipeline(self, user_requirement: Dict[str, Any]) -> str:
        """执行完整PPT生成链路（6步串行，严格禁止跳步）"""

        # 步骤1：需求解析与对齐
        aligned_requirement = self._execute_step_with_retry(
            step_id=1,
            step_fn=self._step1_requirement_alignment,
            args=(user_requirement,),
            fail_msg="需求对齐失败"
        )
        if not aligned_requirement:
            return "❌ 需求对齐失败，请补充必填参数后重试"

        # 步骤2：大纲与逻辑架构生成
        outline = self._execute_step_with_retry(
            step_id=2,
            step_fn=self._step2_outline_generation,
            args=(aligned_requirement,),
            fail_msg="大纲生成失败"
        )
        if not outline:
            return "❌ 大纲生成失败，请重试"

        # 步骤3：单页内容设计（含信息密度即时校验）
        page_content = self._execute_step_with_retry(
            step_id=3,
            step_fn=self._step3_page_content_design,
            args=(outline, aligned_requirement),
            fail_msg="单页内容设计失败"
        )
        if not page_content:
            return "❌ 单页内容设计失败，请重试"

        # 步骤4：布局设计
        layout_spec = self._execute_step_with_retry(
            step_id=4,
            step_fn=self._step4_layout_design,
            args=(page_content,),
            fail_msg="布局设计失败"
        )
        if not layout_spec:
            return "❌ 布局设计失败，请重试"

        # 步骤5：素材生成
        materials = self._execute_step_with_retry(
            step_id=5,
            step_fn=self._step5_material_generation,
            args=(layout_spec, page_content),
            fail_msg="素材生成失败"
        )
        if not materials:
            return "❌ 素材生成失败，请重试"

        # 步骤6：全量校验与交付（传入aligned_requirement以校验符合用户初始需求）
        final_ppt = self._step6_validation_and_delivery(
            page_content, layout_spec, materials, aligned_requirement
        )
        return final_ppt

    # ================ 带重试的步骤执行器 ================
    def _execute_step_with_retry(self, step_id: int, step_fn, args: tuple, fail_msg: str):
        """HarnessConfig: max_retry_times=2, next_step_on_fail=当前步骤重试"""
        last_result = None
        for attempt in range(1, self.max_retry_times + 1):
            result = step_fn(*args)
            if result:
                return result
            last_result = result
            if attempt < self.max_retry_times:
                print(f"⚠️ [步骤{step_id}] 第{attempt}次尝试失败，正在重试...")
        print(f"❌ [步骤{step_id}] 已重试{self.max_retry_times}次，{fail_msg}")
        return last_result

    # ================ HarnessConfig: 人工确认机制 ================
    def _human_confirm(self, check_point: str, details: str) -> bool:
        """
        HarnessConfig mandatory_check_points 实现：
        - "需求对齐确认"（步骤1后）
        - "大纲确认"（步骤2后）
        - "最终交付确认"（步骤6后）
        """
        if self.execution_mode != "human_confirm":
            return True  # auto模式自动通过

        if self._confirm_callback:
            return self._confirm_callback(check_point, details)

        # 默认终端交互确认
        print(f"\n{'='*60}")
        print(f"📋 [人工确认点] {check_point}")
        print(f"{'='*60}")
        print(details)
        print(f"{'='*60}")
        while True:
            choice = input("确认通过？(y/n): ").strip().lower()
            if choice in ("y", "yes"):
                return True
            elif choice in ("n", "no"):
                return False
            print("请输入 y 或 n")

    # ================ 步骤1：需求解析与对齐 ================
    def _step1_requirement_alignment(self, user_requirement: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        HarnessConfig Step1:
        - must_collect_params: 核心主题与汇报目标、目标受众、汇报时长与总页数、交付格式、品牌VI、内容禁忌
        - output: requirement_alignment_form
        - check_rule: 所有必填参数已采集，用户已确认需求
        """
        # 2.1 补全必填参数（HarnessConfig must_collect_params）
        required_params = [
            "核心主题",       # 核心主题与汇报目标
            "目标受众",       # 技术背景/职级/核心诉求
            "汇报时长",       # 汇报时长
            "总页数",         # 总页数范围
            "交付格式",       # .pptx/.key/markdown
            "品牌VI",         # 品牌VI/模板强制要求
            "内容禁忌",       # 内容禁忌与合规要求
        ]
        missing_params = [p for p in required_params if p not in user_requirement]

        # enable_force_requirement_check: 未补全参数禁止进入生成环节
        if missing_params and self.enable_force_requirement_check:
            print(f"❌ [需求对齐] 缺少必填参数：{missing_params}")
            return None

        if missing_params:
            print(f"⚠️ [需求对齐] 缺少参数（非强制）：{missing_params}")

        # 2.2 人工确认：需求对齐确认
        detail_lines = [f"  {k}: {v}" for k, v in user_requirement.items()]
        confirmed = self._human_confirm(
            "需求对齐确认",
            "以下为对齐后的需求：\n" + "\n".join(detail_lines)
        )
        if not confirmed:
            print("❌ [需求对齐] 用户未确认需求，流程终止")
            return None

        # 输出 requirement_alignment_form
        alignment_form = dict(user_requirement)
        alignment_form["_alignment_confirmed"] = True
        print("✅ [步骤1] 需求对齐完成，用户已确认")
        return alignment_form

    # ================ 步骤2：大纲与逻辑架构生成 ================
    def _step2_outline_generation(self, aligned_requirement: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        HarnessConfig Step2:
        - check_rule: 符合金字塔原理，叙事线清晰，结构完整，页数符合需求，用户已确认大纲
        """
        outline = self.content_gen.generate_outline(aligned_requirement)
        if not outline:
            return None

        # 2.4 人工确认：大纲确认
        outline_details = (
            f"叙事线：{outline.get('叙事线', 'N/A')}\n"
            f"页数：{len(outline.get('大纲结构', []))}页\n"
            + "\n".join([f"  {p['page_id']}: {p['title']} ({p['page_type']})"
                         for p in outline.get("大纲结构", [])])
        )
        confirmed = self._human_confirm("大纲确认", outline_details)
        if not confirmed:
            print("❌ [步骤2] 用户未确认大纲，流程终止")
            return None

        print("✅ [步骤2] 大纲生成完成，用户已确认")
        return outline

    # ================ 步骤3：单页内容设计 ================
    def _step3_page_content_design(self, outline: Dict[str, Any], aligned_requirement: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        HarnessConfig Step3:
        - constraint_bind: 信息密度硬约束（单页正文≤300字）
        - check_rule: 每页仅1个核心观点，技术内容适配受众
        """
        page_content = self.content_gen.generate_page_content(outline, aligned_requirement)
        if not page_content:
            return None

        # 2.7 信息密度即时校验（步骤3完成后立即检查，而非延迟到步骤6）
        density_ok = self.compliance_checker.check_information_density(page_content)
        if not density_ok:
            print("⚠️ [步骤3] 信息密度校验未通过，尝试自动截断超长内容...")
            page_content = self._auto_truncate_content(page_content)

        print("✅ [步骤3] 单页内容设计完成")
        return page_content

    def _auto_truncate_content(self, page_content: Dict[str, Any]) -> Dict[str, Any]:
        """自动截断超长正文（信息密度自动优化）"""
        max_chars = 300
        for page_id, content in page_content.items():
            body = content.get("body", "")
            if len(body) > max_chars:
                # 截断到300字，保留最后一行完整性
                truncated = body[:max_chars]
                last_newline = truncated.rfind("\n")
                if last_newline > max_chars * 0.7:
                    truncated = truncated[:last_newline]
                content["body"] = truncated + "\n…（详见演讲备注）"
                print(f"  📝 页面 {page_id} 正文已自动截断至{len(truncated)}字")
        return page_content

    # ================ 步骤4：布局设计 ================
    def _step4_layout_design(self, page_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """HarnessConfig Step4: 基于VI规范设计每页版式"""
        layout_spec = self.layout_designer.design_layout(page_content)
        if not layout_spec:
            return None
        print("✅ [步骤4] 布局设计完成")
        return layout_spec

    # ================ 步骤5：素材生成 ================
    def _step5_material_generation(self, layout_spec: Dict[str, Any], page_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """HarnessConfig Step5: 生成匹配内容的图片、图表、代码块"""
        images = self.image_gen.generate_images(page_content)
        charts = self.chart_gen.generate_charts(page_content)
        materials = {"images": images, "charts": charts}
        print("✅ [步骤5] 素材生成完成")
        return materials

    # ================ 步骤6：全量校验与交付 ================
    def _step6_validation_and_delivery(self, page_content: Dict[str, Any],
                                        layout_spec: Dict[str, Any],
                                        materials: Dict[str, Any],
                                        aligned_requirement: Dict[str, Any]) -> str:
        """
        HarnessConfig Step6:
        - required_input 含 requirement_alignment_form
        - auto_validation.fail_action: "auto_optimize"
        - 演讲备注写入PPT
        - 最终交付确认
        """
        # 2.13 使用 aligned_requirement 校验"符合用户初始需求"
        print(f"📋 [步骤6] 校验交付物是否符合需求主题：{aligned_requirement.get('核心主题', 'N/A')}")

        consistency_ok = self.consistency_checker.check(page_content, layout_spec)
        compliance_ok = self.compliance_checker.check(page_content, layout_spec, materials)

        # B2/B3: 生成模式汇总 + 占位残留检测
        self._report_generation_mode(page_content)

        # 2.11 自动优化：校验不通过时执行修正
        if not consistency_ok or not compliance_ok:
            print("⚠️ [步骤6] 校验失败，执行自动优化...")
            page_content, layout_spec = self._auto_optimize(page_content, layout_spec, materials)
            # 二次校验
            consistency_ok = self.consistency_checker.check(page_content, layout_spec)
            compliance_ok = self.compliance_checker.check(page_content, layout_spec, materials)
            if not consistency_ok or not compliance_ok:
                print("❌ [步骤6] 自动优化后仍有问题，需人工介入")

        # 2.12 演讲备注写入PPT
        output_path = self.pptx_gen.generate_pptx(page_content, layout_spec, materials)

        # 将演讲备注追加到交付包
        notes_path = self._export_speaker_notes(page_content)

        # 2.15 最终交付确认
        delivery_details = (
            f"PPT文件：{output_path}\n"
            f"演讲备注：{notes_path}\n"
            f"一致性校验：{'✅ 通过' if consistency_ok else '❌ 未通过'}\n"
            f"合规性校验：{'✅ 通过' if compliance_ok else '❌ 未通过'}"
        )
        self._human_confirm("最终交付确认", delivery_details)

        print(f"✅ [步骤6] 交付完成：{output_path}")
        return output_path

    # ================ B2/B3: 生成模式汇总 + 占位残留检测 ================
    def _report_generation_mode(self, page_content: Dict[str, Any]):
        """
        汇总各页 generation_mode，并检测 [占位·请替换] 残留。
        - host_ai：宿主 AI 真实生成
        - template_fallback：模板兜底（内容含占位水印，需替换）
        占位残留时告警但不阻断（B3：告警即可，不自动回炉）。
        """
        from core.content_generator import PLACEHOLDER_MARK

        host_ai, fallback, placeholder_pages = 0, 0, []
        for page_id, content in page_content.items():
            mode = content.get("generation_mode", "template_fallback")
            if mode == "host_ai":
                host_ai += 1
            else:
                fallback += 1
            body = str(content.get("body", "")) + str(content.get("speaker_notes", ""))
            if PLACEHOLDER_MARK in body:
                placeholder_pages.append(page_id)

        total = len(page_content)
        print(f"📊 [生成模式] 宿主AI生成 {host_ai}/{total} 页 | 模板兜底 {fallback}/{total} 页")
        if placeholder_pages:
            print(f"⚠️ [占位残留] {len(placeholder_pages)} 页仍含占位水印待替换：{placeholder_pages}")
            print("   提示：未注入宿主 AI content_callback，或宿主 AI 未覆盖这些页面。")
            print("   → 由宿主 AI 调用 set_content_callback 后重跑，可获得真实内容。")
        elif host_ai == total:
            print("✅ [占位残留] 全部页面由宿主 AI 真实生成，无占位残留")

    # ================ 自动优化实现 ================
    def _auto_optimize(self, page_content: Dict[str, Any],
                       layout_spec: Dict[str, Any],
                       materials: Dict[str, Any]) -> tuple:
        """
        HarnessConfig auto_optimize 实现：
        - 信息密度超限 → 自动截断
        - 配色不合规 → 自动替换为VI规范色
        - 版式不一致 → 统一为首个页面版式
        """
        # 1. 信息密度优化
        page_content = self._auto_truncate_content(page_content)

        # 2. 配色合规修正
        vi = self.config.get("vi_spec", {})
        allowed_colors = set()
        if vi:
            allowed_colors.add(vi.get("primary_color", ""))
            allowed_colors.add(vi.get("secondary_color", ""))
            allowed_colors.update(vi.get("neutral_colors", []))
            allowed_colors.discard("")

        for page_id, spec in layout_spec.items():
            if "colors" in spec:
                fixed_colors = [c if c in allowed_colors else vi.get("primary_color", "#165DFF")
                                 for c in spec["colors"]]
                spec["colors"] = fixed_colors

        # 3. 版式一致性修正：统一页边距
        if layout_spec:
            first_key = next(iter(layout_spec))
            reference_margin = layout_spec[first_key].get("margin", "20mm")
            for page_id, spec in layout_spec.items():
                if spec.get("margin") != reference_margin:
                    spec["margin"] = reference_margin
                    print(f"  🔧 页面 {page_id} 页边距已修正为 {reference_margin}")

        print("✅ [自动优化] 修正完成")
        return page_content, layout_spec

    # ================ 演讲备注导出 ================
    def _export_speaker_notes(self, page_content: Dict[str, Any]) -> str:
        """导出演讲备注为独立文件"""
        import os
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        notes_path = os.path.join(output_dir, "speaker_notes.txt")

        with open(notes_path, "w", encoding="utf-8") as f:
            for page_id, content in page_content.items():
                notes = content.get("speaker_notes", "")
                if notes:
                    f.write(f"【{page_id}】{content.get('title', '')}\n")
                    f.write(f"{notes}\n\n")
        print(f"📝 演讲备注已导出：{notes_path}")
        return notes_path

if __name__ == "__main__":
    skill = OpenClawPPTSkill()
    test_requirement = {
        "核心主题": "AI技术在金融风控中的应用",
        "目标受众": "金融科技部门技术负责人",
        "汇报时长": "15分钟",
        "总页数": 10,
        "交付格式": ".pptx",
        "品牌VI": "默认企业蓝",
        "内容禁忌": "避免提及未上线的功能与客户数据"
    }
    result = skill.execute_pipeline(test_requirement)
    print(f"PPT生成完成：{result}")
