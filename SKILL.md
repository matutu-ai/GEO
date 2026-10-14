---
name: geo-keyword-profile-template
description: "为企业从已确认资料和处方生成 GEO 六类词根、四类关键词、核心词根画像卡和九大画像时使用；默认只交付一份 Markdown。Legacy V4 仅在明确指定时使用。"
metadata:
  version: 4.0.0
---

# GEO 业务词根与画像

## 1. Skill 身份与系统边界

GEO-BD 是企业 GEO 诊断与处方系统，负责“事实 → 证据 → 指标 → 判断 → 根因 → 处方”。GEO 当前主线负责“处方与已确认事实 → 执行策略 → 四类关键词与九大画像 → GEO训练运营建议”；内容生产、发布和复测不属于当前主交付。

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

两个系统必须独立运行，不共享业务模块、Pipeline 或内部领域对象，也不直接调用对方 Engine。唯一协作方式是版本化 JSON Contract。Prescription 是 GEO 的上游只读对象；GEO 不得修改其原文、Priority、RootCause、Judgment 或 Diagnostic Score。

程序合同不能被提示词或模型判断绕过；若用户要求改变合同，应先修改程序、验证器和测试。

## 2. 强制执行规则

【强制执行声明】

使用本 Skill 时，必须严格按照所选路径的固定 Pipeline 执行。本 Skill 不允许模型自行选择流程，不允许智能体自行改变企业定位，不允许跳过必需阶段，不允许将推断内容当作确认事实，不允许在缺少证据时生成确定性营销声明。本 Skill 的最终输出必须通过程序校验。

任何模型、智能体、平台或用户都不能改变阶段顺序、删除必需阶段、增加未授权阶段、重新生成事实、覆盖上游结果、将未知写成已知、将推断写成事实，或生成未经证实的案例、客户、评价、资质、数据和能力。校验失败时必须停止最终导出。

Standard Path 的用户决策画像、交互提示和下一步技能建议与企业九大画像分开。默认完整模式；用户可选择完整模式、仅词模式或仅画像模式。必要时一次合并追问，不逐阶段、逐词或逐画像反复确认。最终只交付一份《GEO 业务词根与画像》和一条明确的下一步建议。

## 3. 路径选择与输入合同

默认走 `standard`；只有用户明确要求旧版 V4 时才走 `interactive` 或 `fast_path`。Legacy 的阶段、字段权限及输出由 [固定流程](workflows/fixed_pipeline.md)、`core/agent_contracts.py`、`core/output_renderer.py` 和相应 Schema 决定；Standard 使用独立 `core/standard_renderer.py`，无效输入不得回退 Legacy。不要默认读取 `prompts/legacy/`、`workflows/legacy/` 或旧模板。

阶段 1 Standard Path 定义两种标准输入：

- GEO-BD Prescription Handoff + Confirmed Company Facts。
- Manual Prescription + Confirmed Company Facts。

Manual Prescription 使用与 GEO-BD Handoff 相同的 Prescription 对象结构，`source_system` 必须为 `MANUAL`，且不能跳过 Strategy 层。对应合同为 `schemas/geo-bd-handoff-v1.schema.json`、`schemas/geo-strategy-v1.schema.json` 和 `schemas/geo-retest-request-v1.schema.json`；引用完整性由 `validators/contract_validator.py` 校验。

Standard Path 通过 `python3 main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>` 运行，严格按 `core/standard_pipeline.py` 的 12 个固定阶段执行：

```text
handoff_validation → fact_normalization → prescription_intake
→ strategy_generation → company_context → product_context
→ intent_strategy → keyword_strategy → persona_strategy → user_persona_strategy
→ guidance_projection → execution_projection
```

Standard Path 内部生成 Strategy、Intent 和追溯数据，只导出一份 `GEO 业务词根与画像.md`。完整模式含六类词根、四类关键词、核心词根画像卡和固定九大画像；仅词模式不含任何画像卡或画像正文；仅画像模式不含词根、关键词或组合说明。六类词根是品牌、业务、定位、人群、场景、需求根，以 2–8 字为主；长名称保留原文并请客户确认简称。每类最多 12 个推荐词。完整版画像只按确认资料扩写，缺项待补，不凑字数。垂直业务必须匹配已确认主营业务，未确认关联不得套用。关键词与画像合同仍在运行时校验；不另导出 JSON、Excel 或审计目录。内容、信源、发布和复测不进入当前主交付。无效输入 Fail Closed，禁止静默回退 Legacy。

## 4. 事实状态规则

事实状态只能为 `CONFIRMED`、`INFERRED`、`UNKNOWN`、`CONFLICTED`、`FORBIDDEN`。

- `UNKNOWN` 显示 `【需企业提供真实佐证】`。
- `INFERRED` 显示 `【基于现有资料推断，未经企业确认】`。
- `CONFLICTED` 显示 `【资料存在冲突，需人工确认】`。

不得自动补齐企业定位、产品参数、技术能力、客户、案例、评价、资质、荣誉、人物经历、排名、承诺或社会贡献。

## 5. 输出边界

不得跳过阶段、动态路由、修改上游 Artifact、修改 Prescription、重新定义 Root Cause、生成新的 Judgment 或 Diagnostic Score、重新定义企业定位、无事实生成关键词、输出无 `fact_id` 的声明，或将未授权研究和 legacy 流程带入默认执行。

九大画像的名称和顺序固定为：产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。用户决策画像独立记录人群、场景、痛点、决策标准、决策阶段和典型问题。关键词只能是品牌词、搜索词、问答词、意图场景词，并额外区分 `CLIENT_REQUESTED` / `SYSTEM_RECOMMENDED` 来源和推荐/待确认状态。系统建议是候选表达，不是实测搜索词；默认不做外部搜索或抓词，外部词源研究必须由用户明确要求并记录来源和日期。搜索词侧重场景中找服务，问答词侧重比较/判断/选择，意图场景词侧重明确任务与需求。每条关键词、用户画像和企业画像单元都必须支持 `fact_ids`、`prescription_ids`、`strategy_ids`；当前 V4 仍只实现 `fact_ids`。

校验错误必须 Fail Closed，不得自动修复为通过或改走 Legacy。Trust Score 只能解释为资料完整度 / Evidence Readiness，不是 GEO 总分、AI 推荐概率或权威度。最终报告不得重新诊断、改写上游 Priority 或宣布“已优化成功”；GEO 只能通过 Retest Request 请求 GEO-BD 复测。

## 6. 用户交互规则

Standard 默认采用一次收集、自动生成、必要时一次集中追问的交互：企业/品牌及主营业务、产品/服务、定位、目标客户、使用场景。可选提供关键词、地区和输出模式。若上述五类核心资料缺失，合并询问缺项；其他未知内容标待补，不启动反复确认循环。

若只收到企业名或官网，可先整理公开资料，但只能标为 `INFERRED` 并一次性请企业核实五项必需事实；未确认前不得将其输入要求 `CONFIRMED` 的 Standard CLI，也不得发布为定稿事实。

输出模式：
- `完整模式`（默认）：六类词根、四类关键词、核心词根画像卡、固定九大画像。
- `仅词模式`：只输出资料摘要、六类词根和四类关键词，不输出任何画像内容。
- `仅画像模式`：只输出资料摘要和固定九大画像，不输出词根、关键词或组合解释。

九大画像固定顺序和事实规则见 `references/template-guide.md`。地区规则、四类词意图与每类 12 词上限见 `references/keyword-rules.md`。未有依据的案例、评价、资质、数据、合作关系与人物经历标待补，不凑字数。

旧版 `interactive` / `fast_path` 仅在用户明确要求 Legacy-compatible V4 时使用；不得把它的逐阶段交互加载到 Standard。客户语料库写入、外部研究和真实平台验证仍需用户明确要求。

运行前参照 [INDEX.md](INDEX.md) 与 [阶段 0 系统边界](docs/phase-0-system-boundaries.md)；执行细节由程序与 Schema 决定，而不是由 Markdown 改写。
