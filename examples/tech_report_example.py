#!/usr/bin/env python3
"""
OpenClaw PPT SKILL - 技术汇报PPT生成示例

本示例演示如何使用OpenClaw PPT SKILL生成一份技术汇报PPT，
包含完整的6步执行链路、人工确认、自动校验与演讲备注输出。
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pipeline import OpenClawPPTSkill


def main():
    """技术汇报PPT生成示例"""

    # 1. 初始化 SKILL（自动加载 config/global_config.yaml）
    skill = OpenClawPPTSkill()

    # 2. 定义生成需求（对齐 HarnessConfig Step1 must_collect_params）
    requirement = {
        "核心主题": "AI技术在金融风控中的应用",
        "目标受众": "金融科技部门技术负责人",
        "汇报时长": "15分钟",
        "总页数": 10,
        "交付格式": ".pptx",
        "品牌VI": "默认企业蓝（#165DFF）",
        "内容禁忌": "避免提及未上线的功能与客户隐私数据"
    }

    # 3. 可选：注入自定义确认回调（替代终端交互，适用于GUI/Web集成）
    # skill.set_confirm_callback(lambda check_point, details: True)

    # 4. 执行完整生成链路
    #   - 步骤1：需求解析与对齐（人工确认）
    #   - 步骤2：大纲与逻辑架构生成（人工确认）
    #   - 步骤3：单页内容设计（含信息密度即时校验）
    #   - 步骤4：布局设计
    #   - 步骤5：素材生成（图片+图表+CSV+源码）
    #   - 步骤6：全量校验与交付（人工确认）
    result = skill.execute_pipeline(requirement)

    # 5. 查看输出
    print(f"\n{'='*60}")
    print(f"🎉 生成完成！")
    print(f"{'='*60}")
    print(f"  PPT文件: {result}")
    print(f"  演讲备注: output/speaker_notes.txt")
    print(f"  图表数据: output/charts/")
    print(f"  图片素材: output/images/")


if __name__ == "__main__":
    main()
