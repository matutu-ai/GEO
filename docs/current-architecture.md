# GEO 当前架构

本仓库保留两条隔离运行路径。用户默认交互规则只有一套：一次收集资料与交付版本，自动处理，关键问题最多集中追问一次，然后输出一份结果和一条下一步建议。Legacy 只在用户明确指定时启用。

## Standard Path（当前主路径）

```text
GEO-BD Handoff / Manual Prescription + Confirmed Company Facts
→ 固定 12 阶段 Pipeline
→ 校验引用和执行契约
→ 单份 GEO训练与运营词画像.md
```

Standard 输出四类关键词及其训练用途、固定九大画像及其运营价值、事实状态和下一步建议。内容、信源建设、发布和真实平台验证不属于默认主交付。

用户可选择简约版、完整版或垂直完整版。CLI 当前固定生成精简画像表；完整版由 Skill 基于确认的资料与校验结果组织，每项画像目标 800–1000 个中文字。不得将 CLI 精简表误称为完整版。

## Legacy-compatible V4

保留现有 `interactive` / `fast_path`、协议、Schema 和输出以维持兼容。相关文件位于 `workflows/legacy/` 与 `prompts/legacy/`，不属于 Standard 的默认读取范围。

## 核心保护

- `core/standard_pipeline.py` 固定 Standard 阶段；无效输入 Fail Closed，不回退 Legacy。
- `core/agent_contracts.py`、`core/artifact_store.py` 和 validators 继续保障字段权限、事实状态、来源追溯和合同一致性。
- GEO-BD 与 GEO 仅交换版本化 JSON；Prescription 在 GEO 内只读。
- 用户不需要重复检查每个词或画像；程序仍执行一次确定性合同校验，阻止无效结果导出。
