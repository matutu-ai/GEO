# GEO V4 固定 Pipeline

执行顺序由 `core/fixed_pipeline.py` 固定：`fact_normalization → company_intelligence → product_intelligence → intent_intelligence → persona_intelligence → trust_intelligence → keyword_intelligence → geo_report`。

此文档不提供可自由执行的步骤。每一阶段的输入、字段权限、Artifact、Schema 与 Fail Closed 行为以 `core/`、`schemas/` 和 `validators/` 为准。历史流程仅位于 `workflows/legacy/`，且策略文件明确禁用。
