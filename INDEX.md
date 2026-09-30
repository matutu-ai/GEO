# GEO 当前规则索引

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

| 目标 | 唯一入口 | 边界 / 结果 |
| --- | --- | --- |
| 了解系统职责 | `README.md`、`docs/phase-0-system-boundaries.md` | 诊断与执行分离，只允许 JSON 数据协作 |
| 接收 GEO-BD 处方 | `schemas/geo-bd-handoff-v1.schema.json` | `source_system=GEO-BD`，Prescription 只读 |
| 接收人工处方 | 同一 Schema 的 `$defs.manualPrescriptionInput` | `source_system=MANUAL`，Prescription 对象结构相同 |
| 生成 GEO Strategy | `schemas/geo-strategy-v1.schema.json` | 每个 Strategy 引用至少一个已存在的 Prescription |
| 请求 GEO-BD 复测 | `schemas/geo-retest-request-v1.schema.json` | 只表达复测目标，不携带成功结论或新诊断 |
| 校验 Contract | `validators/contract_validator.py` | Schema 校验、Prescription ID 唯一、引用存在 |
| Prescription-driven Standard Path | `python3 main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>` | Handoff → Facts → Strategy → Intent → Keyword → Persona → Execution |
| Standard Path 运行顺序 | `workflows/standard_path.md`、`core/standard_pipeline.py` | 12 个固定阶段，不回退 Legacy |
| 用户交互唯一入口 | `prompts/standard/00_quick_start.md` | 一次收集资料与版本；必要时只集中追问一次 |
| 四类关键词规则 | `references/keyword-rules.md` | 品牌词、搜索词、问答词、意图场景词 |
| 九大画像与长短版 | `references/template-guide.md` | 简约版、完整版、垂直完整版；九项固定 |
| Standard Path 输出 | `GEO训练与运营词画像.md` | 一份文件：四类词、九大画像、下一步建议 |
| Legacy V4 旧模式 | 用户明确指定时使用 `interactive` / `fast_path` | 旧版兼容运行，不作为默认用户引导 |
| 检查旧 V4 协议和权限 | `core/execution_protocol.py`、`core/agent_contracts.py` | 固定顺序、字段级权限、Fail Closed |
| 旧版兼容资料 | `workflows/legacy/`、`prompts/legacy/` | 仅按需兼容旧路径；禁止与 Standard 混用 |

使用原则：默认只读 `SKILL.md`、Standard 快速启动及当前任务直接相关的一份规则；不要批量读取 Legacy、所有模板或历史案例。

Legacy-compatible V4 仍不读取 Prescription Handoff；只有 `standard` 模式是关键词与九大画像主路径。两条路径逻辑隔离，Standard 输入无效时不得回退到 Legacy。
