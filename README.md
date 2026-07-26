# 高质量科技风PPT生成引擎（high-quality-ppt-skill）

从自然语言需求或结构化大纲，自动生成**咨询公司品质**的专业级可编辑 PPTX。通用技能包，无智能体绑定目录，可被 WorkBuddy / OpenClaw / Hermes 等智能体直接加载。兼容 macOS 与 Windows。

**当前版本：v3.5.2**（版本记录见文末）

## 安装

### 方式 1：WorkBuddy 技能市场（推荐）
打开 WorkBuddy，进入 **技能市场**，搜索「高质量PPT生成引擎」，一键安装即可使用。

### 方式 2：通过 SkillHub 提示词安装
把下面这条提示词直接发给你的 AI，即可自动安装：

> 请根据 https://skillhub.cn/install/skillhub.md ，安装 high-quality-ppt-skill

## 核心能力

- **双模式生成**：JS 直接生成（推荐，视觉最佳）+ Python 6步 Pipeline（完整需求管控）
- **风格样例库 `styles/`（5 套）**：按用户风格要求自动匹配；2 套内置 + 3 套模版提取，支持从自有 PPT 模版提取新风格入库
- **8 种 JS 布局 / 7 种 Python 布局**：cover / agenda / section_divider / data_cards / comparison / three_column / timeline / matrix 等
- **AI 配图体系**：5 种图片角色 × 3 种生成模式（ImageGen 桥接 / 外部 API / 占位）；`auto_image_plan.js` 按大纲+风格自动规划每页配图，prompt 自动嵌入风格色 token 保证色调统一
- **内嵌图标库**：62 关键词 → 57 个 Material Design 线性 SVG 图标，主色可替换
- **原生图表**：PptxGenJS 原生图表 或 matplotlib 四件套（PNG+SVG+CSV+源码）
- **演讲备注**：每页配套话术/停顿点/互动设计
- **约束规则引擎**：金字塔原理、信息密度、对比度（WCAG 2.1 AA）、品牌合规全量校验

## 目录结构

```
high-quality-ppt-skill/
├── SKILL.md                          # 技能定义（智能体加载入口）
├── styles/                           # PPT风格样例库（5套 + 注册表 + 模板）
│   ├── registry.yaml                 # 风格注册表（关键词匹配/回退策略）
│   ├── _template/style.yaml          # 新风格 schema 模板
│   ├── consulting_tech_dark/         # 内置：咨询科技风（暗色，默认回退）
│   ├── green_professional/           # 内置：绿色专业风
│   ├── internet_tech_blue/           # 提取：互联网科技风（亮蓝）
│   ├── business_planning_blue/       # 提取：商业策划风（深蓝）
│   └── navy_corporate/               # 提取：海军蓝商务风（深海军蓝+橙）
├── uploads/                          # 用户PPT模版上传目录（批量风格提取输入）
├── config/                           # global_config.yaml + constraints.yaml
├── core/                             # 6步Pipeline / 内容生成 / 布局设计
├── tools/                            # 7 个工具模块（含 auto_image_plan.js / validate_layout.py）
├── validators/                       # 一致性 + 合规性校验
├── examples/                         # 3个生成示例 + reference_layouts/ 参考设计素材
├── tests/                            # 29个测试用例（E2E+单元）
├── generate_ppt.js                   # JS直接生成参考脚本
├── HarnessConfig.md                  # Harness执行规范（6步+约束引擎）
└── output/                           # 产出目录（PPT/图片/图表/备注）
```

## 快速开始

### 方式1：JS 直接生成（推荐）

在**用户工作目录**执行：

```bash
npm install pptxgenjs react react-dom react-icons sharp js-yaml
node generate_ppt.js   # 按 SKILL.md Step 4-7 编写
```

技能资源（styles/、tools/）通过技能根目录绝对路径引用，不要复制到工作目录。

### 方式2：Python 6步 Pipeline

```bash
pip install -r requirements.txt
python examples/tech_report_example.py
```

### 方式3：JSON → PPT

```bash
python examples/generate_from_json.py
```

## 风格样例库用法

### 按风格要求选择

技能读取 `styles/registry.yaml`，用用户的风格描述匹配各风格 `keywords`，命中最多者胜；无命中回退 `consulting_tech_dark`；平手时优先提取风格。

### 从模版提取新风格

```bash
# 单文件（可指定风格ID与关键词）
python3 tools/style_extractor.py uploads/央企模版.pptx --name soe_blue --keywords "央企,蓝色,商务"

# 批量（uploads/ 整个目录一键入库，幂等跳过已提取文件）
python3 tools/style_extractor.py --batch
```

提取内容：theme 主题色、字体、实际用色频次、页面尺寸、图片密度 → `styles/<风格ID>/style.yaml` + 自动登记 registry。

## 测试

```bash
python -m pytest tests/ -q   # 29 passed
```

## 版本记录

- **v3.5.2** (2026-07-25)：修正 PptxGenJS transparency 参数位置 bug（须写在 `fill` 对象内）；深色背景页改用 hero+overlay 模式，配图可见度显著提升
- **v3.5.1** (2026-07-24)：新增「常见陷阱与预防」章节；新增 `tools/validate_layout.py` 布局校验；新增 `navy_corporate` 风格（第 5 套）
- **v3.5.0** (2026-07-23)：新增 body 主体图角色与 `positionForLayout` 位置解析器；新增 `examples/reference_layouts/` 参考设计素材
- **v3.4.x** (2026-07-23)：新增 `tools/auto_image_plan.js` 自动配图规划与 `assertFits` 画布溢出守卫
- **v3.3.0** (2026-07-23)：真 AI 生成改造——内容骨架 + `set_content_callback` 宿主 AI 回填，不依赖外部 LLM API
- **v3.2.0** (2026-07-22)：技能通用化（适配多智能体加载）；新增 `styles/` 风格样例库与模版批量提取；Python 版扩至 7 种布局
- **v3.1.0** (2026-05-20)：实现 `icon_library.py` 图标库
- **v3.0.0** (2026-05-09)：全面重构——JS 直接生成模式、8 种布局、原生图表、约束规则引擎
- **v1.x–v2.x** (2026-05)：初始版本与视觉规范迭代

## 许可证

MIT
