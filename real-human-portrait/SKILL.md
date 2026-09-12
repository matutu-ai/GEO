---
name: real-human-portrait
description: Generate or refine realistic human portrait prompts for image and video models, preserving natural skin texture, asymmetry, photographic limitations, and human imperfections. Use when a portrait looks plastic, over-retouched, overly symmetrical, or AI-generated; do not use for general illustration or beauty-retouching requests.
metadata:
  short-description: 真实人类感人像生成
  author: matutu-ai
  version: 1.0.0
---

# Real Human Portrait

用于生成像真实摄影机拍摄的人类肖像，降低 AI 完美脸、塑料皮肤、CG 感和商业精修感。

## 核心原则

- 真实性优先于完美：保留毛孔、细小绒毛、肤色不均、油脂、细纹、黑眼圈、眼袋、小痣和轻微不对称。
- 摄影限制要可见：使用 RAW、未修图、自然曝光、柔和阴影、适度胶片颗粒或真实 ISO 噪声；不要用 HDR 或过度饱和替代真实光线。
- 不把缺陷夸张成病态或脏污；缺陷应自然、轻微，并服务于人物可信度。
- 用户指定年龄、身份、族裔、发型、服装和场景时，保持这些设定不变，只补充真实质感。

## 禁用倾向

避免 `perfect skin`、`flawless face`、`perfect symmetry`、`beauty filter`、`skin retouching`、`wax skin`、`CGI skin` 等会强化塑料感的词。

## 工作流程

1. 明确人物、年龄范围、身份、表情、构图、场景和模型；缺少时只做最小合理假设。
2. 按“摄影基础 → 皮肤 → 五官 → 头发 → 光影 → 禁止项”组织提示词。
3. 根据模型适配参数：Midjourney 可使用 `--style raw`、适度 `--chaos 10-20`；Flux 强调 `raw photo`、`unretouched`；SDXL 通常从 CFG 5-7、30-50 steps 起步，具体以工作流为准。
4. 若用于视频首帧，读取 [prompts/seedance-video.md](prompts/seedance-video.md)，保持首帧身份一致，并只加入呼吸、眼神变化、微表情和轻微发丝移动。
5. 输出前按 [prompts/negative-prompts.md](prompts/negative-prompts.md) 检查负面词，并按 [schemas/portrait_prompt.schema.json](schemas/portrait_prompt.schema.json) 组织结构化结果（用户需要 JSON 时）。

## 标准控制句

中文：`不磨皮，不美颜，不精修，保留真实人类皮肤缺陷。`

英文：`no skin retouching, no beauty filter, keep natural human imperfections`

## 质量检查

- 是否能看到自然皮肤纹理，而不是均匀塑料表面？
- 是否有轻微、不夸张的左右不对称和表情变化？
- 眼神、虹膜高光、睫毛和眉毛是否具有真实细节？
- 头发是否存在自然碎发、散落发丝和可见发根？
- 光线、曝光、颗粒和景深是否像摄影结果？
- 是否避免美颜、磨皮、HDR、过度饱和和 CG 感？

## 支持文件

- 基础人像模板：[prompts/portrait-base.md](prompts/portrait-base.md)
- Hero 图模板：[prompts/hero-image.md](prompts/hero-image.md)
- Seedance 首帧与动态规则：[prompts/seedance-video.md](prompts/seedance-video.md)
- 负面提示词：[prompts/negative-prompts.md](prompts/negative-prompts.md)
