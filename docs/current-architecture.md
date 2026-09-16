# GEO V4 固定执行架构

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
- `core/output_renderer.py` 是唯一最终文件输出者。

默认 Interactive Mode 在 Fact_Packet 后暂停；完整资料且明确请求才会走 Fast Path。旧流程被隔离到 `workflows/legacy/` 和 `prompts/legacy/`，策略文件禁用其自动执行。
