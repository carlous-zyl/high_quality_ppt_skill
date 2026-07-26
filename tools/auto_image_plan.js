// tools/auto_image_plan.js
// 用途: 接收大纲 + style.yaml, 自动规划每页配图(角色/prompt/位置), 输出 JSON 清单
// v3.5.0 升级:
//   - 新增 body 角色(实景/叙事 prompt, 非"minimalist"千篇一律)
//   - 新增 positionForLayout(imagePosition) 位置解析器(去除硬编码)
//   - slide meta 加 body / imagePosition / imageStyle 字段, AI 驱动
//   - 决策: body=true → body 角色 + imagePosition 决定位置; 否则角落或跳过
//
// 用法:
//   const { planImages, positionForLayout, robustPrompts } = require('./tools/auto_image_plan');
//   const { plan, skipped } = planImages(slides, '/path/to/style.yaml', { level: 'standard' });
//   // plan[i] = { idx, role, output, prompt, fallback_prompts, position, ... }
//   // position 由 imagePosition 字段解析, 不在代码里硬编码
//
// CLI:
//   echo '[{"idx":1,"type":"cover",...},{"idx":4,"type":"content","body":true,"imagePosition":"body_left",...}]' | \
//     node tools/auto_image_plan.js <style.yaml> <level> [--verbose]

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

const IMG_OUT = path.join(process.cwd(), "output", "images");

// 角色 prompt 模板
// body 角色: 实景/叙事图片(由模型根据 topic 自选照片或插画, 适配参考设计风格)
// background 角色: 全屏背景, 低透明度叠加深色遮罩
// illustration 角色: 角落装饰小图(传统"白底极简", 保留向后兼容)
const ROLE_TEMPLATES = {
  body: {
    prompt: (topic, color) =>
      `${topic}, professional high-quality photograph or detailed digital illustration, ` +
      `vivid colors with ${color.primaryName} and ${color.accentName} tones, ` +
      `well-composed, sharp focus, 16:9 aspect ratio, no text, no watermark`,
    size: "1280x720",
  },
  background: {
    prompt: (topic, color) =>
      `${topic}, abstract digital art, color palette dominated by ${color.primary} and ${color.accent}, ` +
      `dark deep ${color.background_dark} background, futuristic, professional, ` +
      `high resolution, 16:9 aspect ratio, no text, no watermark`,
    size: "1536x1024",
  },
  illustration: {
    prompt: (topic, color) =>
      `${topic}, minimalist digital illustration, ${color.primary} and ${color.accent} accent, ` +
      `clean white background, professional flat design, no text`,
    size: "1024x1024",
  },
};

// 触发插图的关键词 (仅当 body=false 时生效)
const ILLUSTRATION_TRIGGERS = [
  "AI", "转型", "数字化", "智能", "数据", "生成", "设计", "架构",
  "流程", "策略", "风险", "市场", "团队", "协作", "创新", "分析",
  "技术", "产品", "用户", "增长", "竞争", "运营", "组织", "升级",
];

function hasIllustrationTrigger(slide) {
  const text = `${slide.title || ""} ${slide.body || ""} ${slide.topic || ""}`;
  return ILLUSTRATION_TRIGGERS.some((k) => text.includes(k));
}

/**
 * 位置解析器 (v3.5.0 去除硬编码)
 * 输入: imagePosition 字符串 + slide meta (可选)
 * 输出: { x, y, w, h, transparency } 像素单位(in)
 * 支持的位置:
 *   - body_left:        左 40% 主体图 + 右 60% 文字
 *   - body_right:       右 40% 主体图 + 左 60% 文字
 *   - body_top:         顶部 9" 宽 × 2" 高的通栏
 *   - body_top_in_card: 卡片内顶部图
 *   - corner:           右上角 1.5" 小图 (传统)
 *   - background:       全屏背景
 */
function positionForLayout(imagePosition) {
  const pos = imagePosition || "body_left";
  const map = {
    body_left:        { x: 0.5, y: 1.55, w: 4.0, h: 3.0, transparency: 0 },
    body_right:       { x: 5.5, y: 1.55, w: 4.0, h: 3.0, transparency: 0 },
    body_top:         { x: 0.5, y: 1.4,  w: 9.0, h: 2.0, transparency: 0 },
    body_top_in_card: { x: 0.5, y: 1.5,  w: 4.2, h: 1.8, transparency: 0 },
    corner:           { x: 8.3, y: 0.3,  w: 1.5, h: 1.0, transparency: 30 },
    background:       { x: 0,   y: 0,    w: 10,  h: 5.625, transparency: 70 },
  };
  return map[pos] || map.body_left;
}

/**
 * 布局感知: 决定是否跳过角落插图 (v3.4.1 规则保留)
 * 返回 null = 不跳过; 返回 string = 跳过原因
 */
function shouldSkipIllustration(slide) {
  if (slide.body === true) return null; // body 角色独立处理, 这里不参与
  if (slide.skipCorner === true) return "显式 skipCorner=true";
  if (slide.skipCorner === false) return null;
  const layout = slide.layout || "content";
  const cardCount = Number(slide.cardCount || 0);
  if (layout === "data_cards" && cardCount >= 4) {
    return `data_cards≥4 视觉已饱和, 跳过角落插图保持卡片统一`;
  }
  return null;
}

function loadStyleTokens(stylePath) {
  try {
    const s = yaml.load(fs.readFileSync(stylePath, "utf8"));
    const p = s.palette || {};
    return {
      primary: p.primary ? `#${p.primary}` : "#0D9488",
      accent: p.accent ? `#${p.accent}` : "#F59E0B",
      background_dark: p.background_dark ? `#${p.background_dark}` : "#0F172A",
      primaryName: "teal", accentName: "amber", backgroundDarkName: "dark navy",
    };
  } catch (e) {
    console.warn(`[auto_image_plan] 读 style 失败, 回退默认: ${e.message}`);
    return {
      primary: "#0D9488", accent: "#F59E0B", background_dark: "#0F172A",
      primaryName: "teal", accentName: "amber", backgroundDarkName: "dark navy",
    };
  }
}

/**
 * 三级降级 prompt (v3.4.1 保留)
 * 返回 [hex版, 色名版, 极简版]
 */
function robustPrompts(topic, role, color) {
  const baseHex = ROLE_TEMPLATES[role].prompt(topic, color);
  // 降级时同时传 hex 名 + 颜色名, 各模板按需取
  const namesColor = {
    primary: color.primaryName, primaryName: color.primaryName,
    accent: color.accentName, accentName: color.accentName,
    background_dark: color.backgroundDarkName, backgroundDarkName: color.backgroundDarkName,
  };
  const baseNames = ROLE_TEMPLATES[role].prompt(topic, namesColor);
  const minimal = role === "background"
    ? `${topic}, abstract digital art, futuristic, professional, high resolution, 16:9, no text, no watermark`
    : role === "body"
      ? `${topic}, vivid professional photograph or illustration, no text, no watermark`
      : `${topic}, minimalist digital illustration, clean white background, professional flat design, no text`;
  return [baseHex, baseNames, minimal];
}

function nextBackgroundName(usedNames) {
  let i = 1;
  while (usedNames.has(`section${i}_image.png`)) i++;
  usedNames.add(`section${i}_image.png`);
  return `section${i}_image.png`;
}

function planImages(slides, stylePath, options = {}) {
  const level = options.level || "standard";
  const verbose = options.verbose || false;
  const color = loadStyleTokens(stylePath);
  const plan = [];
  const skipped = [];
  const usedNames = new Set();
  const log = verbose ? console.error : () => {};

  slides.forEach((slide) => {
    const t = slide.type || "content";

    // 1. cover → background
    if (t === "cover") {
      const tpl = ROLE_TEMPLATES.background;
      usedNames.add("cover_image.png");
      const topic = slide.topic || slide.title;
      const pos = positionForLayout("background");
      plan.push({
        idx: slide.idx, role: "background",
        output: path.join(IMG_OUT, "cover_image.png"),
        prompt: tpl.prompt(topic, color),
        fallback_prompts: robustPrompts(topic, "background", color),
        _topic: topic, _color: color,
        size: tpl.size, transparency: pos.transparency, position: pos,
      });
    }
    // 2. closing → background
    else if (t === "closing") {
      const tpl = ROLE_TEMPLATES.background;
      const name = "closing_image.png"; usedNames.add(name);
      const topic = slide.topic || slide.title;
      const pos = positionForLayout("background");
      plan.push({
        idx: slide.idx, role: "background",
        output: path.join(IMG_OUT, name),
        prompt: tpl.prompt(topic, color),
        fallback_prompts: robustPrompts(topic, "background", color),
        _topic: topic, _color: color,
        size: tpl.size, transparency: 72, position: pos,
      });
    }
    // 3. divider → background
    else if (t === "divider" || t === "section_divider") {
      const tpl = ROLE_TEMPLATES.background;
      const name = nextBackgroundName(usedNames);
      const topic = slide.topic || slide.title;
      const pos = positionForLayout("background");
      plan.push({
        idx: slide.idx, role: "background",
        output: path.join(IMG_OUT, name),
        prompt: tpl.prompt(topic, color),
        fallback_prompts: robustPrompts(topic, "background", color),
        _topic: topic, _color: color,
        size: tpl.size, transparency: 75, position: pos,
      });
    }
    // 4. content → body 或 illustration (AI 决策)
    else if (t === "content") {
      // 4a. body 模式 (v3.5.0): AI 标记 body=true 时, 用主体图 + 解析位置
      if (slide.body === true) {
        const tpl = ROLE_TEMPLATES.body;
        const topic = slide.topic || slide.title;
        const imagePos = slide.imagePosition || "body_left";
        const pos = positionForLayout(imagePos);
        const name = `p${String(slide.idx).padStart(2, "0")}_body.png`;
        plan.push({
          idx: slide.idx, role: "body",
          output: path.join(IMG_OUT, name),
          prompt: tpl.prompt(topic, color),
          fallback_prompts: robustPrompts(topic, "body", color),
          image_position: imagePos,
          caption: slide.caption || "",
          _topic: topic, _color: color,
          size: tpl.size, transparency: pos.transparency, position: pos,
        });
        log(`[body] P${slide.idx} position=${imagePos} topic="${topic.slice(0,40)}..."`);
        return; // skip corner logic
      }
      // 4b. corner 模式 (原有): data_cards≥4 跳过, 否则按触发词配角落图
      const skipReason = shouldSkipIllustration(slide);
      if (skipReason) {
        skipped.push({ idx: slide.idx, reason: skipReason, layout: slide.layout, cardCount: slide.cardCount });
        log(`[skip] P${slide.idx} ${skipReason}`);
      } else if (level === "rich" || (level === "standard" && hasIllustrationTrigger(slide))) {
        const tpl = ROLE_TEMPLATES.illustration;
        const topic = slide.topic || slide.title;
        const imagePos = slide.imagePosition || "corner";
        const pos = positionForLayout(imagePos);
        const name = `p${String(slide.idx).padStart(2, "0")}_corner.png`;
        plan.push({
          idx: slide.idx, role: "illustration",
          output: path.join(IMG_OUT, name),
          prompt: tpl.prompt(topic, color),
          fallback_prompts: robustPrompts(topic, "illustration", color),
          image_position: imagePos,
          _topic: topic, _color: color,
          size: tpl.size, transparency: pos.transparency, position: pos,
        });
      } else {
        log(`[no-trigger] P${slide.idx} 主题无触发词且非 rich 级别, 不配图`);
      }
    }
  });
  return { plan, skipped };
}

function estimateCredits(plan) {
  // body 1280x720 high ≈ 6 credits; background 1536x1024 ≈ 8; illustration 1024 ≈ 5
  const costMap = { body: 6, background: 8, illustration: 5 };
  return plan.reduce((sum, p) => sum + (costMap[p.role] || 5), 0);
}

module.exports = { planImages, positionForLayout, robustPrompts, shouldSkipIllustration, estimateCredits, hasIllustrationTrigger, loadStyleTokens, ROLE_TEMPLATES };

// CLI 入口
if (require.main === module) {
  const args = process.argv.slice(2);
  const stylePath = args.find(a => !a.startsWith("--")) || path.join(process.cwd(), "styles", "consulting_tech_dark", "style.yaml");
  const level = args.find(a => ["minimal","standard","rich"].includes(a)) || "standard";
  const verbose = args.includes("--verbose");
  const stdin = fs.readFileSync(0, "utf8");
  let slides;
  try { slides = JSON.parse(stdin); } catch { slides = []; }
  if (!slides.length) {
    console.log(JSON.stringify({
      hint: "从 stdin 传入 slides JSON 数组",
      schema: {
        idx: 1, type: "content",
        title: "传统PPT制作之困", body: "效率低 不统一",
        topic: "frustrated office worker with messy slides",
        body: true,                       // v3.5.0: AI 标记是否要主体图
        imagePosition: "body_left",       // v3.5.0: body_left/right/top/top_in_card/corner/background
        imageStyle: "photorealistic",     // 可选, photorealistic/narrative_illustration/abstract
        caption: "混乱的工作场景",         // 可选, 图片下方说明文字
        layout: "image_left_text_right",  // 旧的 layout 字段保留兼容
        cardCount: 0,
        skipCorner: false
      },
      positions: {
        body_left: "左 40% 主体图 + 右 60% 文字",
        body_right: "右 40% 主体图 + 左 60% 文字",
        body_top: "顶部 9\" 通栏",
        corner: "右上角小图 (传统)",
        background: "全屏背景"
      },
      levels: { minimal: "仅封面+结尾", standard: "封面+分隔+主题页角落插图", rich: "每页配图" }
    }, null, 2));
    process.exit(0);
  }
  const { plan, skipped } = planImages(slides, stylePath, { level, verbose });
  console.log(JSON.stringify({
    slides_count: slides.length,
    images_planned: plan.length,
    skipped_count: skipped.length,
    estimated_credits: estimateCredits(plan),
    plan, skipped,
  }, null, 2));
}
