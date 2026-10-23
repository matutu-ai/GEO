# GEO 快速路由

1. 默认读取 `templates/delivery.md` 和 `prompts/standard/00_quick_start.md`，固定交付格式并一次收集五项核心资料。
2. 需要选词时读取 `references/keyword-rules.md`；需要画像时读取 `references/template-guide.md`。
3. 首轮仅词模式，固定两列推荐词、短词根。等用户一次选词并选择画像范围后，进入仅画像模式；完整模式仅用于选定后明确要求合并导出。每轮只输出一份 Markdown。
4. 画像默认完整版，固定九项每项 800–1000 字；简约版仅明确要求时使用。品牌画像与指定业务画像二选一，不默认同时出两套。
5. 只有用户明确指定旧版 V4 时，才读取 `prompts/legacy/` 与 `workflows/legacy/`。
6. 未确认事实标待补；无效输入 Fail Closed，不回退 Legacy。
7. 在其他 AI 中使用时，先按 `references/cross-ai-usage.md` 提供完整 Skill 包并加载相关规则；不要只复制启动提示词后假设所有细则都已生效。
