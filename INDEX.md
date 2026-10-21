# GEO 当前入口

| 任务 | 唯一入口 | 结果 |
| --- | --- | --- |
| 运行当前主流程 | `python3 main.py --handoff <handoff.json> --input <company.json> --output <dir>` | 一份四类关键词与九大画像 |
| 用户快速启动 | `prompts/standard/00_quick_start.md` | 一次收集，必要时集中追问一次 |
| 关键词规则 | `references/keyword-rules.md` | 四类词、来源和地区边界 |
| 画像规则 | `references/template-guide.md` | 九大画像、简约/完整版、垂直范围 |
| 文章训练约束 | `references/article-training.md` | 一文一业务线、一角色、一意向阶段 |
| GEO-BD 输入 | `schemas/geo-bd-handoff-v1.schema.json` | Prescription 只读 |
| Standard 执行 | `core/standard_pipeline.py`、`core/standard_renderer.py` | 校验后导出一份 Markdown |
| Legacy V4 | 显式使用 `--mode interactive` 或 `--mode fast_path` | 仅兼容旧流程 |

默认只读取 `SKILL.md` 和当前任务对应的一份规则。不要把 Legacy 提示、客户历史案例或内容规划载入 Standard。
