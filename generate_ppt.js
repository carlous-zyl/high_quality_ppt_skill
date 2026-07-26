// generate_ppt.js - 知识中台必要性优化版
// 风格: navy_corporate (深海军蓝+橙), 11页结构化方案
// 数据来源: 原《知识中台必要性.pptx》全部保留

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

// ===== Style Loading =====
const SKILL_DIR = path.join(process.env.HOME, ".workbuddy", "skills", "high-quality-ppt-skill");
const STYLE_NAME = "navy_corporate";

function loadPalette(skillDir, styleName) {
  const fallback = {
    background_dark: "0A1A2F", background_dark_2: "0F2C5A", background_light: "FFFFFF",
    card_dark: "142B45", card_light: "FFFFFF", card_subtle: "F5F7FA",
    primary: "0A1A2F", primary_light: "1B3A6B", primary_bright: "2DD4BF",
    accent: "F39C12", accent_light: "F5B041", accent2: "3B82F6",
    success: "10B981", warning: "EF4444", purple: "8B5CF6",
    text_main: "1A2A40", text_sub: "64748B", text_on_dark: "FFFFFF",
    text_on_dark_sub: "94A3B8", card_bg_light: "F5F7FA", divider: "E2E8F0",
  };
  try {
    const p = yaml.load(fs.readFileSync(path.join(skillDir, "styles", styleName, "style.yaml"), "utf8")).palette || {};
    return {
      background_dark: p.background_dark || fallback.background_dark,
      background_dark_2: p.background_dark_2 || fallback.background_dark_2,
      background_light: p.background_light || fallback.background_light,
      card_dark: p.card_dark || fallback.card_dark,
      card_light: p.card_light || fallback.card_light,
      card_subtle: p.card_subtle || fallback.card_subtle,
      primary: p.primary || fallback.primary,
      primary_light: p.primary_light || fallback.primary_light,
      primary_bright: p.primary_bright || fallback.primary_bright,
      accent: p.accent || fallback.accent,
      accent_light: p.accent_light || fallback.accent_light,
      accent2: p.accent2 || fallback.accent2,
      success: p.success || fallback.success,
      warning: p.warning || fallback.warning,
      purple: p.purple || fallback.purple,
      text_main: p.text_main || fallback.text_main,
      text_sub: p.text_sub || fallback.text_sub,
      text_on_dark: p.text_on_dark || fallback.text_on_dark,
      text_on_dark_sub: p.text_on_dark_sub || fallback.text_on_dark_sub,
      card_bg_light: p.card_bg_light || fallback.card_bg_light,
      divider: p.divider || fallback.divider,
    };
  } catch (e) {
    console.warn(`[style] 回退: ${e.message}`);
    return fallback;
  }
}
const C = loadPalette(SKILL_DIR, STYLE_NAME);

// ===== Helpers =====
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 90, color: "000000", opacity: 0.08 });

function addPageHeader(slide, no, total, sectionTag) {
  // 顶部小橙色横条
  slide.addShape(pres.Shapes.RECTANGLE, { x: 0, y: 0, w: 0.4, h: 0.06, fill: { color: C.accent } });
  // 左上：章节标签
  if (sectionTag) {
    slide.addText(sectionTag, {
      x: 0.5, y: 0.18, w: 6.0, h: 0.3,
      fontSize: 10, fontFace: "Arial", color: C.accent, charSpacing: 2, bold: true
    });
  }
}

function addPageFooter(slide, no, total, source) {
  // 左下：数据来源
  if (source) {
    slide.addText(source, {
      x: 0.5, y: 5.32, w: 6.5, h: 0.22,
      fontSize: 8, fontFace: "Arial", color: C.text_sub, italic: true
    });
  }
  // 右下：页码（标准位置）
  slide.addText(`${String(no).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, {
    x: 8.5, y: 5.32, w: 1.3, h: 0.22,
    fontSize: 9, fontFace: "Arial", color: C.text_sub, align: "right"
  });
}

function addPageTitle(slide, title, subtitle) {
  // 左侧色条
  slide.addShape(pres.Shapes.RECTANGLE, { x: 0.5, y: 0.55, w: 0.08, h: 0.65, fill: { color: C.primary } });
  slide.addText(title, {
    x: 0.7, y: 0.5, w: 8.6, h: 0.7,
    fontSize: 26, fontFace: "Noto Sans SC", bold: true, color: C.text_main
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.7, y: 1.18, w: 8.6, h: 0.35,
      fontSize: 12, fontFace: "Noto Sans SC", color: C.text_sub
    });
  }
  // 分隔线
  slide.addShape(pres.Shapes.RECTANGLE, { x: 0.5, y: 1.6, w: 9.0, h: 0.02, fill: { color: C.divider } });
}

// ===== Image Loading =====
const IMG_DIR = path.join(__dirname, "output", "images");
const IMAGES = {
  cover: path.join(IMG_DIR, "cover_image.png"),
  section1: path.join(IMG_DIR, "section1_image.png"),
  section2: path.join(IMG_DIR, "section2_image.png"),
  p4_body: path.join(IMG_DIR, "p4_body_top.png"),
  closing: path.join(IMG_DIR, "closing_image.png"),
  p5_banner: path.join(IMG_DIR, "p5_banner.png"),
  p7_side: path.join(IMG_DIR, "p7_side.png"),
};
const availableImages = {};
for (const [key, p] of Object.entries(IMAGES)) {
  if (fs.existsSync(p)) { availableImages[key] = p; }
}

// ===== Main =====
let pres;
const TOTAL_SLIDES = 10;
const slides = JSON.parse(fs.readFileSync(path.join(__dirname, "slides_meta.json"), "utf8"));

async function main() {
  pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "战略镇汇报";
  pres.title = "企业为什么必须建设知识中台";

  // ==== Load & pre-generate icons ====
  const fa = require("react-icons/fa");
  const icons = {};
  const iconDefs = [
    ["brain", fa.FaBrain, C.accent],
    ["database", fa.FaDatabase, C.accent],
    ["rocket", fa.FaRocket, C.accent],
    ["robot", fa.FaRobot, C.accent],
    ["users", fa.FaUserTie, C.accent],
    ["chart", fa.FaChartLine, C.accent],
    ["trend", fa.FaArrowUp, C.accent],
    ["shield", fa.FaShieldAlt, C.accent],
    ["speed", fa.FaTachometerAlt, C.accent],
    ["time", fa.FaClock, C.accent],
    ["cost", fa.FaCoins, C.accent],
    ["arrow", fa.FaLongArrowAltRight, C.accent],
    ["check", fa.FaCheckCircle, C.accent],
    ["quote", fa.FaQuoteLeft, C.accent],
  ];
  for (const [name, Component, color] of iconDefs) {
    icons[name] = await iconToBase64Png(Component, `#${color}`, 256);
  }

  // ============ P1: 封面 ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_dark };
    if (availableImages.cover) {
      s.addImage({ path: availableImages.cover, x: 0, y: 0, w: 10, h: 5.625,
        sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
      s.addShape(pres.Shapes.RECTANGLE, {
        x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.background_dark, transparency: 45 } });
    }
    // 左侧色条
    s.addShape(pres.Shapes.RECTANGLE, { x: 0.7, y: 2.2, w: 0.06, h: 1.4, fill: { color: C.accent } });
    // 顶部 tagline
    s.addText("ENTERPRISE KNOWLEDGE LAYER · 战略镇汇报", {
      x: 0.7, y: 1.5, w: 8.5, h: 0.4,
      fontSize: 11, fontFace: "Arial", color: C.accent_light, charSpacing: 4, bold: true
    });
    // 主标题
    s.addText("企业为什么必须建设知识中台", {
      x: 0.85, y: 2.0, w: 8.5, h: 1.1,
      fontSize: 38, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark
    });
    // 副标题
    s.addText("AI 时代的战略论证：基于 2024–2026 全球权威机构研究", {
      x: 0.85, y: 3.15, w: 8.5, h: 0.5,
      fontSize: 16, fontFace: "Noto Sans SC", color: C.text_on_dark_sub
    });
    // 底部数据来源
    s.addText(slides[0].sourceLine, {
      x: 0.85, y: 4.9, w: 8.5, h: 0.3,
      fontSize: 11, fontFace: "Arial", color: C.text_on_dark_sub, charSpacing: 2
    });
    s.addNotes("封面：开场强调这是基于 7 家全球权威机构研究的战略论证。强调 3 个核心点：①AI 时代拐点；②权威背书；③战略窗口期紧迫性。");
  }

  // ============ P2: 议程 ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 2, TOTAL_SLIDES, "AGENDA · 三段论");
    addPageTitle(s, "汇报议程", "Why – What – Now What");
    const agenda = slides[1].agenda;
    // 横向三列卡片
    const colW = 2.7, gap = 0.3, startX = (10 - colW * 3 - gap * 2) / 2;
    agenda.forEach((it, i) => {
      const x = startX + i * (colW + gap);
      // 顶部大编号
      s.addText(it.no, {
        x, y: 1.9, w: colW, h: 1.2,
        fontSize: 72, fontFace: "Arial", bold: true,
        color: C.accent, align: "left"
      });
      // 编号下方横条
      s.addShape(pres.Shapes.RECTANGLE, { x, y: 3.15, w: 0.6, h: 0.04, fill: { color: C.primary } });
      // 标题
      s.addText(it.title, {
        x, y: 3.3, w: colW, h: 0.4,
        fontSize: 18, fontFace: "Noto Sans SC", bold: true, color: C.text_main
      });
      // 描述
      s.addText(it.desc, {
        x, y: 3.75, w: colW, h: 0.6,
        fontSize: 12, fontFace: "Noto Sans SC", color: C.text_sub
      });
    });
    addPageFooter(s, 2, TOTAL_SLIDES, "");
    s.addNotes("议程页：3 段式叙事，告知听众我们将先讲 Why Now（时机），再讲 Why Must（必要性），最后讲 Now What（如何行动）。每段约 3 页。");
  }

  // ============ P3: PART 1 分隔 ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_dark };
    if (availableImages.section1) {
      s.addImage({ path: availableImages.section1, x: 0, y: 0, w: 10, h: 5.625,
        sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
      s.addShape(pres.Shapes.RECTANGLE, {
        x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.background_dark, transparency: 45 } });
    }
    s.addText("PART 1", {
      x: 0.8, y: 1.7, w: 8.4, h: 0.5,
      fontSize: 16, fontFace: "Arial", color: C.accent_light, charSpacing: 8, bold: true
    });
    s.addText("为什么是现在", {
      x: 0.8, y: 2.3, w: 8.4, h: 1.1,
      fontSize: 48, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark
    });
    s.addShape(pres.Shapes.RECTANGLE, { x: 0.8, y: 3.5, w: 1.6, h: 0.04, fill: { color: C.accent } });
    s.addText("AI 智能体 · 数据飞轮 · 市场规模 — 三重拐点同步到来", {
      x: 0.8, y: 3.75, w: 8.4, h: 0.5,
      fontSize: 14, fontFace: "Noto Sans SC", color: C.text_on_dark_sub
    });
    s.addNotes("PART 1 过渡：用 1 张过渡页承上启下，强调「现在是分水岭」。接下来用 2 页讲三重拐点与核心数据。");
  }

  // ============ P4: 三重拐点 three_column ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 4, TOTAL_SLIDES, "为什么是现在");
    addPageTitle(s, slides[3].title, slides[3].subtitle);
    // 3 列卡片（去掉折叠的body_top主体图，重排为紧凑3列）
    const cols = slides[3].columns;
    const colW = 2.85, gap = 0.225, startX = (10 - colW * 3 - gap * 2) / 2;
    const cardY = 1.8;
    const cardH = 3.0;
    cols.forEach((col, i) => {
      const x = startX + i * (colW + gap);
      // 卡片底
      s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
        x, y: cardY, w: colW, h: cardH,
        fill: { color: C.card_light }, rectRadius: 0.08, shadow: makeShadow(),
        line: { color: C.divider, width: 0.5 }
      });
      // 顶部色条
      s.addShape(pres.Shapes.RECTANGLE, { x, y: cardY, w: colW, h: 0.08, fill: { color: C.accent } });
      // 顶部图标圆 + 图标
      s.addShape(pres.Shapes.OVAL, { x: x + 0.2, y: cardY + 0.25, w: 0.5, h: 0.5, fill: { color: C.accent } });
      s.addImage({ data: icons[col.icon], x: x + 0.27, y: cardY + 0.32, w: 0.36, h: 0.36,
        sizing: { type: "contain", w: 0.36, h: 0.36 } });
      // 标题（图标右侧）
      s.addText(col.title, {
        x: x + 0.8, y: cardY + 0.22, w: colW - 0.95, h: 0.32,
        fontSize: 15, fontFace: "Noto Sans SC", bold: true, color: C.primary
      });
      s.addText(col.subtitle, {
        x: x + 0.8, y: cardY + 0.5, w: colW - 0.95, h: 0.28,
        fontSize: 10, fontFace: "Noto Sans SC", color: C.text_sub
      });
      // 大数据
      s.addText(col.metric, {
        x: x + 0.15, y: cardY + 0.9, w: colW - 0.3, h: 0.7,
        fontSize: 32, fontFace: "Arial", bold: true, color: C.accent
      });
      s.addText(col.metricLabel, {
        x: x + 0.15, y: cardY + 1.6, w: colW - 0.3, h: 0.3,
        fontSize: 9, fontFace: "Noto Sans SC", color: C.text_sub
      });
      // 分隔小线
      s.addShape(pres.Shapes.RECTANGLE, {
        x: x + 0.15, y: cardY + 1.95, w: 0.5, h: 0.02, fill: { color: C.accent }
      });
      // 要点列表（最多3条）
      const pts = col.points.slice(0, 3);
      pts.forEach((pt, j) => {
        s.addShape(pres.Shapes.OVAL, {
          x: x + 0.15, y: cardY + 2.12 + j * 0.28, w: 0.08, h: 0.08, fill: { color: C.accent }
        });
        s.addText(pt, {
          x: x + 0.3, y: cardY + 2.04 + j * 0.28, w: colW - 0.45, h: 0.25,
          fontSize: 10, fontFace: "Noto Sans SC", color: C.text_main
        });
      });
    });
    // 底部金句 banner（放 4.95 避开页脚）
    s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 4.95, w: 9.0, h: 0.32,
      fill: { color: C.background_dark }, rectRadius: 0.04
    });
    s.addText("三股力量同步抵达临界点 — 任何单一拐点都足以启动知识中台建设，三者叠加则是不可错过的战略窗口期", {
      x: 0.7, y: 4.95, w: 8.6, h: 0.32,
      fontSize: 10, fontFace: "Noto Sans SC", color: C.text_on_dark, italic: true, valign: "middle"
    });
    addPageFooter(s, 4, TOTAL_SLIDES, "数据来源：Gartner 2025 十大战略趋势 / IDC FutureScape 2026 / 行业研究综合");
    s.addNotes("三重拐点：技术成熟（Agentic AI）+ 数据爆发（私域资产化）+ 市场扩张（420 亿美元 + 12.1% CAGR）。强调 3 者是同步抵达临界点，不是孤立事件。讲法建议：每列用 1 句话讲清拐点，底部金句收口。");
  }

  // ============ P5: 核心数据 data_cards ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 5, TOTAL_SLIDES, "为什么是现在");
    addPageTitle(s, slides[4].title, slides[4].subtitle);
    // 4 张数据卡片
    const cards = slides[4].cards;
    const colW = 2.15, rowH = 1.7, gapX = 0.13, gapY = 0.2;
    const startX = (10 - colW * 4 - gapX * 3) / 2;
    const startY = 1.85;
    cards.forEach((card, i) => {
      const x = startX + i * (colW + gapX);
      const y = startY;
      const colorHex = card.color === "accent" ? C.accent : C.primary;
      // 卡片背景
      s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
        x, y, w: colW, h: rowH,
        fill: { color: C.card_light }, rectRadius: 0.08, shadow: makeShadow(),
        line: { color: C.divider, width: 0.5 }
      });
      // 顶部色条
      s.addShape(pres.Shapes.RECTANGLE, { x, y, w: colW, h: 0.06, fill: { color: colorHex } });
      // Tag
      s.addText(card.tag, {
        x: x + 0.2, y: y + 0.18, w: colW - 0.4, h: 0.25,
        fontSize: 8, fontFace: "Arial", color: colorHex, bold: true, charSpacing: 2
      });
      // 大数据（22pt 修复 Agentic AI 在窄卡换行）
      s.addText(card.value, {
        x: x + 0.2, y: y + 0.45, w: colW - 0.4, h: 0.5,
        fontSize: 22, fontFace: "Arial", bold: true, color: C.primary
      });
      // 描述
      s.addText(card.desc, {
        x: x + 0.2, y: y + 1.0, w: colW - 0.4, h: 0.65,
        fontSize: 9, fontFace: "Noto Sans SC", color: C.text_sub
      });
    });
    // 中间空白带：横向叙事图「私域知识 → Agent 能力转化」（3.62-4.42，填补卡片与banner间空白）
    if (availableImages.p5_banner) {
      s.addImage({ path: availableImages.p5_banner, x: 0.5, y: 3.62, w: 9.0, h: 0.8,
        sizing: { type: "cover", w: 9.0, h: 0.8 } });
      // 细边框勾勒
      s.addShape(pres.Shapes.RECTANGLE, { x: 0.5, y: 3.62, w: 9.0, h: 0.02, fill: { color: C.accent } });
      s.addShape(pres.Shapes.RECTANGLE, { x: 0.5, y: 4.4, w: 9.0, h: 0.02, fill: { color: C.accent } });
    }
    // 底部金句 banner
    s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 4.5, w: 9.0, h: 0.6,
      fill: { color: C.background_dark }, rectRadius: 0.05
    });
    s.addImage({ data: icons.quote, x: 0.7, y: 4.65, w: 0.3, h: 0.3, sizing: { type: "contain", w: 0.3, h: 0.3 } });
    s.addText("AI 时代的竞争，是「谁能把私域知识变成 Agent 可即时调用能力」的竞争 — 三重拐点叠加，现在是建设知识中台的战略窗口期", {
      x: 1.1, y: 4.55, w: 8.2, h: 0.5,
      fontSize: 11, fontFace: "Noto Sans SC", color: C.text_on_dark, italic: true, valign: "middle"
    });
    addPageFooter(s, 5, TOTAL_SLIDES, "来源：Gartner《2025 十大战略技术趋势》/ IDC FutureScape 2026《认知智能与营销研究》");
    s.addNotes("核心数据论证：4 个权威数据点支撑「现在是战略窗口期」。讲法建议：每个数据 1 句话解释来源+含义，节奏明快。底部金句是本节核心 Take-away。");
  }

  // ============ P6: PART 2 分隔 ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_dark };
    if (availableImages.section2) {
      s.addImage({ path: availableImages.section2, x: 0, y: 0, w: 10, h: 5.625,
        sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
      s.addShape(pres.Shapes.RECTANGLE, {
        x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.background_dark, transparency: 45 } });
    }
    s.addText("PART 2", {
      x: 0.8, y: 1.7, w: 8.4, h: 0.5,
      fontSize: 16, fontFace: "Arial", color: C.accent_light, charSpacing: 8, bold: true
    });
    s.addText("为什么必须建", {
      x: 0.8, y: 2.3, w: 8.4, h: 1.1,
      fontSize: 48, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark
    });
    s.addShape(pres.Shapes.RECTANGLE, { x: 0.8, y: 3.5, w: 1.6, h: 0.04, fill: { color: C.accent } });
    s.addText("七大权威机构共识 × 四维可量化战略价值", {
      x: 0.8, y: 3.75, w: 8.4, h: 0.5,
      fontSize: 14, fontFace: "Noto Sans SC", color: C.text_on_dark_sub
    });
    s.addNotes("PART 2 过渡：从「why now」进入「why must」——讲权威背书与可量化价值，这是说服决策层的关键。");
  }

  // ============ P7: 七大权威共识 comparison ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 7, TOTAL_SLIDES, "为什么必须建");
    addPageTitle(s, "七大权威机构共识：知识中台 = 战略必选", slides[6].subtitle);
    // 表头（表格压到 6.5" 宽，右侧留 2.85" 放智库网络图）
    const tableY = 1.75;
    const colW1 = 1.2, colW2 = 2.9, colW3 = 2.4;
    const tableW = colW1 + colW2 + colW3 + 0.0; // 6.5
    const startX = 0.5;
    // 表头背景
    s.addShape(pres.Shapes.RECTANGLE, { x: startX, y: tableY, w: tableW, h: 0.38, fill: { color: C.primary } });
    s.addText("权威机构", {
      x: startX + 0.12, y: tableY + 0.04, w: colW1, h: 0.3,
      fontSize: 11, fontFace: "Arial", bold: true, color: C.text_on_dark, valign: "middle"
    });
    s.addText("核心观点", {
      x: startX + colW1 + 0.08, y: tableY + 0.04, w: colW2, h: 0.3,
      fontSize: 11, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark, valign: "middle"
    });
    s.addText("权威证据", {
      x: startX + colW1 + colW2 + 0.12, y: tableY + 0.04, w: colW3, h: 0.3,
      fontSize: 11, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark, valign: "middle"
    });
    // 7 行数据（斑马纹，行高 0.36）
    const rows = slides[6].rows;
    const rowH = 0.36;
    rows.forEach((r, i) => {
      const y = tableY + 0.38 + i * rowH;
      // 斑马
      if (i % 2 === 0) {
        s.addShape(pres.Shapes.RECTANGLE, { x: startX, y, w: tableW, h: rowH, fill: { color: C.card_subtle } });
      }
      // 机构名（橙色加粗）
      s.addText(r.dim, {
        x: startX + 0.12, y: y + 0.04, w: colW1, h: 0.28,
        fontSize: 11, fontFace: "Arial", bold: true, color: C.accent, valign: "middle"
      });
      // 核心观点
      s.addText(r.consensus, {
        x: startX + colW1 + 0.08, y: y + 0.04, w: colW2, h: 0.28,
        fontSize: 10, fontFace: "Noto Sans SC", color: C.text_main, valign: "middle"
      });
      // 证据
      s.addText(r.evidence, {
        x: startX + colW1 + colW2 + 0.12, y: y + 0.04, w: colW3, h: 0.28,
        fontSize: 9, fontFace: "Noto Sans SC", color: C.text_sub, valign: "middle"
      });
    });
    // 右侧竖图：全球智库网络（图高2.72+说明0.22，结束4.74避开banner 4.85）
    if (availableImages.p7_side) {
      s.addImage({ path: availableImages.p7_side, x: 7.15, y: tableY, w: 2.35, h: 2.72,
        sizing: { type: "cover", w: 2.35, h: 2.72 } });
      // 图下说明
      s.addText("全球权威智库网络", {
        x: 7.15, y: tableY + 2.72 + 0.05, w: 2.35, h: 0.22,
        fontSize: 9, fontFace: "Noto Sans SC", color: C.text_sub, align: "center"
      });
    }
    // 底部金句（4.85 避开表格末尾 4.65）
    s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 4.85, w: 9.0, h: 0.38,
      fill: { color: C.background_dark }, rectRadius: 0.04
    });
    s.addText("→ 7 家机构从「该不该建」到「必须建」形成统一口径 — 知识中台已不是技术选择，是战略共识", {
      x: 0.7, y: 4.85, w: 8.6, h: 0.38,
      fontSize: 10, fontFace: "Noto Sans SC", color: C.text_on_dark, valign: "middle"
    });
    addPageFooter(s, 7, TOTAL_SLIDES, "数据来源：Gartner / IDC / McKinsey / Deloitte / KPMG / 艾瑞咨询 / 亿欧智库 权威报告综合");
    s.addNotes("权威共识矩阵：列出 7 家权威机构口径。重点强调：不是 1 家说，是 7 家形成共识，决策风险被显著降低。讲法建议：可点名 2-3 家关键机构深化（如 Gartner+IDC+McKinsey）。");
  }

  // ============ P8: 四维战略价值 data_cards ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 8, TOTAL_SLIDES, "为什么必须建");
    addPageTitle(s, slides[7].title, slides[7].subtitle);
    // 2x2 卡片矩阵
    const cards = slides[7].cards;
    const colW = 4.3, rowH = 1.4, gapX = 0.2, gapY = 0.15;
    const startX = (10 - colW * 2 - gapX) / 2;
    const startY = 1.78;
    cards.forEach((card, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = startX + col * (colW + gapX);
      const y = startY + row * (rowH + gapY);
      const colorHex = card.color === "accent" ? C.accent : C.primary;
      // 卡片
      s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
        x, y, w: colW, h: rowH,
        fill: { color: C.card_light }, rectRadius: 0.08, shadow: makeShadow(),
        line: { color: C.divider, width: 0.5 }
      });
      // 左侧图标圆
      s.addShape(pres.Shapes.OVAL, { x: x + 0.2, y: y + 0.22, w: 0.5, h: 0.5, fill: { color: colorHex } });
      s.addImage({ data: icons[card.icon], x: x + 0.27, y: y + 0.29, w: 0.36, h: 0.36,
        sizing: { type: "contain", w: 0.36, h: 0.36 } });
      // 大数据
      s.addText(card.value, {
        x: x + 0.85, y: y + 0.12, w: 2.5, h: 0.6,
        fontSize: 32, fontFace: "Arial", bold: true, color: colorHex
      });
      // 标签
      s.addText(card.label, {
        x: x + 0.85, y: y + 0.72, w: colW - 1.0, h: 0.3,
        fontSize: 12, fontFace: "Noto Sans SC", bold: true, color: C.text_main
      });
      // 描述
      s.addText(card.desc, {
        x: x + 0.85, y: y + 1.02, w: colW - 1.0, h: 0.32,
        fontSize: 10, fontFace: "Noto Sans SC", color: C.text_sub
      });
    });
    // 底部金句（4.78 避开卡片底 4.73）
    s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 4.78, w: 9.0, h: 0.38,
      fill: { color: C.background_dark }, rectRadius: 0.04
    });
    s.addText("→ 4 项可量化战略价值：决策 +37% / 效率 +45% / 时间 -30% / 成本 -30% — 是经营级回报，不是锦上添花", {
      x: 0.7, y: 4.78, w: 8.6, h: 0.38,
      fontSize: 10, fontFace: "Noto Sans SC", color: C.text_on_dark, valign: "middle"
    });
    addPageFooter(s, 8, TOTAL_SLIDES, "数据来源：IDC / McKinsey / Deloitte 多份行业报告综合");
    s.addNotes("四维战略价值：可量化、可验证、可写进 KPI。每个数据都对应到经营指标——决策准确度/运营效率/研究时间/运营成本。讲法建议：每个值都强调「可以写进年度 KPI」");
  }

  // ============ P9: 战略窗口期 timeline ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_light };
    addPageHeader(s, 9, TOTAL_SLIDES, "如何快速建成");
    addPageTitle(s, slides[8].title, slides[8].subtitle);
    // 时间轴主线
    const lineY = 3.1;
    s.addShape(pres.Shapes.RECTANGLE, { x: 0.7, y: lineY, w: 8.6, h: 0.04, fill: { color: C.accent } });
    // 3 个阶段
    const phases = slides[8].phases;
    phases.forEach((p, i) => {
      const x = 0.85 + i * 3.0;
      // 节点圆
      const nodeColor = p.color === "primary" ? C.primary : p.color === "accent" ? C.accent : C.primary_bright;
      s.addShape(pres.Shapes.OVAL, { x: x + 1.3, y: lineY - 0.15, w: 0.35, h: 0.35, fill: { color: nodeColor } });
      s.addText(String(i + 1), {
        x: x + 1.3, y: lineY - 0.13, w: 0.35, h: 0.32,
        fontSize: 14, fontFace: "Arial", bold: true, color: C.text_on_dark, align: "center", valign: "middle"
      });
      // 上方时间
      s.addText(p.date, {
        x, y: 2.3, w: 2.9, h: 0.35,
        fontSize: 13, fontFace: "Arial", bold: true, color: nodeColor, align: "center"
      });
      s.addText(p.label, {
        x, y: 2.62, w: 2.9, h: 0.3,
        fontSize: 10, fontFace: "Arial", color: C.text_sub, align: "center", charSpacing: 3
      });
      // 下方卡片
      s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
        x, y: 3.45, w: 2.9, h: 1.4,
        fill: { color: C.card_light }, rectRadius: 0.08, shadow: makeShadow(),
        line: { color: nodeColor, width: 1.5 }
      });
      s.addText(p.title, {
        x: x + 0.15, y: 3.6, w: 2.6, h: 0.35,
        fontSize: 14, fontFace: "Noto Sans SC", bold: true, color: C.primary, align: "center"
      });
      s.addText(p.desc, {
        x: x + 0.2, y: 4.0, w: 2.5, h: 0.75,
        fontSize: 10, fontFace: "Noto Sans SC", color: C.text_sub, align: "center"
      });
    });
    // 顶部金句
    s.addShape(pres.Shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 1.7, w: 9.0, h: 0.5,
      fill: { color: C.accent }, rectRadius: 0.05
    });
    s.addText("未来 24 个月是从「试水」到「领跑」的关键窗口 — 启动越早，护城河越深", {
      x: 0.7, y: 1.75, w: 8.6, h: 0.4,
      fontSize: 12, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark, valign: "middle"
    });
    addPageFooter(s, 9, TOTAL_SLIDES, "");
    s.addNotes("战略窗口期：3 阶段路径（锚定-嵌入-规模化）。重点讲时间紧迫性——错过 24 个月 = 错过 5 年。讲法建议：把 3 个阶段对应到具体里程碑，让决策层看到「可执行」。");
  }

  // ============ P10: 结尾 closing ============
  {
    const s = pres.addSlide();
    s.background = { color: C.background_dark };
    if (availableImages.closing) {
      s.addImage({ path: availableImages.closing, x: 0, y: 0, w: 10, h: 5.625,
        sizing: { type: "cover", w: 10, h: 5.625 }, transparency: 10 });
      s.addShape(pres.Shapes.RECTANGLE, {
        x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.background_dark, transparency: 45 } });
    }
    // 顶部装饰
    s.addShape(pres.Shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.accent } });
    // 核心金句（26pt 缩到 23 字内）
    s.addText("知识中台不是「要不要建」，而是「多快建成」", {
      x: 0.8, y: 1.5, w: 8.4, h: 1.2,
      fontSize: 26, fontFace: "Noto Sans SC", bold: true, color: C.text_on_dark, align: "center"
    });
    // 金句下方副标
    s.addText(slides[9].subtitle, {
      x: 0.8, y: 2.7, w: 8.4, h: 0.5,
      fontSize: 15, fontFace: "Noto Sans SC", color: C.text_on_dark_sub, align: "center"
    });
    // 分隔线
    s.addShape(pres.Shapes.RECTANGLE, { x: 4.2, y: 3.4, w: 1.6, h: 0.04, fill: { color: C.accent } });
    // Q&A
    s.addText(slides[9].highlight, {
      x: 0.8, y: 3.7, w: 8.4, h: 0.6,
      fontSize: 22, fontFace: "Arial", bold: true, color: C.accent_light, align: "center", charSpacing: 4
    });
    // 底部源机构
    s.addText(slides[0].sourceLine, {
      x: 0.8, y: 4.9, w: 8.4, h: 0.3,
      fontSize: 10, fontFace: "Arial", color: C.text_on_dark_sub, align: "center", charSpacing: 2
    });
    s.addNotes("结尾页：核心金句「要不要建 → 多快建成」，最后落到 Q&A 引导讨论。强调知识中台是「必需底座」而非「技术选项」。");
  }

  // ===== Save =====
  const outputPath = path.join(__dirname, "output", "知识中台必要性_优化版.pptx");
  await pres.writeFile({ fileName: outputPath });
  console.log(`✅ PPT已生成: ${outputPath}`);

  // 统计
  const stat = fs.statSync(outputPath);
  console.log(`   文件大小: ${(stat.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`   总页数: ${TOTAL_SLIDES}`);
}

main().catch(err => { console.error("❌ 生成失败:", err); process.exit(1); });
