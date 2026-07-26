# uploads/ — 用户 PPT 模版上传目录

把你自己收集的 PPT 模版（`.pptx`）放进这个目录，技能可以批量提取它们的视觉风格，生成风格样例保存到 `styles/`，之后生成 PPT 时即可按风格名/关键词选用。

## 用法

### 批量提取（整个目录）

```bash
python3 tools/style_extractor.py --batch
# 扫描 uploads/*.pptx，逐个提取 → styles/<风格ID>/style.yaml + 登记 registry.yaml
```

### 指定目录 / 覆盖已存在风格

```bash
python3 tools/style_extractor.py --batch uploads/ --force
```

### 单个文件精细提取（推荐重要模版使用）

```bash
python3 tools/style_extractor.py uploads/央企汇报模版.pptx \
    --name soe_corp_blue --keywords "央企,蓝色,商务"
```

## 命名规则

- 批量模式下风格 ID 由文件名自动转为 snake_case（如 `Blue-Corp-2024.pptx` → `blue_corp_2024`）
- 中文文件名无法自动转写时，命名为 `style_001`、`style_002`…，并把原文件名写入 `keywords` 便于匹配
- 想精确控制风格 ID 和关键词时，请用单文件模式 `--name` / `--keywords`

## 注意

- 本目录只放源模版，提取产物在 `styles/`，两者互不影响
- 删除本目录的模版不会删除已入库的风格样例；如需移除风格，删 `styles/<风格ID>/` 并在 `styles/registry.yaml` 去掉对应条目
- `.DS_Store` 等系统文件会被自动忽略
