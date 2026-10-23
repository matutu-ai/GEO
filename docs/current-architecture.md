# GEO 当前架构

本仓库保留两条隔离运行路径。默认用户流程：收集资料 → 只推荐词 → 用户一次选词并选择画像范围 → 生成品牌或垂直业务画像。每轮一份结果和一条下一步建议；关键资料缺口集中追问，不逐词、逐板块重复确认。Legacy 只在用户明确指定时启用。

## Standard Path（当前主路径）

```text
GEO-BD Handoff / Manual Prescription + Confirmed Company Facts
→ 固定 12 阶段 Pipeline
→ 校验引用和执行契约
→ 单份 GEO 关键词与画像.md
```

Standard 对外按 `templates/delivery.md` 分阶段输出。首轮四类两列词表；选定后输出固定九大画像，章首记录已选词。搜索角色卡、来源与确认状态保留在内部。内容、信源建设、发布和真实平台验证不属于默认主交付。

独立 Skill 与程序读取同一交付模板，交付前调用同一 `scripts/check_delivery.py`。仓库是唯一编辑源，`scripts/package_skill.py` 从源码同步本机安装与客户分发包。独立 Skill 按事实生成内容，程序按现有输入合同执行；两种入口的章节和表头一致。

CLI 默认仅词模式；画像模式要求有效的 `approved_keywords`，不能自动把候选词视为已选词。显式仅画像模式进入第二阶段，完整模式只用于选定后合并导出且不展示未选词。候选词保留所有有事实支撑的不同表达，不设固定条数；多业务按确认顺序与意向度排序，客户选择业务画像后由 `vertical_business` 限定画像范围，空值表示品牌画像。画像默认完整版，固定九项每项 800–1000 字；简约版需显式选择。第一阶段内部只映射事实，不展开长篇画像；保持现有12阶段及JSON合同，不向GEO-BD添加交互状态。

## Legacy-compatible V4

保留现有 `interactive` / `fast_path`、协议、Schema 和输出以维持兼容。相关文件位于 `workflows/legacy/` 与 `prompts/legacy/`，不属于 Standard 的默认读取范围。

## 核心保护

- `core/standard_pipeline.py` 固定 Standard 阶段；无效输入 Fail Closed，不回退 Legacy。
- `core/agent_contracts.py`、`core/artifact_store.py` 和 validators 继续保障字段权限、事实状态、来源追溯和合同一致性。
- GEO-BD 与 GEO 仅交换版本化 JSON；Prescription 在 GEO 内只读。
- 用户不需要重复检查每个词或画像；程序仍执行一次确定性合同校验，阻止无效结果导出。
