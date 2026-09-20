# GEO 关键词与九大画像架构

本页同时记录 Legacy-compatible V4 和 Prescription-driven Standard Path。阶段 0 的系统边界和 JSON Contract 见 `docs/phase-0-system-boundaries.md`。

主路径 Standard Path：

```text
Handoff → Confirmed Facts → Prescription Intake → Strategy
→ Company/Product Context → Intent → Keyword / Persona
→ Excel / Markdown Delivery
```

```text
Raw Input
→ Fact_Packet
→ Company_Profile
→ Product_Profile
→ Intent_Keyword_Matrix
→ Nine_Personas
→ Trust_Report
→ Keyword_Matrix
→ GEO_Report
→ Output Renderer
```

- `core/execution_protocol.py` 固定阶段、禁止阶段与 Fail Closed 规则，并加载 `config/pipeline_policy.json`。
- `core/agent_contracts.py` 规定字段级读写所有权；Company Intelligence、Keyword Intelligence、GEO Report 分别是定位、关键词和报告的唯一所有者。
- `core/artifact_store.py` 只向下游暴露已校验且不可覆盖的 Artifact。
- `validators/v4_validator.py` 校验事实状态、可追溯性、九大画像、关键词和执行顺序。
- Legacy V4 由 `core/output_renderer.py` 输出；Standard Path 由独立 `core/standard_renderer.py` 输出关键词 Excel 和九大画像 Markdown，同时保留 JSON 机器产物。

默认 Interactive Mode 在 Fact_Packet 后暂停；完整资料且明确请求才会走 Fast Path。旧流程被隔离到 `workflows/legacy/` 和 `prompts/legacy/`，策略文件禁用其自动执行。

Legacy 路径仍不读取 Prescription Handoff，也不生成 Standard Strategy。Standard Path 的关键词和画像均包含 `fact_ids`、`prescription_ids`、`strategy_ids`；内容、信源、发布和复测保留为内部边界，不进入当前主交付。
