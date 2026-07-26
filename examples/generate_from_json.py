#!/usr/bin/env python3
"""
从JSON结构化内容生成PPT
支持 layout 类型：cover / toc / bullets / steps / closing
"""
import sys
import os
import json
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.layout_designer import LayoutDesigner
from tools.image_generator import ImageGenerator
from tools.chart_generator import ChartGenerator
from tools.pptx_generator import PPTXGenerator
from validators.consistency_checker import ConsistencyChecker
from validators.compliance_checker import ComplianceChecker


# ================ 用户提供的JSON内容 ================
# image_prompt: 配图提示词，描述该页面需要的配图场景
# 如不提供，image_generator会根据title自动生成（_auto_generate_prompt）
SLIDES_JSON = [
  {
    "id": "slide-1",
    "layout": "cover",
    "title": "三年窗口期：三方投顾的生死竞速",
    "bullets": ["—— AI Agent 时代的生存路径与竞争策略"],
    "notes": "开场白：各位好。今天汇报的主题是三方投顾数智化转型。先抛结论——行业窗口期只有三年，不转型即出局。这不是危言耸听，是我们基于六大咨询框架系统性诊断后得出的结论。"
  },
  {
    "id": "slide-2",
    "layout": "toc",
    "title": "汇报纲要",
    "bullets": ["行业诊断：范式剧变与五力困局", "市场机遇：千亿蓝海与增长飞轮", "战略路径：SWOT × 风险 × Agent矩阵", "行动路线：FAST 四阶段转型路线图", "关键要素：人、合规、数据、组织"],
    "notes": "汇报分五个板块：先看行业发生了什么，再看市场有多大，然后是我们的战略选择，接着是具体怎么走，最后讲转型能不能成取决于什么。全程约20分钟。"
  },
  {
    "id": "slide-3",
    "layout": "bullets",
    "title": "核心判断：三年窗口期",
    "bullets": ["行业战略健康度仅 54.9/100，处于「亚健康」", "技术代差扩大：头部研发 5-15 亿 vs 中小 <500 万", "核心转型目标：效率 +50%、成本 -40%、AUM 翻倍"],
    "image_prompt": "倒计时沙漏场景，沙漏中流淌的不是沙子而是数据流和代码，暗示时间紧迫，背景是模糊的金融城市天际线",
    "notes": "54.9 分这个数字是基于波特五力、PESTLE、SWOT、TAM、BCG、风险矩阵六套框架综合打分。不是拍脑袋，是系统算出来的。重点看第三点——三个量化目标是我们整个转型路线的北极星指标。"
  },
  {
    "id": "slide-4",
    "layout": "bullets",
    "title": "范式剧变：卖方→买方",
    "bullets": ["旧范式：信息不对称套利 → 荐股费占收入 80%+", "新范式：专业能力创造价值 → AUM+SaaS+绩效分成", "格局重构：互联网巨头渗透、银行券商转型、三方突围"],
    "image_prompt": "商业范式转换场景，左侧是旧模式（单方向箭头从机构指向客户），右侧是新模式（双向循环箭头，机构与客户平等交互），中间由闪电连接表示变革",
    "notes": "行业核心矛盾是什么？盈利模式。荐股服务费占收入80%以上，典型的「付费前推涨停、付费后高位套牢」。续费率持续走低，形成拉新-流失-再拉新的恶性循环。不解决这个根本问题，其他都是修修补补。"
  },
  {
    "id": "slide-5",
    "layout": "bullets",
    "title": "千亿蓝海：市场机遇",
    "bullets": ["中国智能投顾市场 2030 年突破 2000 亿，CAGR 25%+", "2.5 亿投资者 × 人均 500 元 = 1250 亿潜在市场", "四大驱动力：投资者基数、AI 降本已验证、政策红利、买方转型"],
    "image_prompt": "市场增长趋势可视化，向上攀升的柱状图融入海洋意象，蓝色和绿色的数据柱从海面升起，背景是广阔的蓝海",
    "notes": "这里有个关键数字——CAGR 25%+，是全球增速的 3 倍以上。当前渗透率仅约15%。换句话说，市场还很大，但窗口期有限。谁先完成买方转型，谁就享有客户黏性红利。"
  },
  {
    "id": "slide-6",
    "layout": "bullets",
    "title": "宏观环境：技术×监管",
    "bullets": ["技术是最大机会（评分 9.0）：AI Agent 元年开启新赛道", "监管是最大威胁（评分 8.5）：年均 326 张罚单，同比 +36.59%", "2026 年 9 月重磅：投顾列为独立监管类别，严禁非持牌展业"],
    "image_prompt": "双面天平场景，左侧是AI芯片和神经网络象征技术机遇，右侧是天平和法槌象征监管约束，两者保持微妙平衡",
    "notes": "PESTLE 分析的结论非常清晰——技术和监管是两个 9 分级别的变量。必须两手抓：加速技术转型，同时强化合规防线。2026 年 9 月的新规是分水岭，不合规的机构将直接出局。"
  },
  {
    "id": "slide-7",
    "layout": "bullets",
    "title": "竞争格局：五力困局",
    "bullets": ["行业竞争压力指数 6.6/10 —— 高压力行业", "现有竞争者 8.5 分：头部 AI 护城河正在形成不可逆代差", "破局路径：专业化 + AI 化双轮驱动，正面竞争不如差异化"],
    "image_prompt": "商业竞争五力困局示意图，中心是一个企业图标，被五个方向的力箭头包围，每个箭头用不同颜色表示不同竞争力量",
    "notes": "波特五力最刺眼的数据：现有竞争者 8.5 分。同花顺年研发 11.45 亿，九方有九章大模型和数字人九哥服务 60 万客户。中小机构研发不到 500 万——这个代差不是缩小，是在扩大。我们的策略不是硬碰硬，而是在垂直领域用专业投研+AI做差异化。"
  },
  {
    "id": "slide-8",
    "layout": "bullets",
    "title": "SWOT：四大战略组合",
    "bullets": ["SO 进攻：用 AI 先发优势抢占买方转型蓝海", "WO 改善：优先部署高 ROI 场景（合规质检 -60%）", "ST 防御：深耕垂直知识图谱，打造「AI+IP」壁垒", "WT 收缩：退出低效产品线，集中资源聚焦核心客户"],
    "image_prompt": "SWOT四象限战略分析图，四个彩色象限分别标注优势、劣势、机会、威胁，中心交汇处是战略核心",
    "notes": "SWOT 不是做做样子，是给我们四个明确的行动方向。SO 是主攻方向——买方向转型。WO 最关键——合规质检降 60% 是投入产出比最高的场景，先从这里切入。ST 告诉我们，专业投研是我们的护城河，互联网玩家复制不了。"
  },
  {
    "id": "slide-9",
    "layout": "bullets",
    "title": "风险矩阵：三重极高",
    "bullets": ["监管合规风险 0.78（极高）—— 一次重罚可能停摆业务", "盈利模式风险 0.76（极高）—— 荐股费 80%+ 不可持续", "AI 幻觉是新型风险 —— Human-in-the-Loop 强制审核"],
    "image_prompt": "风险管控场景，三面不同颜色的警示盾牌排列成三角形，中心是一个保护性屏障，暗示三重风险的管控策略",
    "notes": "三重极高风险叠加，这不是一个舒服的局面。但最大的风险不是风险本身，是不行动。监管风险建议营收 5% 以上预算投入合规体系，设立 CCO。盈利模式风险必须立即启动转型。AI 幻觉——大模型生成虚假投资建议——这是全新的合规挑战，必须用 Human-in-the-Loop 机制兜底。"
  },
  {
    "id": "slide-10",
    "layout": "bullets",
    "title": "AI Agent：范式革命",
    "bullets": ["传统 AI：单轮问答、被动响应、无状态", "AI Agent：多轮推理、自主执行、持续记忆、目标驱动", "五层架构中 L4 编排层 + L2 数据层 = 差异化护城河"],
    "image_prompt": "AI Agent多智能体协同场景，多个发光的AI节点通过光线连接形成网络，中心是编排引擎节点，各节点间有数据流动的光效",
    "notes": "关键认知：传统的问答式 AI 挂件已经无法建立差异化壁垒。AI Agent 不一样——它能多轮推理、自主调用工具、持续记忆用户画像。我们的五层架构中，编排层和数据层是构建壁垒的关键。金融知识图谱+多 Agent 编排逻辑，是互联网巨头难以快速复制的。"
  },
  {
    "id": "slide-11",
    "layout": "bullets",
    "title": "四大 Agent 产品矩阵",
    "bullets": ["基本面 Agent：财务分析、估值模型、业绩预测 —— 分析师能力规模化", "技术面 Agent：K 线识别、量价分析 —— 7×24 不间断", "消息面 Agent：舆情监控、事件驱动、政策解读", "陪伴 Agent：风险教育、情绪管理 —— 解决因亏损流失的根本问题"],
    "image_prompt": "四类AI Agent产品矩阵，四个风格统一但功能不同的AI助手图标排成2x2网格，分别标注分析、监控、洞察、陪伴功能",
    "notes": "四类 Agent 通过 LangGraph 编排引擎协同工作。基本面 Agent 解决投研效率，技术面 Agent 解决覆盖面，消息面 Agent 解决信息速度，陪伴 Agent 解决客户留存。合在一起，就是完整的 AI+IP 投顾服务闭环。"
  },
  {
    "id": "slide-12",
    "layout": "bullets",
    "title": "BCG：资源配置抉择",
    "bullets": ["明星（重投）：AI 投研助手、AI 智能客服 —— 增速 45%/40%", "问号（探索）：投顾数字人、买方投顾平台 —— 增速 55%/60%", "核心结论：AI 产品投资占比从 30% → 60% 以上"],
    "image_prompt": "BCG波士顿矩阵示意图，四象限中明星象限和问号象限被高亮标注，箭头指示资源从现金牛流向明星和问号",
    "notes": "BCG 矩阵给的是一个资源配置的硬约束。传统荐股服务（现金牛）维持运营但不追加投资，用它的现金流支持明星和问号产品。未来三年，AI 相关投资占比必须翻倍到 60% 以上。这不是激进，是生存底线。"
  },
  {
    "id": "slide-13",
    "layout": "steps",
    "title": "FAST 四阶段路线图",
    "bullets": ["F·基础建设（2026 H2）：合规先行，AI 投研快落地 → 合规事故 -60%", "A·Agent 深化（2027 H1）：四类 Agent 上线，LangGraph 编排 → 效率 +50%", "S·模式转型（2027 H2）：AUM 管理费占 30%，SaaS 上线 → 收入结构重构", "T·生态扩展（2028）：开放 API，跨市场 Agent → AUM 翻倍"],
    "image_prompt": "四阶段转型路线图，从左到右的登山路径，四个里程碑标记F-A-S-T，山脚是基础设施，山顶是生态扩展，路径上有AI和数据的元素",
    "notes": "FAST 模型：Foundation → Agent → Switch → Transcend。第一阶段最紧迫——合规和 AI 投研同时推进。第二阶段是核心差异化——多 Agent 协同落地。第三阶段是商业模式的重构。第四阶段是打开天花板。整个路线 24 个月，分四步走。"
  },
  {
    "id": "slide-14",
    "layout": "bullets",
    "title": "转型成功的四大要素",
    "bullets": ["一把手工程：CEO 挂帅，不是 IT 项目是战略转型", "合规前置：每个 AI 功能上线前必须通过合规审查", "数据资产优先：客户交易行为、服务记录是 AI 不可替代的基础", "人才三路并进：引进复合人才 + 培养现有团队 + 产学研合作"],
    "image_prompt": "转型成功四大支柱场景，四根坚实的柱子支撑起一座现代化金融大厦，每根柱子分别标注领导力、合规、数据、人才",
    "notes": "这四条缺一不可。第一条最重要——如果 CEO 不亲自推，转型大概率会变成 IT 部门的自嗨项目。第二条是血的教训——监管处罚的损失远超技术投入。第三条，我们的数据资产是互联网巨头没有的。第四条，人永远是最稀缺的。"
  },
  {
    "id": "slide-15",
    "layout": "closing",
    "title": "今天的选择，定义三年后的座次",
    "bullets": ["这不是激进的愿景，而是最低限度的生存战略", "Q & A"],
    "notes": "结尾：回到开头的判断——窗口期只有三年。今天做的每一个决定，定义三年后我们在这个行业的座次。技术不是终点，工具服务于价值。三方投顾的核心价值永远是帮助投资者做出更好的决策。谢谢各位，欢迎提问。"
  }
]


def convert_json_to_page_content(slides_json):
    """将用户JSON格式转换为pipeline所需的page_content格式"""
    page_content = {}

    for slide in slides_json:
        slide_id = slide["id"]
        layout = slide["layout"]
        title = slide["title"]
        bullets = slide.get("bullets", [])
        notes = slide.get("notes", "")

        # 构建 body 文本
        if layout == "cover":
            body = ""
            subtitle = bullets[0] if bullets else ""
        elif layout == "toc":
            body = "\n".join([f"{i+1}. {b}" for i, b in enumerate(bullets)])
            subtitle = ""
        elif layout == "steps":
            body = "\n".join([f"▸ {b}" for b in bullets])
            subtitle = ""
        elif layout == "closing":
            body = "\n".join(bullets)
            subtitle = ""
        else:  # bullets
            body = "\n".join([f"• {b}" for b in bullets])
            subtitle = ""

        content = {
            "title": title,
            "body": body,
            "speaker_notes": notes,
            "layout_type": layout,  # 传递布局类型给生成器
        }

        if subtitle:
            content["subtitle"] = subtitle

        # 传递配图提示词（如有）
        if slide.get("image_prompt"):
            content["image_prompt"] = slide["image_prompt"]

        # 为特定页面添加图表数据
        if slide_id == "slide-5":  # 千亿蓝海
            content["chart_data"] = {
                "type": "line",
                "title": "中国智能投顾市场规模预测（亿元）",
                "data": {
                    "x": ["2024", "2025", "2026", "2027", "2028", "2029", "2030"],
                    "y": [190, 257, 321, 440, 620, 950, 2000],
                    "x_label": "年份",
                    "y_label": "市场规模（亿元）"
                }
            }
        elif slide_id == "slide-7":  # 五力困局
            content["chart_data"] = {
                "type": "bar",
                "title": "波特五力竞争压力评分",
                "data": {
                    "x": ["现有竞争者", "新进入者", "替代品", "买方议价", "供方议价"],
                    "y": [8.5, 6.0, 7.0, 7.5, 5.5],
                    "y_label": "评分（1-10）"
                }
            }
        elif slide_id == "slide-13":  # FAST路线图
            content["chart_data"] = {
                "type": "bar",
                "title": "FAST转型量化目标",
                "data": {
                    "x": ["效率+", "成本-", "合规事故-", "AUM+"],
                    "y": [50, 40, 60, 100],
                    "y_label": "变化幅度(%)"
                }
            }

        page_content[slide_id] = content

    return page_content


def generate_ppt():
    """从JSON内容生成PPT"""

    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'global_config.yaml')
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["execution_mode"] = "auto"

    # 转换JSON为page_content
    page_content = convert_json_to_page_content(SLIDES_JSON)

    print(f"✅ 内容转换完成，共 {len(page_content)} 页")
    for pid, pc in page_content.items():
        layout = pc.get("layout_type", "bullets")
        has_chart = "📊" if pc.get("chart_data") else "  "
        print(f"  {has_chart} {pid}: [{layout}] {pc['title']}")

    # 步骤4：布局设计
    layout_designer = LayoutDesigner(config)
    layout_spec = layout_designer.design_layout(page_content)

    # 步骤5：素材生成
    image_gen = ImageGenerator(config)
    chart_gen = ChartGenerator(config)
    images = image_gen.generate_images(page_content)
    charts = chart_gen.generate_charts(page_content)
    materials = {"images": images, "charts": charts}

    # 步骤6：校验与交付
    consistency_checker = ConsistencyChecker(config)
    compliance_checker = ComplianceChecker(config)

    consistency_ok = consistency_checker.check(page_content, layout_spec)
    compliance_ok = compliance_checker.check(page_content, layout_spec, materials)

    print(f"一致性校验：{'✅ 通过' if consistency_ok else '⚠️ 需修正'}")
    print(f"合规性校验：{'✅ 通过' if compliance_ok else '⚠️ 需修正'}")

    # 生成PPT
    pptx_gen = PPTXGenerator(config)
    output_path = pptx_gen.generate_pptx(page_content, layout_spec, materials)

    # 导出演讲备注
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    notes_path = os.path.join(output_dir, "speaker_notes_三年窗口期.txt")
    with open(notes_path, "w", encoding="utf-8") as f:
        for page_id, content in page_content.items():
            notes = content.get("speaker_notes", "")
            if notes:
                f.write(f"【{page_id}】{content.get('title', '')}\n")
                f.write(f"{notes}\n\n")

    print(f"\n{'='*60}")
    print(f"🎉 PPT生成完成！")
    print(f"{'='*60}")
    print(f"  PPT文件: {output_path}")
    print(f"  演讲备注: {notes_path}")
    print(f"  图表数据: output/charts/")
    print(f"  图片素材: output/images/")

    return output_path


if __name__ == "__main__":
    result = generate_ppt()
    print(f"\n最终输出: {result}")
