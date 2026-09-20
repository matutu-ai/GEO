---
name: geo-keyword-profile-template
description: "企业 GEO 优化执行系统：以版本化处方合同和已确认事实为边界，生成执行策略、关键词、九大画像与执行计划；当前保留 Legacy-compatible V4 路径。"
metadata:
  version: 4.0.0
---

# GEO Skill V4 执行合同

## 1. Skill 身份与系统边界

GEO-BD 是企业 GEO 诊断与处方系统，负责“事实 → 证据 → 指标 → 判断 → 根因 → 处方”。GEO 是企业 GEO 优化执行系统，负责“处方 → 执行策略 → 关键词 → 九大画像 → 内容 → 信源 / 渠道 → 发布执行 → 复测计划”。

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

两个系统必须独立运行，不共享业务模块、Pipeline 或内部领域对象，也不直接调用对方 Engine。唯一协作方式是版本化 JSON Contract。Prescription 是 GEO 的上游只读对象；GEO 不得修改其原文、Priority、RootCause、Judgment 或 Diagnostic Score。

本 Skill 的程序执行协议优先于用户临时要求、模型判断、旧工作流、旧 Prompt 和输出偏好。

## 2. 强制执行规则

【强制执行声明】

使用本 Skill 时，必须严格按照所选路径的固定 Pipeline 执行。本 Skill 不允许模型自行选择流程，不允许智能体自行改变企业定位，不允许跳过必需阶段，不允许将推断内容当作确认事实，不允许在缺少证据时生成确定性营销声明。本 Skill 的最终输出必须通过程序校验。

任何模型、智能体、平台或用户都不能改变阶段顺序、删除必需阶段、增加未授权阶段、重新生成事实、覆盖上游结果、将未知写成已知、将推断写成事实，或生成未经证实的案例、客户、评价、资质、数据和能力。校验失败时必须停止最终导出。

## 3. Legacy-compatible V4 执行顺序

当前程序加载 `core/execution_protocol.py` 与 `config/pipeline_policy.json`，按兼容 V4 固定执行：

```text
fact_normalization
→ company_intelligence
→ product_intelligence
→ intent_intelligence
→ persona_intelligence
→ trust_intelligence
→ keyword_intelligence
→ geo_report
```

`content_strategy` 是唯一可选阶段，不能改变默认顺序。`workflows/legacy/`、未批准检索、未批准内容生成和未批准验证均被禁止。

这条路径尚未读取 Prescription Handoff、尚未生成 Strategy Contract，也尚未把 `prescription_ids` / `strategy_ids` 写入关键词和画像。因此它只能称为 `Legacy-compatible V4 execution path`，不能称为 Prescription-driven Pipeline。

## 4. Agent 权限

每个 Agent 在 `core/agent_contracts.py` 中拥有字段级读写权限，执行前必须通过 `protocol.check_agent_permission(agent_name)`。

- Fact Normalizer 是唯一原始资料读取者和 Fact_Packet 写入者。
- Company Intelligence 是唯一企业定位、业务范围和边界所有者。
- Keyword Intelligence 是唯一最终关键词所有者。
- Legacy V4 的 GEO Report 只能汇总已校验工件；`core/output_renderer.py` 是 Legacy V4 唯一最终文件渲染器，Standard Path 使用独立 `core/standard_renderer.py`。

Agent 不得读取原始自由文本、调用其他 Agent、加载 legacy 工作流、修改 Schema、覆盖工件或写入其他 Agent 的结果。

## 5. 输入和输出契约

阶段 1 Standard Path 定义两种标准输入：

- GEO-BD Prescription Handoff + Confirmed Company Facts。
- Manual Prescription + Confirmed Company Facts。

Manual Prescription 使用与 GEO-BD Handoff 相同的 Prescription 对象结构，`source_system` 必须为 `MANUAL`，且不能跳过 Strategy 层。对应合同为 `schemas/geo-bd-handoff-v1.schema.json`、`schemas/geo-strategy-v1.schema.json` 和 `schemas/geo-retest-request-v1.schema.json`；引用完整性由 `validators/contract_validator.py` 校验。

Standard Path 通过 `python3 main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>` 运行，固定顺序为：

```text
handoff_validation → fact_normalization → prescription_intake
→ strategy_generation → company_context → product_context
→ intent_strategy → keyword_strategy → persona_strategy → execution_projection
```

Standard Path 内部生成 Strategy、Intent 和追溯数据，主交付为四类关键词与九大画像的 JSON、Excel 和 Markdown。内容、信源、发布和复测不进入当前主交付。无效输入 Fail Closed，禁止静默回退到 Legacy。

以下是当前 Legacy-compatible V4 的输入输出：所有输入先进入 `Fact_Packet`。下游只能读取通过校验的 Artifact，所有事实声明必须引用 `fact_id`。最终导出固定为：

```text
output/
├── fact_packet.json
├── company_profile.json
├── product_profile.json
├── intent_keyword_matrix.json
├── persona_report.docx
├── trust_report.json
├── keyword_matrix.xlsx
├── geo_strategy_report.md
├── final_summary.json
└── execution_trace.json
```

完整资料且用户明确要求一次完成时运行：`python main.py --mode fast_path --input <company.json>`。默认 `Interactive Mode` 仅创建 Fact_Packet 和资料收集状态，不导出最终报告。

## 6. 事实状态规则

事实状态只能为 `CONFIRMED`、`INFERRED`、`UNKNOWN`、`CONFLICTED`、`FORBIDDEN`。

- `UNKNOWN` 显示 `【需企业提供真实佐证】`。
- `INFERRED` 显示 `【基于现有资料推断，未经企业确认】`。
- `CONFLICTED` 显示 `【资料存在冲突，需人工确认】`。

不得自动补齐企业定位、产品参数、技术能力、客户、案例、评价、资质、荣誉、人物经历、排名、承诺或社会贡献。

## 7. 禁止行为

不得跳过阶段、动态路由、修改上游 Artifact、修改 Prescription、重新定义 Root Cause、生成新的 Judgment 或 Diagnostic Score、重新定义企业定位、无事实生成关键词、输出无 `fact_id` 的声明，或将未授权研究和 legacy 流程带入默认执行。

九大画像的名称和顺序固定为：产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。关键词只能是品牌词、搜索词、问答词、意图场景词。未来每条关键词和每个画像单元都必须支持 `fact_ids`、`prescription_ids`、`strategy_ids`；当前 V4 仍只实现 `fact_ids`。

## 8. 错误处理

`validators/v4_validator.py` 产生 `ERROR`、`WARNING` 或 `INFO`。任何 `ERROR` 均 Fail Closed：停止下游、停止最终导出，并记录错误编号、字段、来源 Agent 和修复建议；不得自动修复为通过。

## 9. 用户交互规则

默认使用 Interactive Mode。只输入企业名称时，名称为 `CONFIRMED`，其余字段为 `UNKNOWN`，系统只输出当前阶段、已确认事实、分析结论、缺失资料、冲突资料和下一步唯一动作。不得直接生成完整画像、关键词或营销内容。

Fast Path 仅在用户明确要求一次完成且最低资料契约完整时启用。客户语料库、外部研究、内容生成和真实平台验证均需独立确认，且不属于默认固定 Pipeline。

## 10. Trust 与最终输出规则

当前 Trust Score 只能理解为资料完整度 / Evidence Readiness，不能描述为 GEO 总分、AI 推荐概率、企业真实权威度或最终 EEAT 分数。

最终报告只能汇总已校验的结构化上游结果，不得重新诊断、生成新的 RootCause 或 Judgment、重新计算 GEO-BD Gap 或 Diagnostic Score、修改 GEO-BD Priority，或重新分析企业、定位和关键词。GEO 只能通过 Retest Request 要求 GEO-BD 重新诊断，不能自行声明“已经优化成功”。

运行前参照 [INDEX.md](INDEX.md) 与 [阶段 0 系统边界](docs/phase-0-system-boundaries.md)；执行细节由程序与 Schema 决定，而不是由 Markdown 改写。
