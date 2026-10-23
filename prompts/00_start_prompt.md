# GEO Skill 启动提示

默认使用 `prompts/standard/00_quick_start.md`：一次收集企业、产品/服务、定位、目标客户和使用场景；先推荐四类词，用户选定词和画像范围后再生成九大画像。画像默认完整版，每项800–1000字。画像交付后给出词包训练篇数和纯文本选项提示，不自动进入文章生成。

仅在主体、业务、政策或对外事实存在关键缺失/冲突时，读取 `prompts/standard/01_evidence_confirmation.md`，将必要问题合并为一次追问。禁止逐阶段、逐词和逐画像反复确认。

`interactive` / `fast_path`、`prompts/legacy/` 与 `workflows/legacy/` 仅在用户明确指定旧版 V4 时使用。Standard Path 固定执行顺序与事实校验不变。
