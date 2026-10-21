# GEO 快速路由

1. 默认读取 `prompts/standard/00_quick_start.md`，一次收集五项核心资料。
2. 需要选词时读取 `references/keyword-rules.md`；需要画像时读取 `references/template-guide.md`。
3. Standard 只输出一份 Markdown：完整模式、仅词模式或仅画像模式。
4. 画像默认简约版；完整版固定九项每项 800–1000 字。垂直业务只限定一个已确认主营业务。
5. 只有用户明确指定旧版 V4 时，才读取 `prompts/legacy/` 与 `workflows/legacy/`。
6. 未确认事实标待补；无效输入 Fail Closed，不回退 Legacy。
