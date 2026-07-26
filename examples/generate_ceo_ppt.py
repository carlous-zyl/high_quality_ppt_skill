#!/usr/bin/env python3
"""
基于《三方投顾公司数智化转型战略报告》生成CEO交流PPT
受众：客户CEO（business级，结论先行，数据说话）
"""
import sys
import os
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pipeline import OpenClawPPTSkill
from core.content_generator import ContentGenerator
from core.layout_designer import LayoutDesigner
from tools.chart_generator import ChartGenerator
from tools.pptx_generator import PPTXGenerator
from validators.consistency_checker import ConsistencyChecker
from validators.compliance_checker import ComplianceChecker


def generate_ceo_ppt():
    """基于战略报告生成CEO交流PPT"""

    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'global_config.yaml')
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["execution_mode"] = "auto"

    # 初始化各模块
    content_gen = ContentGenerator(config)
    layout_designer = LayoutDesigner(config)
    chart_gen = ChartGenerator(config)
    pptx_gen = PPTXGenerator(config)
    consistency_checker = ConsistencyChecker(config)
    compliance_checker = ComplianceChecker(config)

    # ============================================
    # CEO受众定制化内容（基于战略报告原文提取）
    # ============================================
    theme = "三方投顾数智化转型战略"

    page_content = {
        "cover": {
            "title": "三方投顾数智化转型战略",
            "subtitle": "AI Agent时代的生存路径与竞争策略 | 2026年5月",
            "body": "",
            "image_prompt": "商务科技风封面，蓝金色调，象征战略转型与突破",
            "chart_data": None,
            "speaker_notes": (
                "【开场话术】各位领导好，今天我将汇报三方投顾行业在AI Agent时代面临的战略拐点与转型路径。\n"
                "【停顿点】停顿2秒，环顾全场。\n"
                "【互动设计】提问：在座有多少人感受到行业正在加速分化？\n"
                "【补充细节】本汇报基于六大咨询框架系统性诊断，数据来源包括证券时报、新浪财经、财联社等。"
            )
        },
        "agenda": {
            "title": "汇报议程",
            "body": "1. 行业拐点：三年窗口期，不转型即出局\n2. 千亿蓝海：中国CAGR超25%的增长机遇\n3. 竞争格局：三足鼎立下的生存法则\n4. AI Agent转型：技术架构与核心Agent矩阵\n5. 战略路线图：24个月FAST转型路径",
            "image_prompt": None,
            "chart_data": None,
            "speaker_notes": (
                "【话术】我将从五个方面展开汇报：\n"
                "1. 行业正站在历史性拐点，三年窗口期是核心判断\n"
                "2. 千亿蓝海市场已验证\n"
                "3. 竞争格局急剧分化\n"
                "4. AI Agent是转型的核心武器\n"
                "5. 我们有清晰的24个月转型路线图\n"
                "【停顿点】每项之间停顿1秒。"
            )
        },
        "critical_judgment": {
            "title": "核心判断：三年窗口期，不转型即出局",
            "body": "• 行业综合健康度仅54.9/100，处于「亚健康」状态\n• 持牌机构从83家收缩至76家，市场加速出清\n• 技术代差扩大：头部研发5-15亿 vs 中小<500万\n• 荐股服务费占收入80%+，商业模式可持续性存疑\n• 监管处罚常态化：2025年326张罚单，同比+36.59%",
            "image_prompt": "战略决策概念图，十字路口隐喻",
            "chart_data": {
                "type": "bar",
                "title": "行业核心风险指标",
                "data": {
                    "x": ["持牌机构数(家)", "罚单数(张)", "荐股费占比(%)", "健康度评分"],
                    "y": [76, 326, 80, 54.9],
                    "y_label": "数值"
                }
            },
            "speaker_notes": (
                "【话术】行业综合战略健康度仅54.9分，处于亚健康。最核心的判断是：技术窗口期仅剩约3年。\n"
                "三个关键数据：机构数持续收缩、监管处罚+37%、荐股费依赖80%+。\n"
                "【停顿点】每个数据讲完后停顿1秒，让数据说话。\n"
                "【互动设计】可以问：大家是否感受到监管和技术的双重压力正在加速？"
            )
        },
        "market_opportunity": {
            "title": "千亿蓝海：中国智能投顾市场CAGR超25%",
            "body": "• 2030年中国市场突破2000亿，三方投顾SOM达500亿\n• 潜在市场规模1250亿（2.5亿投资者×500元/年）\n• 当前渗透率仅约15%，增长空间巨大\n• 四大驱动力：投资者基础、AI降本增效、政策红利、买方转型",
            "image_prompt": "增长曲线与市场蓝海概念图",
            "chart_data": {
                "type": "line",
                "title": "中国智能投顾市场规模预测（亿元）",
                "data": {
                    "x": ["2024", "2025", "2026", "2027", "2028", "2029", "2030"],
                    "y": [190, 257, 321, 440, 620, 950, 2000],
                    "x_label": "年份",
                    "y_label": "市场规模（亿元）"
                }
            },
            "speaker_notes": (
                "【话术】市场机会是巨大的。中国CAGR超25%，是全球增速的3倍以上。\n"
                "2030年2000亿市场，当前渗透率仅15%。AI降本增效ROI已经验证：效率+50%、成本-40%、合规事故-60%。\n"
                "【停顿点】讲完2000亿数据后停顿2秒。\n"
                "【补充细节】数据来源：新浪财经、证券时报。"
            )
        },
        "competition": {
            "title": "竞争格局：三足鼎立，差异化是唯一出路",
            "body": "• 互联网系：同花顺月活3502万，研发11.45亿，AI评分9.3\n• 金融机构系：中金财富买方投顾1200亿+\n• 独立三方：九方智投「AI+专业投研」双轮突围\n• 波特五力综合指数6.6/10，行业竞争压力极高\n• 战略结论：专业化+AI化是突围唯一路径",
            "image_prompt": "三足鼎立竞争格局示意图",
            "chart_data": None,
            "speaker_notes": (
                "【话术】行业已形成三足鼎立格局。我们最大的竞争对手不是彼此，而是时间窗口。\n"
                "同花顺年研发11.45亿，蚂蚁已补齐全牌照。正面硬刚难度极大，必须走差异化路线。\n"
                "【停顿点】讲完竞争格局后停顿1秒。\n"
                "【互动设计】可以问：大家认为我们最大的差异化优势是什么？"
            )
        },
        "tech_architecture": {
            "title": "AI Agent技术架构：五层体系+四大核心Agent",
            "body": "• 编排层(L4)：LangGraph多智能体协同——差异化核心\n• 数据层(L2)：知识图谱+向量库——专业壁垒\n• 四大Agent：基本面/技术面/消息面/投资陪伴\n• 关键突破：从「问答挂件」到「原生智能体」的范式革命\n• Human-in-the-Loop：AI输出100%经合规审核",
            "image_prompt": "五层智能体技术架构图，蓝色科技风",
            "chart_data": None,
            "speaker_notes": (
                "【话术】技术架构的核心差异在于L4编排层和L2数据层——这是互联网巨头难以快速复制的专业壁垒。\n"
                "四大Agent通过LangGraph协同，形成完整的AI+IP投顾服务闭环。\n"
                "关键原则：所有AI输出必须经人工审核，合规前置。\n"
                "【停顿点】每层讲完后停顿1秒。\n"
                "【补充细节】技术选型采用开源大模型+垂直微调，初始投入可控在2000万以内。"
            )
        },
        "strategy_roadmap": {
            "title": "24个月转型路线图：FAST模型",
            "body": "• F-基础建设(H2'26)：合规先行，AI投研三大场景上线\n• A-智能体深化(H1'27)：四类Agent全面上线，效率+50%\n• S-模式转型(H2'27)：AUM管理费迁移至30%\n• T-生态扩展(2028)：开放API，AUM+100%",
            "image_prompt": "四阶段转型路线图，时间轴构图",
            "chart_data": {
                "type": "bar",
                "title": "转型量化目标",
                "data": {
                    "x": ["投顾效率+", "人力成本-", "合规事故-", "AUM规模+"],
                    "y": [50, 40, 60, 100],
                    "y_label": "变化幅度(%)"
                }
            },
            "speaker_notes": (
                "【话术】24个月转型分四个阶段。第一阶段最关键：合规先行打地基，AI投研快落地。\n"
                "量化目标明确：效率+50%、成本-40%、合规事故-60%、AUM+100%。\n"
                "【停顿点】讲完量化目标后停顿2秒，让听众消化。\n"
                "【互动设计】可以问：大家对第一阶段6个月落地AI投研三大场景的时间线是否有信心？\n"
                "【补充细节】荐股费占比目标：80%→50%→30%。"
            )
        },
        "ksf": {
            "title": "转型成功的四大关键要素",
            "body": "• KSF1 一把手工程：CEO亲自挂帅，不是IT项目\n• KSF2 合规前置：每个AI功能上线前必过合规审查\n• KSF3 数据资产优先：客户行为数据是专业AI的不可替代基础\n• KSF4 人才与组织：引进+培养+合作三路并进",
            "image_prompt": "四大支柱概念图，稳重商务风",
            "chart_data": None,
            "speaker_notes": (
                "【话术】转型能否成功，关键在于这四个要素。最重要的一点：这是一把手工程，不是IT项目。\n"
                "合规前置是底线，数据资产是根基，人才是保障。\n"
                "【停顿点】每个要素讲完后停顿1秒。\n"
                "【互动设计】可以问：各位认为当前组织架构是否支撑这种转型？"
            )
        },
        "summary": {
            "title": "总结与行动建议",
            "body": "核心结论：\n1. 三年窗口期是确定性判断，不转型即出局\n2. 千亿蓝海已验证，AI降本增效ROI清晰\n3. 合规先行→AI投研落地→模式转型→生态扩展\n\n行动建议：\n• 立即启动第一阶段基础建设\n• 营收5%+投入合规体系\n• 2000万启动AI投研三大场景",
            "image_prompt": "感谢观看的商务科技风配图",
            "chart_data": None,
            "speaker_notes": (
                "【话术】总结三个核心结论：\n"
                "1. 三年窗口期是确定性的，犹豫即出局\n"
                "2. 市场机会已验证，AI的ROI清晰可量化\n"
                "3. 路线图明确：合规先行→快速落地→模式转型→生态扩展\n\n"
                "行动建议：立即启动第一阶段，合规预算不低于5%，AI投研2000万可控启动。\n"
                "【停顿点】总结后停顿3秒，进入Q&A。\n"
                "【互动设计】开放提问环节。"
            )
        }
    }

    # ============================================
    # 步骤4：布局设计
    # ============================================
    layout_spec = layout_designer.design_layout(page_content)

    # ============================================
    # 步骤5：素材生成
    # ============================================
    from tools.image_generator import ImageGenerator
    image_gen = ImageGenerator(config)
    images = image_gen.generate_images(page_content)
    charts = chart_gen.generate_charts(page_content)
    materials = {"images": images, "charts": charts}

    # ============================================
    # 步骤6：校验与交付
    # ============================================
    consistency_ok = consistency_checker.check(page_content, layout_spec)
    compliance_ok = compliance_checker.check(page_content, layout_spec, materials)

    print(f"一致性校验：{'✅ 通过' if consistency_ok else '⚠️ 需修正'}")
    print(f"合规性校验：{'✅ 通过' if compliance_ok else '⚠️ 需修正'}")

    output_path = pptx_gen.generate_pptx(page_content, layout_spec, materials)

    # 导出演讲备注
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    notes_path = os.path.join(output_dir, "speaker_notes_三方投顾CEO交流.txt")
    with open(notes_path, "w", encoding="utf-8") as f:
        for page_id, content in page_content.items():
            notes = content.get("speaker_notes", "")
            if notes:
                f.write(f"【{page_id}】{content.get('title', '')}\n")
                f.write(f"{notes}\n\n")

    print(f"\n{'='*60}")
    print(f"🎉 CEO交流PPT生成完成！")
    print(f"{'='*60}")
    print(f"  PPT文件: {output_path}")
    print(f"  演讲备注: {notes_path}")
    print(f"  图表数据: output/charts/")
    print(f"  图片素材: output/images/")

    return output_path


if __name__ == "__main__":
    result = generate_ceo_ppt()
    print(f"\n最终输出: {result}")
