# Confirmed Decisions

- GEO-BD 与 GEO 仅通过版本化 JSON Contract 交换数据，不共享代码、Pipeline 或内部领域对象。
- GEO-BD 负责诊断与处方；GEO 负责处方之后的执行策略与执行产物。
- Prescription 是 GEO 的上游只读对象，Strategy 必须引用已存在的 Prescription。
- 当前 V4 保持不变，并标记为 Legacy-compatible V4 execution path，而不是 Prescription-driven Pipeline。
- 阶段 0 已验收。阶段 1 新增独立 Prescription-driven Standard Path，不覆盖 Legacy-compatible V4。
- Standard Path 无效输入必须 Fail Closed，禁止静默回退到 Legacy Fast Path。
- 阶段 1 不修改 GEO-BD，不进入阶段 2。
- 用户最终交付目标是简洁、可直接用于下一步 GEO 训练与运营的四类关键词和九大画像；Standard Path 默认只导出 `GEO训练与运营词画像.md`，标明每类词的训练用途、每个画像的运营价值及确认状态，结构化产物在运行时校验。
- 内容、信源、发布和复测保留为内部边界，不进入当前主交付。
- 九大画像采用 Markdown 人类交付，避免运行环境中文 DOCX 字体依赖；Legacy V4 的既有 DOCX 输出保持不变。
- Standard Path 直接导出一份训练运营建议稿；未确认词与缺失事实保留状态，不要求逐词填写选择表，也不把建议词冒充已批准词。
- Standard 用户流程采用一次资料收集 → 自动处理 → 关键事实必要时集中追问一次 → 单份交付与一条下一步建议；不逐阶段、逐词或逐画像确认。
- 交付版本固定为简约版、完整版或垂直完整版；简约画像每项描述核心事实，完整版每项目标 800–1000 个中文字；垂直版限定单一业务。事实不足时待补，不凑字数。
- Standard CLI 当前只渲染简约画像表；`delivery_mode` 是交付偏好元数据，不能宣称 CLI 已实现完整版正文。Skill 组织长版时必须以确认资料和校验事实为依据。
- 为避免旧资料覆盖新流程，Legacy-compatible V4 代码和隔离资料保留但不进入 Standard 默认读取；删除的仅是无引用的过时 GEO/质量评分规则与含虚构数字的画像示例。
- 指导产物只保留一个已完成状态、一个下一步运营动作和一个相关技能建议；内部合同校验保留，不转化为多轮用户确认。
