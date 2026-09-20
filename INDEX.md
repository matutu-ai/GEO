# GEO 关键词与九大画像执行索引

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
| Prescription-driven Standard Path | `python3 main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>` | Handoff → Facts → Strategy → Intent → Keyword → Persona → Execution → Retest |
| Standard Path 运行顺序 | `workflows/standard_path.md` | 10 个固定阶段，不回退 Legacy |
| Standard Path 输出 | `keyword_matrix.xlsx`、`persona_report.md`、`keyword_matrix.json`、`persona_plan.json` | 关键词与九大画像主交付 |
| 资料不足或只给企业名称 | `python3 main.py --mode interactive` | Legacy-compatible V4：Fact Packet 后暂停 |
| 资料完整且明确一次完成 | `python3 main.py --mode fast_path --input <company.json>` | Legacy-compatible V4：现有 10 份输出 |
| 检查旧 V4 协议和权限 | `core/execution_protocol.py`、`core/agent_contracts.py` | 固定顺序、字段级权限、Fail Closed |
| 了解历史资料 | `workflows/legacy/`、`prompts/legacy/` | 仅供人工参考，不自动执行 |

Legacy-compatible V4 仍不读取 Prescription Handoff；只有 `standard` 模式是关键词与九大画像主路径。两条路径逻辑隔离，Standard 输入无效时不得回退到 Legacy。
