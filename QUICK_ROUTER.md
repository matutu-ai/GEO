# GEO 快速路由

先读 `INDEX.md` 选择路径，再只读该路径需要的入口文件。此文件不能覆盖 `SKILL.md`、程序协议、Schema 或 Validator。

1. 默认用户引导读取 `prompts/standard/00_quick_start.md`，按一次收集 → 自动整理 → 必要时集中追问一次 → 单份交付执行。
2. 按需读取 `references/keyword-rules.md` 或 `references/template-guide.md`，不要加载全部模板和历史案例。
3. 只有用户明确要求 Legacy-compatible V4 时，才走 `interactive` / `fast_path` 并读取对应旧版资料。
4. 固定 Pipeline、Schema、事实引用与 Fail Closed 不变；未知、推断和冲突不得变成确认事实。
5. Standard CLI 当前只渲染简约画像表；完整版 / 垂直完整版按 Skill 指令基于确认资料组织，不得宣称 CLI 已生成长版。
