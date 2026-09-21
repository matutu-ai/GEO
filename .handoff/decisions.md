# Confirmed Decisions

- GEO-BD 与 GEO 仅通过版本化 JSON Contract 交换数据，不共享代码、Pipeline 或内部领域对象。
- GEO-BD 负责诊断与处方；GEO 负责处方之后的执行策略与执行产物。
- Prescription 是 GEO 的上游只读对象，Strategy 必须引用已存在的 Prescription。
- 当前 V4 保持不变，并标记为 Legacy-compatible V4 execution path，而不是 Prescription-driven Pipeline。
- 阶段 0 已验收。阶段 1 新增独立 Prescription-driven Standard Path，不覆盖 Legacy-compatible V4。
- Standard Path 无效输入必须 Fail Closed，禁止静默回退到 Legacy Fast Path。
- 阶段 1 不修改 GEO-BD，不进入阶段 2。
- 用户最终交付目标是关键词和九大画像；Standard Path 主交付固定为 `keyword_matrix.xlsx`、`persona_report.md`、`keyword_matrix.json`、`persona_plan.json`。
- 内容、信源、发布和复测保留为内部边界，不进入当前主交付。
- 九大画像采用 Markdown 人类交付，避免运行环境中文 DOCX 字体依赖；Legacy V4 的既有 DOCX 输出保持不变。
- Standard Path 互动顺序收敛为：初版导出 → 先确认四类关键词 → 确认用户决策画像 → 确认企业九大画像 → 选择后续技能；系统推荐词仅作参考，不自动视为已批准。
