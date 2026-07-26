# PPT 风格样例库

按风格分目录维护的可复用 PPT 视觉规范库。技能生成 PPT 前先在这里选风格，避免硬编码配色。

## 目录结构

```
styles/
├── registry.yaml              # 风格注册表：名称/关键词/路径/回退策略
├── README.md                  # 本文件
├── _template/
│   └── style.yaml             # 新风格 schema 模板（字段说明全在里面）
├── consulting_tech_dark/      # 内置：咨询科技风（暗色）
│   └── style.yaml
└── green_professional/        # 内置：绿色专业风
    └── style.yaml
```

每个风格一个独立子目录，目录名即风格 ID（snake_case）。

## 如何选择风格（技能侧）

1. 读取 `registry.yaml`，取用户风格要求（自然语言关键词）与各风格 `keywords` 求命中数
2. 命中最多者胜；零命中用 `selection.fallback`（默认 `consulting_tech_dark`）
3. 加载 `styles/<name>/style.yaml`，使用其中的 `palette`（色板）、`fonts`（字体）、`layout`（布局规范）、`imagery`（配图规范）

## 如何新增风格

### 方式1：从用户上传的 PPT 模版提取（推荐）

```bash
python3 tools/style_extractor.py /path/to/用户模版.pptx \
    --name corporate_blue \
    --keywords "央企,蓝色,商务,正式"
```

提取器会自动：
- 解析主题色（theme XML accent1-6、深浅底色）
- 统计实际使用的文字色/填充色频次
- 提取字体（中英 major/minor）
- 统计图片密度、页面尺寸
- 生成 `styles/corporate_blue/style.yaml` 并登记到 `registry.yaml`

### 方式2：手工复制模板

复制 `_template/style.yaml` 到 `styles/<new_style>/style.yaml`，逐项填写后在 `registry.yaml` 的 `styles:` 下补一条记录。

## 维护原则

- 一个风格一个目录，风格之间不允许互相引用
- 色值统一 6 位 hex 大写、不带 `#` 前缀（对齐 PptxGenJS 约定）
- 提取自用户模版的风格，`source` 字段必须注明来源文件名
- 用户明确要求「和上次一样」时，优先复用已入库风格而不是重新提取
