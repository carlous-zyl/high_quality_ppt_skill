---
name: high-quality-ppt-skill
description: 高质量科技风PPT生成引擎 -
  从自然语言需求或结构化大纲，自动生成专业级可编辑PPTX。支持5套风格样例库(styles/)按风格生成、8种页面布局、AI配图+内嵌图标库(62关键词→57图标)、原生图表、演讲备注同步输出；可将用户上传到 uploads/ 的PPT模版批量提取为风格样例入库复用。触发词：PPT、演示文稿、幻灯片、咨询PPT、科技风PPT、战略汇报、PPT模版、PPT风格
description_zh: 高质量科技风PPT生成
description_en: High-quality tech-style PPT generation
version: 3.5.2
license: MIT
disable: false
agent_created: true
metadata:
  category: productivity
  language: javascript + python
  tech_stack: PptxGenJS + react-icons + sharp + ImageGen
  python_pipeline: python-pptx + matplotlib + YAML + SVG
  layouts: cover / agenda / section_divider / data_cards / comparison /
    three_column / timeline / matrix
  icon_library: 62关键词→57个Material Design线性SVG图标（tools/icon_library.py）
  image_roles: background / illustration / icon_pair / section_icon / logo
  image_modes: placeholder / api / workbuddy(ImageGen桥接)
  reference_ppt: OpenClaw技术扫盲交流.pptx (19页, 121张媒体, 平均6.4张/页)
  harness_config: HarnessConfig.md (6步Pipeline + 约束规则引擎)
---

# 高质量科技风PPT生成引擎

## 概述

从自然语言需求或结构化大纲，自动生成**咨询公司品质**的专业级可编辑PPTX文件。支持两大生成模式：JavaScript直接生成（推荐，视觉效果最佳）和Python 6步Pipeline（完整需求管控）。输出包含AI配图、内嵌图标、原生图表、演讲备注的完整交付包。

## 快速参考

| 项目 | 规格 |
|------|------|
| **页面尺寸** | 16:9 宽屏 (10" × 5.625") |
| **风格样例库** | 5 套：咨询科技风(暗·默认) / 绿色专业风 / 互联网科技风(亮蓝·提取) / 商业策划风(深蓝·提取) / 海军蓝商务风(提取)，详见 `styles/registry.yaml` |
| **英文字体** | Arial |
| **中文字体** | Noto Sans SC (macOS回退 PingFang SC) |
| **图标系统** | react-icons → SVG渲染 → sharp转PNG → base64内嵌；Python侧内置图标库 62关键词→57图标（tools/icon_library.py） |
| **图片模式** | workbuddy(ImageGen桥接) / api(外部API) / placeholder(占位) |
| **图表** | PptxGenJS原生图表(BAR/LINE/PIE) 或 matplotlib→PNG+SVG+CSV+Python源码 |
| **输出路径** | `output/` (PPT + 图片 + 图表 + 备注) |

---

## 生成方式选择

| 方式 | 适用场景 | 技术栈 | 视觉质量 |
|------|----------|--------|----------|
| **方式1: JS直接生成（推荐）** | 有明确大纲/内容，追求最佳视觉效果 | PptxGenJS + react-icons + ImageGen | ⭐⭐⭐⭐⭐ |
| **方式2: Python 6步Pipeline** | 完整需求管控，人工分步确认 | python-pptx + matplotlib + YAML | ⭐⭐⭐ |
| **方式3: JSON→PPT** | 已有结构化JSON数据 | python-pptx 7种布局 | ⭐⭐⭐ |

### 🎯 生成路径决策（重要，先读）

**内容由谁生成，是本技能"真 AI 生成"的关键。请遵循以下决策：**

- **默认走方式1（JS 直接生成）= 开箱即用的真 AI 生成**：单页内容（标题/论据/数据/备注）由**你（宿主 AI）结合真实主题、受众、行业现状直接撰写**，再写入 generate_ppt.js。这是主推路径，无需任何额外配置，内容随主题真实变化。
- **方式2/3（Python Pipeline）= 需求管控 / 骨架方案**：适合需要 6 步分阶段人工确认、或已有结构化数据的场景。其 `core/content_generator.py` **不内置任何真实内容**——每页产出带 `[占位·请替换]` 水印的结构骨架，由宿主 AI 通过 `set_content_callback` 回填真实内容：
  - 注入回调 → 内容由宿主 AI 真实生成（`generation_mode=host_ai`）
  - 未注入 → 保留占位骨架（`generation_mode=template_fallback`），交付时会告警提示，**绝不用编造的假数据冒充真实**
- **本技能只用宿主 AI，不依赖任何外部 LLM API**（无 api_key/endpoint/模型配置），用户零感知。宿主环境有什么 AI 就用什么 AI。

> content_callback 签名：`fn(page_type, theme, audience, title) -> {"body": ..., "speaker_notes": ...}`。详见 `core/content_generator.py`。

---

## 方式1: JS直接生成 — 完整工作流（推荐）

### Step 0: 环境准备

在**用户工作目录**（即当前对话的项目目录，产出落在该目录 `output/`）执行：

```bash
cd <用户工作目录>
npm install pptxgenjs react react-dom react-icons sharp js-yaml
```

**路径约定**：技能资源（`styles/` 风格库、`tools/`、`examples/`）一律通过**技能根目录绝对路径**引用（WorkBuddy 下为 `~/.workbuddy/skills/high-quality-ppt-skill/`，其他智能体按实际部署路径），不要把技能源码复制到用户工作目录。`generate_ppt.js` 生成脚本写在用户工作目录。

### Step 1: 需求解析与大纲设计

基于用户提供的需求（自然语言即可），设计PPT大纲：

**必采参数**（对齐 HarnessConfig must_collect_params）：
1. 核心主题与汇报目标
2. 目标受众（技术背景/职级/核心诉求）
3. 汇报时长与总页数范围
4. 交付格式（.pptx）
5. 品牌VI/风格偏好（默认：咨询科技风暗色）
6. 内容禁忌与合规要求

**大纲设计原则**：
- 遵循金字塔原理：结论先行，以上统下，归类分组，逻辑递进
- 推荐结构：封面 → 议程 → **Part1(Why)** → 分隔页 → 核心论据页(3-6页) → **Part2(How)** → 分隔页 → 解决方案页(3-6页) → 关键要素 → 结尾
- 每3-4页设置1个叙事钩子（核心数据/对比/互动问题）
- 每页仅1个核心观点，标题为结论式表达

### Step 2: 选择视觉风格（风格样例库驱动）

风格样例库位于 `styles/`，**按风格分目录维护**，每个风格一个子目录，内含 `style.yaml`（完整色板/字体/布局/配图规范）。**不要硬编码配色**，先从样例库选风格。

**选择流程**：

1. 读取 `styles/registry.yaml`，用用户输入的风格要求（关键词/品牌VI描述/行业偏好）匹配 `keywords` 命中数最多的风格
2. 加载对应 `styles/<style_name>/style.yaml`，取其 `palette` / `fonts` / `layout` 规范用于生成
3. 无命中时回退 `registry.yaml` 的 `selection.fallback`（默认 `consulting_tech_dark`）
4. **用户上传了参考PPT模版**时，先提取入库再使用：
   ```bash
   # 单文件精细提取（可指定风格ID与关键词）
   python3 tools/style_extractor.py <用户模版.pptx> --name <style_name> --keywords "关键词1,关键词2"
   # 批量提取：用户把模版放入 uploads/ 后一键入库
   python3 tools/style_extractor.py --batch
   # 产出 styles/<style_name>/style.yaml，并自动登记到 styles/registry.yaml
   ```

#### 风格样例库总览（5 个风格）

| 风格ID | 显示名 | 类型 | 主色 | 强调 | 深底 | 字体 | 来源 |
|---|---|---|---|---|---|---|---|
| `consulting_tech_dark` | 咨询科技风（暗色） | 内置·默认回退 | `0D9488` | `F59E0B` | `0F172A` | Arial / Noto Sans SC | 手工沉淀 |
| `green_professional` | 绿色专业风 | 内置 | `047857` | `F97316` | `1E293B` | Arial / Noto Sans SC | 手工沉淀 |
| `internet_tech_blue` | 互联网科技风（亮蓝） | 模版提取 | `5B9BD5` | `FFC000` | `000000` | Arial / 微软雅黑 | 参考模版 |
| `business_planning_blue` | 蓝色商业策划风（深蓝） | 模版提取 | `4472C4` | `FFC000` | `000000` | Calibri Light / Noto Sans SC | 参考模版 |
| `navy_corporate` | 海军蓝商务风（深海军蓝+橙） | 模版提取 | `0A1A2F` | `F39C12` | `0A1A2F` | Arial / Noto Sans SC | 参考模版 |

> 提取风格的 `background_dark` 来自 theme XML 的 dk1，常为 `000000`（纯黑）。**生成时建议把封面/分隔页深底微调为品牌深蓝**（如 `0A1A2F` 海军蓝），比纯黑更有质感——这是 per-generation override，不入 style.yaml。

#### 内置风格A: 咨询科技风 `styles/consulting_tech_dark/`（默认推荐）

| 用途 | 色值 | 变量名 |
|------|------|--------|
| 深色背景(封面/分隔/结尾) | `0F172A` | `C.dark` |
| 深色卡片 | `1E293B` | `C.darkCard` |
| 主色(青绿) | `0D9488` | `C.teal` |
| 主色亮 | `14B8A6` | `C.tealLight` |
| 强调亮 | `2DD4BF` | `C.tealBright` |
| 高亮(琥珀) | `F59E0B` | `C.amber` |
| 风险/警告 | `EF4444` | `C.red` |
| 正面/成功 | `10B981` | `C.green` |
| 信息蓝 | `3B82F6` | `C.blue` |
| 紫色标签 | `8B5CF6` | `C.purple` |
| 浅色背景(内容页) | `F8FAFC` | `C.offWhite` |
| 卡片背景 | `F1F5F9` | `C.slate100` |
| 正文色 | `334155` | `C.slate700` |
| 副文本 | `64748B` | `C.slate500` |
| 暗文本 | `94A3B8` | `C.slate400` |

#### 内置风格B: 绿色专业风 `styles/green_professional/`

| 用途 | 色值 |
|------|------|
| 深色背景 | `1E293B` |
| 主色(深绿) | `047857` |
| 主色中绿 | `059669` |
| 主色亮绿 | `10B981` |
| 强调浅绿 | `6EE7B7` |
| 橙色徽章 | `F97316` |
| 橙色浅底 | `FFF7ED` |
| 绿色浅底 | `E6F9F0` |

#### 用户提取风格C: 互联网科技风 `styles/internet_tech_blue/`

提取自参考模版 `互联网科技.pptx`（28 页，平均 3.8 张图/页，图文密集型）。

| 用途 | 色值 | 备注 |
|---|---|---|
| 主色(亮蓝) | `5B9BD5` | theme accent1 |
| 主色亮(青蓝) | `18D2FC` | 实际填充色 top1 |
| 主色强调(青绿) | `00A4A4` | 实际填充色 top2 |
| 强调(黄) | `FFC000` | theme accent4 |
| 辅助(亮蓝) | `0293F2` | 实际填充色 top3 |
| 深底 | `000000` | theme dk1，建议生成时改 `0A1A2F` |
| 浅底 / 卡片 | `FFFFFF` / `E7E6E6` | |
| 文字主 / 副 | `334155` / `64748B` | |
| 字体 | Arial / 微软雅黑 | |

**适用**：互联网产品发布、科技产品介绍、亮色调品牌汇报。触发关键词：互联网 / 科技 / 亮蓝 / 科技蓝。

#### 用户提取风格D: 蓝色商业策划风 `styles/business_planning_blue/`

提取自参考模版 `蓝色商业策划书.pptx`（30 页，平均 0.5 张图/页，文字密集型）。

| 用途 | 色值 | 备注 |
|---|---|---|
| 主色(深蓝) | `4472C4` | theme accent1 |
| 主色亮(中蓝) | `5B9BD5` | theme accent2 |
| 强调(黄) | `FFC000` | theme accent4 |
| 辅助(橙) | `ED7D31` | theme accent3 |
| 深底 | `000000` | theme dk1，建议生成时改 `0F1B3D` |
| 浅底 / 卡片 | `FFFFFF` / `E7E6E6` | |
| 文字主 / 副 | `334155` / `64748B` | |
| 字体 | Calibri Light / Noto Sans SC | |

**适用**：商业策划书、BP 路演、商务汇报、深蓝商务风。触发关键词：商业 / 策划 / 商业策划 / 蓝色 / 深蓝 / 商务。

### Step 3: 8种页面布局类型

| 布局类型 | 视觉特征 | 适用场景 |
|----------|----------|----------|
| **cover** | 深色全屏背景图(70%透明+暗色覆盖层25%) + 大标题 + 底部指标卡片(3个) | 封面页 |
| **agenda** | 浅色背景 + 左右双栏 + 编号+文字列表 | 议程/目录页 |
| **section_divider** | 深色全屏背景图(75%透明+暗色覆盖层20%) + PART编号 + 大标题 | 章节分隔页 |
| **data_cards** | 浅色背景 + 页标题 + 多个数据卡片(图标+数值+说明) | 核心判断/证据页 |
| **comparison** | 浅色背景 + 左右对比表(传统 vs 新范式) + 维度标签 | 对比分析页 |
| **three_column** | 浅色背景 + 3列独立卡片 + 顶部图标 + 右上角插图 | 三方对比/分类页 |
| **timeline** | 浅色背景 + 水平时间线/步骤 + 标签卡片 + 右侧插图 | 政策/路线/流程页 |
| **matrix** | 浅色/深色 + 2×2四象限 + 标签pill + 可选图表 | SWOT/BCG/Agent矩阵页 |

### Step 4: 编写 generate_ppt.js

基于大纲逐页编写JS生成脚本，核心结构：

```javascript
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const yaml = require("js-yaml");
const fs = require("fs");
const path = require("path");

// ===== Icon System =====
async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ===== Style Loading（风格样例库驱动，禁止硬编码配色）=====
// 技能根目录：WorkBuddy 下为 ~/.workbuddy/skills/high-quality-ppt-skill，按实际部署替换
const SKILL_DIR = path.join(process.env.HOME, ".workbuddy", "skills", "high-quality-ppt-skill");
const STYLE_NAME = "consulting_tech_dark"; // ← 由 Step 2 风格选择结果填入

function loadPalette(skillDir, styleName) {
  // 内置回退 = styles/consulting_tech_dark/style.yaml
  const fallback = {
    dark: "0F172A", darkCard: "1E293B", teal: "0D9488", tealLight: "14B8A6",
    tealBright: "2DD4BF", amber: "F59E0B", red: "EF4444", green: "10B981",
    blue: "3B82F6", purple: "8B5CF6", white: "FFFFFF", offWhite: "F8FAFC",
    slate100: "F1F5F9", slate400: "94A3B8", slate500: "64748B",
    slate700: "334155", slate800: "1E293B", slate900: "0F172A",
  };
  try {
    const stylePath = path.join(skillDir, "styles", styleName, "style.yaml");
    const style = yaml.load(fs.readFileSync(stylePath, "utf8"));
    const p = style.palette || {};
    return {
      dark: p.background_dark || fallback.dark,
      darkCard: p.card_dark || fallback.darkCard,
      teal: p.primary || fallback.teal,
      tealLight: p.primary_light || fallback.tealLight,
      tealBright: p.primary_bright || fallback.tealBright,
      amber: p.accent || fallback.amber,
      blue: p.accent2 || fallback.blue,
      green: p.success || fallback.green,
      red: p.warning || fallback.red,
      purple: p.purple || fallback.purple,
      white: "FFFFFF",
      offWhite: p.background_light || fallback.offWhite,
      slate100: p.card_bg_light || fallback.slate100,
      slate400: p.text_on_dark_sub || fallback.slate400,
      slate500: p.text_sub || fallback.slate500,
      slate700: p.text_main || fallback.slate700,
      slate800: p.card_dark || fallback.slate800,
      slate900: p.background_dark || fallback.slate900,
    };
  } catch (e) {
    console.warn(`[style] 加载 ${styleName} 失败，回退内置咨询科技风: ${e.message}`);
    return fallback;
  }
}
const C = loadPalette(SKILL_DIR, STYLE_NAME);

// ===== Helpers =====
const makeShadow = () => ({
  type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.1
});
function addSlideNumber(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 8.8, y: 5.25, w: 1.0, h: 0.3,
    fontSize: 9, color: C.slate400, align: "right", fontFace: "Arial"
  });
}
function addPageTitle(slide, title, subtitle) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.4, w: 0.06, h: 0.5, fill: { color: C.teal }
  });
  slide.addText(title, {
    x: 0.7, y: 0.35, w: 8.5, h: 0.55,
    fontSize: 24, fontFace: "Arial", bold: true, color: C.slate800
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.7, y: 0.85, w: 8.5, h: 0.35,
      fontSize: 12, fontFace: "Arial", color: C.slate500
    });
  }
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 9.0, h: 0.02, fill: { color: C.tealLight }, transparency: 60
  });
}

// ===== Image Loading =====
const IMG_DIR = path.join(__dirname, "output", "images");
const IMAGES = {
  cover: path.join(IMG_DIR, "cover_image.png"),
  section1: path.join(IMG_DIR, "section1_image.png"),
  // ... 按需添加
};
const availableImages = {};
for (const [key, p] of Object.entries(IMAGES)) {
  if (fs.existsSync(p)) { availableImages[key] = p; }
}

// ===== Main =====
let pres;
const TOTAL_SLIDES = 17; // 按大纲调整

async function main() {
  pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Author Name";
  pres.title = "PPT Title";

  // Load & pre-generate icons
  const fa = require("react-icons/fa");
  const icons = {};
  const iconDefs = [
    ["rocket", fa.FaRocket, C.tealBright],
    ["chart", fa.FaChartLine, C.tealLight],
    // ... 按需添加（react-icons 全库可选；Python侧另有62关键词→57图标映射可参考）
  ];
  for (const [name, Component, color] of iconDefs) {
    icons[name] = await iconToBase64Png(Component, `#${color}`, 256);
  }

  // ===== SLIDE N: 各页定义 =====
  // ... 逐页定义（见下方各布局模板）

  // ===== Save =====
  const outputPath = path.join(__dirname, "output", "PPT标题.pptx");
  await pres.writeFile({ fileName: outputPath });
  console.log(`PPT已生成: ${outputPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
```

### Step 5: 各布局模板代码片段

#### 封面页 (cover)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.dark };
// AI背景图（hero image + dark overlay：图90%显示 + 遮罩55%覆盖，图片可见度~40%）
if (availableImages.cover) {
  slide.addImage({ path: availableImages.cover, x: 0, y: 0, w: 10, h: 5.625,
    sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.dark, transparency: 45 } });
}
// 顶部装饰线
slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
// 标签
slide.addText("STRATEGIC REPORT", { x: 0.8, y: 0.8, w: 8.4, h: 0.4,
  fontSize: 11, fontFace: "Arial", color: C.tealBright, letterSpacing: 4 });
// 大标题
slide.addText("主标题", { x: 0.8, y: 1.5, w: 8.4, h: 1.0,
  fontSize: 36, fontFace: "Arial", bold: true, color: C.white });
// 副标题
slide.addText("副标题描述", { x: 0.8, y: 2.5, w: 8.4, h: 0.5,
  fontSize: 16, fontFace: "Arial", color: C.slate400 });
// 底部指标卡片 (3个)
const metrics = [
  { value: "2000亿", label: "市场规模", color: C.teal },
  { value: "25%+", label: "年增长率", color: C.amber },
  { value: "~3年", label: "窗口期", color: C.red },
];
metrics.forEach((m, i) => {
  const x = 0.8 + i * 3.0;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.8, w: 2.6, h: 1.2,
    fill: { color: C.darkCard }, rectRadius: 0.1, shadow: makeShadow() });
  slide.addText(m.value, { x, y: 3.95, w: 2.6, h: 0.55,
    fontSize: 22, fontFace: "Arial", bold: true, color: m.color, align: "center" });
  slide.addText(m.label, { x, y: 4.5, w: 2.6, h: 0.3,
    fontSize: 11, fontFace: "Arial", color: C.slate400, align: "center" });
});
```

#### 章节分隔页 (section_divider)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.dark };
if (availableImages.section1) {
  slide.addImage({ path: availableImages.section1, x: 0, y: 0, w: 10, h: 5.625,
    sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.dark, transparency: 45 } });
}
slide.addText("PART 1", { x: 0.8, y: 1.5, w: 8.4, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: C.tealBright, letterSpacing: 6 });
slide.addText("章节标题", { x: 0.8, y: 2.2, w: 8.4, h: 1.0,
  fontSize: 40, fontFace: "Arial", bold: true, color: C.white });
slide.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 3.4, w: 2.0, h: 0.04, fill: { color: C.teal } });
slide.addText("章节描述", { x: 0.8, y: 3.7, w: 8.4, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: C.slate400 });
```

#### 议程页 (agenda)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "议程", "AGENDA");
// 左右双栏：每栏2-3个编号条目
const agendaLeft = [
  { no: "01", title: "为什么必须转型", desc: "市场 · 竞争 · 监管 三重压力" },
  { no: "02", title: "转型的本质判断", desc: "从人力密集到人机协同" },
];
const agendaRight = [
  { no: "03", title: "数智化转型方案", desc: "三大核心能力 + 落地路径" },
  { no: "04", title: "路线图与保障", desc: "24个月三阶段推进" },
];
const renderAgendaCol = (items, x) => {
  items.forEach((it, i) => {
    const y = 1.5 + i * 1.6;
    // 编号
    slide.addText(it.no, { x, y, w: 0.7, h: 0.55,
      fontSize: 24, fontFace: "Arial", bold: true, color: C.teal });
    // 编号右侧竖线
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.75, y: y + 0.05, w: 0.025, h: 0.75, fill: { color: C.tealLight } });
    // 条目文字
    slide.addText(it.title, { x: x + 0.95, y, w: 3.5, h: 0.45,
      fontSize: 16, fontFace: "Arial", bold: true, color: C.slate800 });
    slide.addText(it.desc, { x: x + 0.95, y: y + 0.45, w: 3.5, h: 0.35,
      fontSize: 11, fontFace: "Arial", color: C.slate500 });
  });
};
renderAgendaCol(agendaLeft, 0.6);
renderAgendaCol(agendaRight, 5.2);
```

#### 数据卡片页 (data_cards)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "核心判断：三年窗口期", "不转型即出局");
const cards = [
  { icon: "chart", value: "2000亿", desc: "2030年智能投顾市场", color: C.teal },
  { icon: "shield", value: "6.6/10", desc: "竞争压力指数", color: C.red },
  { icon: "gavel", value: "326张", desc: "2025年监管罚单", color: C.amber },
  { icon: "rocket", value: "~3年", desc: "技术窗口期", color: C.purple },
  { icon: "exclamation", value: "80%+", desc: "荐股费收入占比", color: C.red },
];
cards.forEach((card, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.5 + col * 3.1, y = 1.5 + row * 2.0;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.8, h: 1.7,
    fill: { color: C.white }, rectRadius: 0.1, shadow: makeShadow() });
  slide.addImage({ data: icons[card.icon], x: x+0.3, y: y+0.2, w: 0.35, h: 0.35 });
  slide.addText(card.value, { x: x+0.3, y: y+0.65, w: 2.2, h: 0.45,
    fontSize: 22, fontFace: "Arial", bold: true, color: card.color });
  slide.addText(card.desc, { x: x+0.3, y: y+1.15, w: 2.2, h: 0.35,
    fontSize: 11, fontFace: "Arial", color: C.slate500 });
});
```

#### 对比分析页 (comparison)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "传统模式 vs 智能新范式", "五大维度对比");
// 表头：维度 / 传统 / 新范式
const headers = [
  { text: "对比维度", x: 0.5, w: 2.0, bg: C.slate700 },
  { text: "传统模式", x: 2.6, w: 3.3, bg: C.slate400 },
  { text: "智能新范式", x: 6.0, w: 3.5, bg: C.teal },
];
headers.forEach(h => {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: h.x, y: 1.4, w: h.w, h: 0.5,
    fill: { color: h.bg }, rectRadius: 0.06 });
  slide.addText(h.text, { x: h.x, y: 1.45, w: h.w, h: 0.4,
    fontSize: 13, fontFace: "Arial", bold: true, color: C.white, align: "center" });
});
// 维度行（斑马纹）
const dims = [
  { dim: "作业方式", old: "人工荐股", neo: "AI辅助决策" },
  { dim: "服务半径", old: "有限营业部", neo: "规模化个性服务" },
  { dim: "核心资产", old: "明星投顾", neo: "人机协同体系" },
  { dim: "合规管控", old: "事后抽查", neo: "全流程留痕" },
];
dims.forEach((d, i) => {
  const y = 2.0 + i * 0.62;
  if (i % 2 === 0) {
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 9.0, h: 0.62, fill: { color: C.white } });
  }
  slide.addText(d.dim, { x: 0.7, y: y + 0.13, w: 1.8, h: 0.35,
    fontSize: 12, fontFace: "Arial", bold: true, color: C.slate700 });
  slide.addText(d.old, { x: 2.8, y: y + 0.13, w: 3.0, h: 0.35,
    fontSize: 12, fontFace: "Arial", color: C.slate500 });
  slide.addText(d.neo, { x: 6.2, y: y + 0.13, w: 3.1, h: 0.35,
    fontSize: 12, fontFace: "Arial", bold: true, color: C.teal });
});
```

#### 三列卡片页 (three_column)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "三大核心能力", "能力体系拆解");
// 右上角插图（可选）
if (availableImages.corner) {
  slide.addImage({ path: availableImages.corner, x: 8.3, y: 0.3, w: 1.5, h: 1.0, transparency: 30 });
}
const cols = [
  { icon: "brain",  title: "智能投研", desc: "研究生产效率革命",
    points: ["研报自动摘要", "产业链图谱", "另类数据融合"] },
  { icon: "agent",  title: "投顾智能体", desc: "7×24 在线服务",
    points: ["组合诊断", "调仓建议", "合规话术生成"] },
  { icon: "shield", title: "合规风控", desc: "全流程留痕可溯",
    points: ["实时话术质检", "适当性匹配", "风险预警"] },
];
cols.forEach((col, i) => {
  const x = 0.5 + i * 3.1;
  // 卡片 + 顶部色条
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.9, h: 3.6,
    fill: { color: C.white }, rectRadius: 0.1, shadow: makeShadow() });
  slide.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 2.9, h: 0.08, fill: { color: C.teal } });
  // 顶部图标（居中）
  slide.addImage({ data: icons[col.icon], x: x + 1.2, y: 1.8, w: 0.5, h: 0.5 });
  // 标题 + 描述 + 要点
  slide.addText(col.title, { x, y: 2.45, w: 2.9, h: 0.4,
    fontSize: 16, fontFace: "Arial", bold: true, color: C.slate800, align: "center" });
  slide.addText(col.desc, { x: x + 0.25, y: 2.9, w: 2.4, h: 0.4,
    fontSize: 11, fontFace: "Arial", color: C.slate500, align: "center" });
  col.points.forEach((pt, j) => {
    slide.addText(pt, { x: x + 0.3, y: 3.45 + j * 0.38, w: 2.3, h: 0.32,
      fontSize: 10, fontFace: "Arial", color: C.slate700, bullet: { code: "2022" } });
  });
});
```

#### 时间线页 (timeline)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "24个月转型路线图", "三阶段推进");
// 水平主轴线
slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 3.1, w: 8.0, h: 0.04, fill: { color: C.tealLight } });
const phases = [
  { date: "0-6月",   label: "Foundation", desc: "数据底座 + 系统整合", color: C.teal },
  { date: "6-15月",  label: "Agent",      desc: "智能体上岗试点",     color: C.amber },
  { date: "15-24月", label: "Transcend",  desc: "全面人机协同",       color: C.purple },
];
phases.forEach((p, i) => {
  const x = 0.7 + i * 2.7;
  // 轴上节点
  slide.addShape(pres.shapes.OVAL, { x: x + 0.95, y: 2.95, w: 0.35, h: 0.35, fill: { color: p.color } });
  // 上方时间段
  slide.addText(p.date, { x, y: 2.35, w: 2.3, h: 0.35,
    fontSize: 12, fontFace: "Arial", bold: true, color: p.color, align: "center" });
  // 下方标签卡片
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.55, w: 2.3, h: 1.3,
    fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow(),
    line: { color: p.color, width: 1.5 } });
  slide.addText(p.label, { x, y: 3.7, w: 2.3, h: 0.35,
    fontSize: 14, fontFace: "Arial", bold: true, color: p.color, align: "center" });
  slide.addText(p.desc, { x: x + 0.15, y: 4.12, w: 2.0, h: 0.6,
    fontSize: 10, fontFace: "Arial", color: C.slate500, align: "center" });
});
// 右下角插图（可选）
if (availableImages.roadmap) {
  slide.addImage({ path: availableImages.roadmap, x: 8.8, y: 3.6, w: 1.1, h: 1.3, transparency: 35 });
}
```

#### 2×2矩阵页 (matrix)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "SWOT战略诊断", "四象限分析框架");
const quadrants = [
  { label: "S 优势", items: ["..."], color: C.green, x: 0.5, y: 1.5 },
  { label: "W 劣势", items: ["..."], color: C.red, x: 5.0, y: 1.5 },
  { label: "O 机会", items: ["..."], color: C.teal, x: 0.5, y: 3.4 },
  { label: "T 威胁", items: ["..."], color: C.amber, x: 5.0, y: 3.4 },
];
quadrants.forEach(q => {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: q.x, y: q.y, w: 4.3, h: 1.7,
    fill: { color: C.white }, rectRadius: 0.1, shadow: makeShadow(),
    line: { color: q.color, width: 1.5 } });
  slide.addText(q.label, { x: q.x+0.3, y: q.y+0.15, w: 2.0, h: 0.35,
    fontSize: 14, fontFace: "Arial", bold: true, color: q.color });
  q.items.forEach((item, j) => {
    slide.addText(item, { x: q.x+0.3, y: q.y+0.55+j*0.28, w: 3.8, h: 0.25,
      fontSize: 11, fontFace: "Arial", color: C.slate700, bullet: { code: "2022" } });
  });
});
```

#### 原生图表 (PptxGenJS Chart)

```javascript
const slide = pres.addSlide();
slide.background = { color: C.offWhite };
addPageTitle(slide, "市场规模预测", "2024-2030年智能投顾市场");
slide.addChart(pres.charts.BAR, [
  { name: "市场规模(亿)", labels: ["2024","2025","2026","2027","2028","2029","2030"],
    values: [190,257,321,401,501,626,781] }
], { x: 0.5, y: 1.4, w: 9.0, h: 3.8,
  showValue: true, valueFontSize: 9, valueFontFace: "Arial",
  chartColors: [C.teal], catAxisLabelColor: C.slate500,
  valAxisLabelColor: C.slate500, catAxisLabelFontSize: 10,
  valAxisLabelFontSize: 9, legendPos: "none" });
```

### Step 6: AI配图生成

使用 ImageGen 工具为PPT生成配图，**两种图片嵌入模式**：

#### 模式1: 全屏背景图（封面/分隔页/结尾页）

```
Prompt格式: "[主题场景描述], abstract digital art, [配色关键词] tones, futuristic, professional, high resolution, 16:9 aspect ratio, no text, no watermark"
透明度处理: 图片transparency:10%（90%显示）+ 深色矩形覆盖层transparency:45%（55%覆盖）
            ※ hero image + dark overlay 模式，图片可见度~40%，文字清晰
            ※ transparency 必须写在 fill 对象内：fill: { color: X, transparency: 45 }
```

#### 模式2: 角落插图（内容页）

```
Prompt格式: "[主题场景描述], minimalist digital illustration, clean composition, [配色] accent, white background, professional, no text"
透明度处理: 图片transparency:25-40%, 放置在页面角落不遮挡文字
```

**7张典型配图场景**：

| 页面 | 图片角色 | Prompt关键词 | 嵌入方式 |
|------|----------|-------------|----------|
| 封面 | 全屏背景 | "Futuristic digital finance transformation" | 图transparency:10% + 暗色覆盖45% |
| Part1分隔 | 全屏背景 | "Abstract industry disruption visualization" | 图transparency:10% + 暗色覆盖45% |
| 竞争分析 | 右上角插图 | "Three competitive forces collision" | transparency:30%, 右上 |
| 监管政策 | 右上角插图 | "Regulatory storm concept" | transparency:25%, 右上 |
| 市场机遇 | 右下角插图 | "Vast blue ocean market opportunity" | transparency:40%, 右下 |
| Part2分隔 | 全屏背景 | "Futuristic AI robot brain with neural connections" | 图transparency:10% + 暗色覆盖45% |
| 路线图 | 右下角插图 | "Strategic roadmap pathway forward" | transparency:35%, 右下 |

#### 自动化配图（image_auto）— 推荐

**问题**：上面 7 张表是手写清单，扩展性差。JS 主路径上每张图的 prompt、角色、位置都靠人写，三大痛点——①无自动规划②prompt 不带风格色③策略固定。

**解法**：`tools/auto_image_plan.js` —— 接收大纲 + style.yaml，按主题自动规划每页配图，输出 JSON 清单。

**3 个 level**：

| level | 适用范围 | 出图数 | 10 页示例 |
|---|---|---|---|
| `minimal` | 仅快出片 | 封面+结尾 ≈ 2 | 2 |
| `standard`（推荐） | 主题页配图 | 封面+分隔+N 主题角落 ≈ 5-7 | 6 |
| `rich` | 全配图 | 封面+分隔+每页插图 ≈ 8-12 | 10 |

**JS 调用**：

```javascript
const { planImages, estimateCredits } = require("./tools/auto_image_plan");
const slides = [
  { idx: 1, type: "cover", title: "封面", topic: "AI 驱动的产业升级" },
  { idx: 2, type: "content", title: "议程" },
  { idx: 3, type: "divider", title: "PART 1", topic: "市场变革" },
  { idx: 4, type: "content", title: "AI 趋势", body: "大模型重塑...", topic: "AI 技术" },
  { idx: 9, type: "closing", title: "结尾", topic: "未来已来" },
];
const stylePath = path.join(SKILL_DIR, "styles", "consulting_tech_dark", "style.yaml");
const plan = planImages(slides, stylePath, { level: "standard" });
console.log(`规划 ${plan.length} 张图，约 ${estimateCredits(plan)} credits`);
// plan = [{idx, role, output, prompt, size, transparency, position}, ...]
// prompt 已嵌入风格色 token: "...color palette dominated by #0D9488 and #F59E0B..."
// AI 助手按 plan 逐个调 ImageGen, 产物写到 output, 再跑 PPT 生成
```

**CLI 调试**：

```bash
echo '[{"idx":1,"type":"cover","title":"封面","topic":"AI驱动"}]' | \
  node tools/auto_image_plan.js styles/consulting_tech_dark/style.yaml standard
```

**触发插图的关键词**（`standard` level 自动判断是否给内容页配图）：
`AI/转型/数字化/智能/数据/生成/设计/架构/流程/策略/风险/市场/团队/协作/创新/分析/技术/产品/用户/增长/竞争/运营/组织/升级` —— 任一出现在 title/body/topic 即配图。

**风格色 token 注入**：
prompt 模板自动从 style.yaml 读取 `palette.primary / accent / background_dark`，嵌入 prompt 尾部，确保全稿图片色调统一（避免「封面青绿、分隔橙红」的割裂感）。

**布局感知跳过规则**：
自动配图不再只看主题关键词，还看**页面布局密度**——当页面已有丰富视觉元素时，角落插图反而破坏统一。

| 布局 | 卡片数 | 角落插图？ | 理由 |
|------|--------|-----------|------|
| cover/divider/closing | — | 背景（不算角落） | 全屏角色 |
| **data_cards** | **≥4** | **❌ 跳过** | 卡片已视觉饱和, 插图破坏「6个版本统一设计」 |
| data_cards | <4 | ✅ | 留白多, 插图填充 |
| comparison/timeline/agenda/three_column | 任意 | ✅ | 线性/表格结构, 插图不冲突 |
| 通用 content | 触发关键词 | ✅ | 原有逻辑 |
| 任意 | `skipCorner: true` | ❌ | 显式强制跳过 |

slides_meta.json 加 `layout` + `cardCount` 字段触发该规则。plan 输出 `skipped[]` 数组会说明每个跳过项的 `reason / layout / cardCount`，方便复盘。

**例外：天然空白带可补横条叙事图**：
`data_cards≥4 跳过角落插图`针对的是**装饰性角落图**。若页面布局本身有 ≥0.7" 的天然空白带（如 4 横卡与底部 banner 之间的悬空区），可加**横条叙事图**（w:9, h:0.8, cover 裁剪）填补——它补的是排版结构而非装饰，且主题必须呼应页面核心观点。同理，全宽表格可压缩至 6.5" + 右侧 2.35" 竖版主题图（左文右图），比单纯表格更丰满。

**三级降级 prompt（robustPrompts）**：
ImageGen 对 prompt 中的 `#XXXXXX` 十六进制色**偶发解析失败**（报"neither base64 nor URL"），需色名回退才能成功。auto_image_plan 为每个 plan 项内嵌 3 档降级：

```javascript
const { robustPrompts } = require("./tools/auto_image_plan");
const prompts = robustPrompts(topic, "background", color);
// 返回 [hex版, 色名版, 极简版]
// [0] "...#0D9488 and #F59E0B..."     ← 首选
// [1] "...teal and amber..."           ← 降级
// [2] "<topic>, minimalist, no text"   ← 极简
// AI 助手依次重试, 全失败则跳过该项
```

调用方式：plan item 字段 `fallback_prompts` 直接含 3 档数组，无需自行构造。

#### body 主体图：按布局驱动的大图配图

`body` 角色用于「左 40% 主体图 + 右 60% 文字」这类设计师式大图排版，区别于装饰性角落插图（1.5"×1" 白底极简图，位置固定右上角）。三个要点：

1. **body 角色 prompt 模板**（不再是"minimalist illustration on white"）：
   ```
   "<topic>, professional high-quality photograph or detailed digital illustration,
    vivid colors, well-composed, 16:9, no text, no watermark"
   ```
   由模型根据 topic 自选（"拥挤招聘会"→照片；"棋盘战略"→插画；"种子成长"→叙事图）。

2. **位置由 layout 决定（非硬编码）**：
   `positionForLayout(imagePosition)` 解析器，6 种位置类型：

   | imagePosition | 坐标 (x, y, w, h) | 用途 |
   |---|---|---|
   | `body_left` | (0.5, 1.55, 4.0, 3.0) | **左 40% 主体图 + 右 60% 文字**（参考设计主流） |
   | `body_right` | (5.5, 1.55, 4.0, 3.0) | 右 40% 主体图 + 左 60% 文字 |
   | `body_top` | (0.5, 1.4, 9.0, 2.0) | 顶部 9" 通栏 |
   | `body_top_in_card` | (0.5, 1.5, 4.2, 1.8) | 卡片内顶部 |
   | `corner` | (8.3, 0.3, 1.5, 1.0) | 右上角（向后兼容） |
   | `background` | (0, 0, 10, 5.625) | 全屏背景 |

3. **AI 决策字段**（slides_meta.json 加 3 个）：

   ```json
   {
     "idx": 4,
     "type": "content",
     "title": "传统PPT制作：高投入、低产出",
     "body": true,                       // AI 标记：需要主体图
     "imagePosition": "body_left",       // AI 决策：左图右文
     "imageStyle": "photorealistic",     // 可选提示
     "caption": "混乱的工作场景",         // 图片下方说明
     "topic": "frustrated office worker..."
   }
   ```

4. **决策逻辑**：
   - `body=true` → body 角色 + `positionForLayout(imagePosition)` 解析位置
   - `body!=true` → 旧逻辑（data_cards≥4 跳过 / 触发词配 corner）

5. **参考设计素材**：4 张高质量参考截图存于 `examples/reference_layouts/`，可作为新场景设计的视觉参考。

### Step 7: 运行生成

在**用户工作目录**执行：

```bash
cd <用户工作目录>
node generate_ppt.js
# 输出: <用户工作目录>/output/PPT标题.pptx
```

### Step 8: 质量校验

**必检项**（对齐 HarnessConfig 约束规则引擎）：

- [ ] 金字塔原理：每页1个核心观点，结论式标题，叙事线闭环
- [ ] 信息密度：单页正文≤300字，无大段文字堆砌
- [ ] 品牌合规：配色/字体全稿统一，主色≤3种，辅助色≤2种
- [ ] 对比度合规：文字与背景对比度≥4.5:1（WCAG 2.1 AA）
- [ ] 图标一致性：所有图标同风格、同色系、同尺寸
- [ ] 图片服务观点：每张配图服务于当前页核心观点，无装饰性空图
- [ ] 图表合规：类型匹配数据(对比→柱状/趋势→折线/占比→环形)，标注单位和数据源
- [ ] 演讲备注：每页有配套备注（话术+停顿点+互动设计）

---

## 方式2: Python 6步Pipeline

适用于需要完整需求管控、人工分步确认的场景。

### 执行流程

```python
from core.pipeline import OpenClawPPTSkill

skill = OpenClawPPTSkill("config/global_config.yaml")
result = skill.execute_pipeline({
    "核心主题": "AI投顾转型战略",
    "目标受众": "CEO/CTO级",
    "汇报时长": "15分钟",
    "总页数": 10,
    "交付格式": ".pptx",
    "品牌VI": "绿色科技风",
    "内容禁忌": "避免未上线功能"
})
```

### 6步串行Pipeline

| Step | 名称 | 输入 | 输出 | 关键约束 |
|:---:|------|------|------|----------|
| 1 | 需求解析与对齐 | 用户原始需求 | 需求对齐确认单 | 7项必填参数采集完毕 |
| 2 | 大纲与逻辑架构 | 对齐确认单+VI规范 | 完整大纲+叙事线 | 金字塔原理，核心方案占60% |
| 3 | 单页内容设计 | 大纲+叙事线 | 逐页核心内容 | 每页1观点，≤300字，结论式标题 |
| 4 | 视觉规范与布局 | 内容+VI规范 | 页面布局规格 | 4大设计原则，对比度合规 |
| 5 | 配套素材生成 | 布局+内容+VI | 图片+图表+代码 | 配图服务观点，图表匹配数据 |
| 6 | 校验与交付 | 全部中间产物 | 最终PPT+备注 | 全维度校验通过，违规项自动优化 |

### 7种布局类型（Python版）

| 布局 | 视觉特征 | 适用场景 |
|------|----------|----------|
| **cover** | 深色背景 + 浅绿大标题 + 底部3个指标卡片 | 封面页 |
| **toc** | 白底 + 绿色编号圆圈 + 白色卡片列表 | 目录/议程 |
| **bullets** | 白底 + 橙色编号徽章 + 白色圆角卡片 | 要点/论述页 |
| **steps** | F/A/S/T彩色标签 + 白色卡片 + 连接箭头 | 流程/步骤页 |
| **matrix** | 白底 + 2×2象限卡片(彩色描边+标签+要点) + 可选总结条 | SWOT/BCG/矩阵分析页 |
| **comparison** | 白底 + 左右对比列(灰/绿双卡+彩色pill标题) + VS标识 | 传统vs新范式/现状vs目标 |
| **closing** | 深色背景 + 居中Q&A标题 + 装饰线 | 结尾页 |

matrix / comparison 的 content 结构（JSON直传或body回退解析）：

```python
{
    "id": "slide-6",
    "layout": "matrix",
    "title": "SWOT战略诊断",
    "quadrants": [  # 最多4个；缺省时用 body 每行 "标签|要点1;要点2" 回退解析
        {"label": "S 优势", "items": ["牌照齐全", "团队500人"], "color": "#10B981"}
    ],
    "summary": "底部总结条（可选）"
}
{
    "id": "slide-7",
    "layout": "comparison",
    "title": "传统投顾 vs 智能投顾",
    "comparison": {  # 缺省时用 body 每行 "左侧要点|右侧要点" 回退解析
        "left":  {"title": "传统模式", "items": ["人工荐股", "服务半径有限"]},
        "right": {"title": "新范式",   "items": ["AI辅助决策", "规模化服务"]}
    },
    "summary": "底部总结条（可选）"
}
```

### 图片生成系统

#### 5种图片角色

| 角色 | 格式 | 数量占比 | 出现位置 |
|------|------|----------|----------|
| **background** | JPEG (2048×1152px) | 1.7% | 封面/结尾页，全出血 |
| **illustration** | JPEG (726-4550px宽) | 5% | 内容页左侧/顶部，视觉锚点 |
| **icon_pair** | SVG+PNG (48×48px) | 66% | 几乎每个内容卡片 |
| **section_icon** | SVG+PNG (48×48px) | 21% | 分隔页/分区布局 |
| **logo** | PNG (251×110px) | 0.8% | 结尾页底部 |

#### SVG图标规范

| 属性 | 规格 |
|------|------|
| 尺寸 | 48×48 viewBox |
| 描边 | stroke-width: 2.0 |
| 亮底图标色 | #FF6F00 (琥珀橙) 或 STYLE['orange'] |
| 暗底图标色 | #FFFFFF (纯白) |
| 风格 | Material Design线性图标 |

#### 关键词→图标映射 (ICON_MAP)

```python
ICON_MAP = {
    "网关": "gateway", "智能体": "agent", "技能": "plugin", "记忆": "memory",
    "风险": "shield", "安全": "lock", "凭证": "key", "攻击": "bug",
    "文件": "folder", "浏览器": "globe", "系统": "terminal", "API": "api",
    "市场": "trending", "用户": "person", "数据": "database", "自动化": "gear",
    "观察": "eye", "思考": "brain", "行动": "hand", "检查": "checkmark",
    "本地": "home", "开源": "code", "跨平台": "layers", "效率": "rocket",
}
```

#### 3种图片生成模式

| 模式 | 说明 | 何时使用 |
|------|------|----------|
| **placeholder** | 1x1像素占位PNG | 开发测试、快速预览 |
| **api** | 调用外部文生图API (DALL-E/通义万相) | 有API密钥时 |
| **workbuddy** | 写入manifest.json，AI助手调用ImageGen | WorkBuddy环境（推荐） |

#### WorkBuddy图片桥接流程

1. 运行Python生成 → `image_generator` 产出 `output/images/generate_manifest.json`
2. AI助手读取manifest，对每个pending条目按角色处理：
   - `background/illustration` → 调用 ImageGen 工具
   - `icon_pair` → 内置图标库获取SVG → 替换主色 → 导出PNG
3. 将结果复制到manifest指定的 `output_path`
4. 重新运行PPT生成以嵌入图片

#### 图片密度参考（基于参考PPT《OpenClaw技术扫盲交流》）

| 页面类型 | 图片数 | 构成 |
|----------|--------|------|
| 封面页 | 2-3 | 1×background + 1-2×decoration |
| 目录页 | 4-8 | N×icon_pair |
| 要点/论述页 | 5-7 | 1×illustration + 3×icon_pair |
| 步骤/流程页 | 8-11 | N×icon_pair + N×section_icon |
| 分隔页 | 3 | 3×section_icon |
| 结尾页 | 2-4 | 1×background + 1×logo + 1×decoration |

### 图表系统

JSON中通过 `chart_data` 字段添加图表：

```python
{
    "id": "slide-5",
    "layout": "bullets",
    "title": "市场增长趋势",
    "bullets": ["要点1", "要点2"],
    "chart_data": {
        "type": "bar",  # bar / line / pie
        "title": "市场规模预测",
        "data": { "x": ["2024","2025","2026"], "y": [190,257,321] }
    }
}
```

图表同步输出4种文件（`output/charts/`）：
- `{page_id}_chart.png` — 嵌入PPT的位图
- `{page_id}_chart.svg` — 矢量编辑源文件
- `{page_id}_data.csv` — CSV数据源
- `{page_id}_chart.py` — 可独立执行的Python生成脚本

---

## 约束规则引擎

以下规则100%强制遵守，违反则生成失败（对齐 HarnessConfig.md）：

### 全局硬规则

1. **金字塔原理强制约束**：结论先行，以上统下，归类分组，逻辑递进，内容层级≤3层
2. **单页单核心观点**：每页有且仅有1个结论式核心标题，所有内容服务于该观点
3. **信息密度硬约束**：单页正文文字≤300字，核心信息≤3行，禁止大段文字堆砌
4. **受众适配强制约束**：内容技术深度、语言风格100%匹配目标受众，禁止跨层级输出
5. **品牌合规约束**：所有视觉元素严格符合VI规范，禁止违规使用颜色、字体、Logo

### 分模块规则

**内容结构**：
- 标题必须为结论式表达（正确《XX技术将延迟降低75%》，错误《XX技术优化介绍》）
- 叙事线遵循「是什么→为什么→怎么做→效果→下一步」闭环逻辑
- 技术内容分层：核心原理放正文，实现细节放演讲备注
- 所有论点必须有量化数据/可溯源案例支撑
- 每3-4页设置1个叙事钩子

**视觉呈现**：
- 全稿字体≤2种，字号层级清晰，标题与正文字号差≥4号
- 主色≤3种，辅助色≤2种，重点信息高亮占比≤10%
- 文字与背景对比度≥4.5:1（WCAG 2.1 AA）
- 全稿版式、图标风格、项目符号、页边距完全统一

**图片生成**：
- 图片100%服务于当前页核心观点，禁止装饰性空图
- 风格全稿统一，分辨率≥300DPI，宽高比适配布局
- 图片占单页面积≤70%，与文字有明确分区
- 文生图Prompt模板：`[主题], [风格], 配色:主色{primary}, [构图], 无水印, 无文字, 高分辨率`

**图表代码**：
- 图表类型匹配数据：对比→柱状/趋势→折线/占比→环形/流程→泳道/架构→拓扑
- 单页图表≤1个，数据系列≤6个，必须标注单位和数据源
- 图表配色匹配VI规范，同步输出CSV+Python源码
- 代码≤20行/页，等宽字体，带行号与语法高亮

---

## 项目文件结构

```
high-quality-ppt-skill/
├── SKILL.md                         # 本文件（技能定义，通用：workbuddy/openclaw/hermes 等智能体均可加载）
├── styles/                           # PPT风格样例库（按风格分目录维护，共5套）
│   ├── registry.yaml                 # 风格注册表（关键词匹配/回退策略）
│   ├── README.md                     # 风格库使用与维护说明
│   ├── _template/style.yaml          # 新风格 schema 模板
│   ├── consulting_tech_dark/         # 内置A：咨询科技风（暗色，默认回退）
│   │   └── style.yaml
│   ├── green_professional/           # 内置B：绿色专业风
│   │   └── style.yaml
│   ├── internet_tech_blue/           # 提取C：互联网科技风（亮蓝）
│   │   └── style.yaml
│   ├── business_planning_blue/       # 提取D：商业策划风（深蓝）
│   │   └── style.yaml
│   └── navy_corporate/               # 提取E：海军蓝商务风（深海军蓝+橙）
│       └── style.yaml
├── uploads/                          # 用户PPT模版上传目录（批量风格提取的输入）
│   └── README.md                     # 使用说明：放入.pptx后运行 style_extractor --batch
├── config/
│   ├── global_config.yaml            # 全局配置（VI/工具链/校验/执行模式）
│   └── constraints.yaml              # 合规约束规则
├── core/
│   ├── pipeline.py                   # 6步Pipeline总控（Harness入口）
│   ├── content_generator.py          # 内容生成（大纲+叙事线+页面+备注）
│   └── layout_designer.py            # 布局设计（版式+视觉分区+规范适配）
├── tools/
│   ├── pptx_generator.py             # PPTX生成（7种布局渲染器+STYLE字典）
│   ├── image_generator.py             # 配图生成（5角色+3模式+自动prompt+manifest）
│   ├── chart_generator.py             # 图表生成（3类型+4输出格式）
│   ├── icon_library.py               # SVG图标库（48×48, 主色可替换, 62关键词→57图标）
│   ├── style_extractor.py            # 风格提取器（用户上传PPT→style.yaml→登记registry）
│   ├── validate_layout.py            # 布局校验（元素越界/重叠/标题超长，生成后运行）
│   └── auto_image_plan.js            # 自动配图规划器（输入大纲+style.yaml→输出每页图像方案JSON，含风格色token注入与3档level）
├── validators/
│   ├── consistency_checker.py         # 一致性校验（字体/配色/版式）
│   └── compliance_checker.py          # 合规性校验（对比度/信息密度/品牌规范）
├── examples/
│   ├── generate_from_json.py          # JSON→PPT入口
│   ├── generate_ceo_ppt.py            # CEO级PPT生成示例
│   ├── tech_report_example.py         # 技术汇报示例
│   └── reference_layouts/             # 高质量参考设计素材（4张）
│       ├── 01_双卡图上文下_挑战与机遇.jpg
│       ├── 02_左图右文_核心目标棋盘.png
│       ├── 03_左图右文_就业趋势工厂.jpg
│       └── 04_左图右文_学习路径种子花朵.png
├── tests/
│   ├── test_e2e.py                   # E2E测试
│   └── test_skill.py                 # 模块单元测试（共29个用例）
├── generate_ppt.js                    # JS直接生成脚本（方式1，推荐）
├── HarnessConfig.md                    # Harness执行规范（6步+约束引擎）
├── README.md                          # 项目说明
├── requirements.txt                   # Python依赖
├── package.json                       # Node.js依赖
└── output/                            # 产出目录
    ├── *.pptx                         # PPT文件
    ├── images/                         # AI配图 + manifest.json
    └── charts/                         # 图表+CSV+源码
```

---

## 常见陷阱与预防

> 以下 6 条是生成高质量 PPT 的关键约束，生成前务必通读。

### 陷阱 1：高度预算失控 ⭐ 最常见

**现象**：元素重叠、越界、被 banner 覆盖。

**预防**：每页先做 Y 坐标规划表，再写代码。

```
画布 5.625"
├─ 页头 0 - 1.60"     (sectionTag + title + 分隔线)
├─ 内容 1.65 - 4.85"  (核心 3.2" 空间)
├─ banner 4.85 - 5.23" (可选, 0.38" 高, 最多 1 个)
└─ 页脚 5.32 - 5.54"  (source 左 + 页码 右)

规则：
✅ 所有元素 bottom ≤ 4.85" (有 banner 时)
✅ 所有元素 bottom ≤ 5.10" (无 banner 时)
✅ banner 只能 0 或 1 个
❌ 禁止元素 y+h > 5.10
```

**标准函数**：所有内页用 `addPageFooter(slide, no, total, source)` 统一管底部（source 左下 + 页码右下），不要手写。

### 陷阱 2：PptxGenJS transparency 参数位置 bug ⭐ 极易踩

**现象**：图片+覆盖层叠加后图片完全不可见（深色页变纯色、浅色页变白条）。

**根因**：PptxGenJS 的 `transparency` **必须写在 `fill` 对象内部**，写在 shape 顶层会被静默忽略 → 覆盖层变成 100% 不透明，把图盖死。

```javascript
// ❌ 错误：transparency 在 shape 顶层，被忽略，覆盖层 100% 不透明
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: "0A1A2F" }, transparency: 45
});

// ✅ 正确：transparency 在 fill 对象内，生成 <a:alpha val="55000"/>
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: "0A1A2F", transparency: 45 }
});
```

**验证方法**：生成后解压 pptx 检查 slide XML，确认有 `<a:alpha val="..."/>`：
```bash
# macOS / Linux
unzip -p output.pptx ppt/slides/slide1.xml | grep -o 'alpha val="[0-9]*"'
# Windows（PowerShell，需 Python）
python -c "import zipfile,re; print(re.findall(r'alpha val=\"[0-9]*\"', zipfile.ZipFile('output.pptx').read('ppt/slides/slide1.xml').decode('utf-8')))"
```

**深色背景页推荐配置**（hero image + dark overlay 模式）：
```javascript
slide.background = { color: C.dark };
slide.addImage({ path: img, x: 0, y: 0, w: 10, h: 5.625,
  sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });   // 图 90% 显示
slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: C.dark, transparency: 45 } });                      // 遮罩 55% 覆盖
```
效果：图片可见度 ~40-50%，文字清晰，视觉冲击力拉满。**禁止**图 transparency 70%+（图直接没了）。

**口诀**：`transparency` 永远跟着 `fill` 走，别放 shape 顶层。

### 陷阱 3：标题超长自动换行

**现象**：26pt 中文标题 21 字撑成 2 行，排版错位。

**预防**：按「字号 → 每字宽度」预估字数上限。

| 字号 | 每字宽度 | 8.6" 大标题上限 | 2.85" 卡片标题上限 |
|---|---|---|---|
| 26pt | 0.36" | **23 字** | — |
| 18pt | 0.25" | 34 字 | — |
| 14pt | 0.19" | 45 字 | **15 字** |
| 12pt | 0.17" | 50 字 | 16 字 |
| 10pt | 0.14" | 60 字 | 20 字 |

**规则**：
- 页面大标题（26pt）≤ **23 字**
- 卡片标题（14pt）≤ **15 字**
- 超出立即缩字，不要指望自动换行

### 陷阱 4：Write 覆盖文件导致函数丢失

**现象**：用 `Write` 全量覆盖 `generate_ppt.js` 后，`iconToBase64Png`/`addPageTitle` 等函数 ReferenceError。

**预防**：
- ✅ **修改已有文件必须用 Edit**（精确替换）
- ❌ 避免 `Write` 全量覆盖（易丢函数定义）
- ✅ 函数定义放文件头部，`main()` 放文件末尾
- ✅ 必须 Write 时，先 Read 确认结构，写入后 grep 验证函数定义存在

### 陷阱 5：第三方 API 结构没确认就调用

**现象**：`estimateCredits(plan)` 报 `plan.reduce is not a function`（实际返回 `{plan, skipped}` 对象）；`FaArrowTrendUp` 在 react-icons v5.6 不存在。

**预防**：
- 第三方函数调用前先 `console.log(JSON.stringify(result, null, 2).slice(0, 500))` 确认结构
- 图标数组生成前预校验：

```javascript
for (const [name, Component, color] of iconDefs) {
  if (typeof Component === 'undefined') {
    throw new Error(`Icon ${name} 在 react-icons 不存在，请换名`);
  }
}
```

### 陷阱 6：布局问题暴露给用户

**现象**：用户开 PPT 才发现「标题换行/元素重叠/图片折叠」。

**预防**：生成后跑 `tools/validate_layout.py` 自动校验：

```bash
python tools/validate_layout.py output/你的文件.pptx
```

检测项：
- 元素越界（y+h > 5.625）
- 元素重叠（矩形相交）
- 标题超长（按字号预估）

**生成 → 校验 → 修复 → 展示**，让 bug 留在自己手里，不传给用户。

---

## 注意事项

1. **中文字体兼容**：Noto Sans SC 未安装时自动回退（macOS → PingFang SC，Windows → Microsoft YaHei）
2. **全角引号**：Python字符串中避免使用全角引号 `""`，替换为 `「」`
3. **图片半透明叠加**：深色背景页用「图 transparency:10% + 覆盖层 fill:{color:X, transparency:45%}」hero+overlay 模式；**transparency 必须写在 fill 对象内**，写 shape 顶层会被静默忽略（覆盖层变 100% 不透明把图盖死）
4. **图表嵌入**：python-pptx 只支持PNG嵌入（SVG供矢量编辑）；PptxGenJS原生图表可直接嵌入
5. **配色变更**：JS版改C字典，Python版改STYLE字典 + global_config.yaml
6. **图片密度**：参考PPT平均6.4张/页，主要是icon_pair。生成PPT不应只有1张大配图
7. **图标色适配**：深色背景页用白色图标(#FFFFFF)，浅色背景页用主题色
8. **react-icons图标**：需通过 `ReactDOMServer.renderToStaticMarkup` + `sharp` 转PNG base64，不能直接嵌入SVG
9. **PptxGenJS颜色**：使用6位hex字符串（无#前缀），如 `"0D9488"`
10. **执行模式**：Python Pipeline支持 `human_confirm`（分步确认）和 `auto`（全自动）
11. **画布溢出守卫**：JS 生成脚本内置 `assertFits(slideNo, name, y, h, mode)` 工具（`mode="canvas"` 硬下界 5.625" / `mode="content"` 收紧到 5.10" 避开页码）。所有网格类布局（data_cards/three_column/matrix 等）必须在 row 计算后调一次 `assertFits` 兜底。规则：items ÷ cols 决定行数时，先按 `y0 + rows * (cardH + gap)` 算底，>limit 即触发错误。

---

## 依赖安装

### JS模式（方式1）

```bash
npm install pptxgenjs react react-dom react-icons sharp js-yaml
```

### Python模式（方式2/3）

```bash
pip install python-pptx matplotlib pyyaml requests
```

### 文本提取（QA用）

```bash
pip install "markitdown[pptx]"
```

---

## 版本记录

- **v3.5.2** (2026-07-25)：修正 PptxGenJS transparency 参数位置 bug（必须写在 `fill` 对象内）；深色背景页改用 hero+overlay 模式，配图可见度显著提升
- **v3.5.1** (2026-07-24)：新增「常见陷阱与预防」章节；新增 `tools/validate_layout.py` 布局校验；新增 `navy_corporate` 风格（第 5 套）
- **v3.5.0** (2026-07-23)：新增 body 主体图角色与 `positionForLayout` 位置解析器（6 种位置按布局决定）；新增 `examples/reference_layouts/` 参考设计素材
- **v3.4.x** (2026-07-23)：新增 `tools/auto_image_plan.js` 自动配图规划（风格色 token 注入、3 档 level、布局感知跳过、3 档降级 prompt）；新增 `assertFits` 画布溢出守卫
- **v3.3.0** (2026-07-23)：真 AI 生成改造——内容骨架 + `set_content_callback` 宿主 AI 回填，不依赖外部 LLM API
- **v3.2.0** (2026-07-22)：技能通用化（适配 workbuddy/openclaw/hermes）；新增 `styles/` 风格样例库与用户模版批量提取（`style_extractor.py`）
- **v3.1.0** (2026-05-20)：实现 `icon_library.py` 图标库（62 关键词→57 图标）
- **v3.0.0** (2026-05-09)：全面重构——JS 直接生成模式、8 种布局、PptxGenJS 原生图表、约束规则引擎
- **v1.x–v2.x** (2026-05)：初始版本与视觉规范迭代

