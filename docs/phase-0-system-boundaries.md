# 阶段 0：系统边界冻结与 GEO-BD 协作合同

## 1. 唯一产品定位

GEO-BD 是企业 GEO 诊断与处方系统：

```text
事实 → 证据 → 指标 → 判断 → 根因 → 处方
```

GEO 是企业 GEO 优化执行系统：

```text
处方 → 执行策略 → 关键词 → 九大画像 → 内容 → 信源 / 渠道 → 发布执行 → 复测计划
```

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

## 2. 系统级隔离

- GEO-BD 和 GEO 都能独立运行、独立交付。
- GEO 不依赖 GEO-BD 代码，GEO-BD 不依赖 GEO 代码。
- 两个仓库不共享业务模块、Pipeline 或内部领域对象。
- 禁止直接导入对方包、调用对方 Engine，或建立任何隐式跨仓库依赖。
- GEO 不得修改 `Judgment`、`RootCause`、`Prescription`、`DiagnosticMeasurement` 或 Diagnostic Score。
- GEO-BD 不生成 GEO 的关键词、画像、内容、发布计划、渠道执行或媒体计划。

唯一允许的协作是版本化 JSON 数据交换：GEO-BD 输出 Prescription Handoff，GEO 输出 Retest Request。

## 3. GEO-BD → GEO Prescription Handoff V1

Schema：`schemas/geo-bd-handoff-v1.schema.json`。

标准 Handoff 必须声明 `handoff_version=1.0.0`、`diagnostic_id`、`company_id`、`source_system=GEO-BD`、`target_system=GEO`，且至少包含一条 Prescription。Prescription ID 必须唯一，每条必须包含：

```text
id
statement
priority
root_cause_ids
expected_outcome
verification_method
handoff_to=GEO
```

Handoff 和 Prescription 均为封闭对象。`generated_keywords`、`generated_personas`、`generated_content`、`keyword_matrix`、`content_plan`、`publishing_plan`、`media_plan`、`channel_plan`、`execution_tasks`、`retest_result` 以及其他未定义字段都会被 Schema 拒绝。

Prescription 是上游只读对象。GEO 只能读取其 ID、原文、优先级、Root Cause 引用、预期结果和验证方法，不得改写原文、重新定义根因、调整优先级、重新判断问题或生成新的 GEO-BD 诊断对象。

## 4. GEO Strategy V1

Schema：`schemas/geo-strategy-v1.schema.json`。

每条 Strategy 必须有 `STRATEGY-*` ID，并至少引用一个 `PRESCRIPTION-*`。`validators/contract_validator.py` 会校验引用的 Prescription 确实存在于本次 GEO-BD Handoff 或 Manual Prescription 输入中。Strategy 不能脱离处方独立生成，也不能带入 RootCause、Judgment 或 Diagnostic Score 字段。

阶段 0 统一预留引用链：

```text
PRESCRIPTION-*
↓
STRATEGY-*
↓
KEYWORD-* / PERSONA-* / CONTENT-* / SOURCE-* / EXECUTION-* / RETEST-*
```

未来执行对象至少支持 `prescription_ids`、`strategy_ids`、`fact_ids`。阶段 0 只在 Schema、文档和测试中冻结规则，不改造旧模块。

## 5. 两种标准输入模式

- 模式 A：GEO-BD Prescription Handoff + Confirmed Company Facts。
- 模式 B：Manual Prescription + Confirmed Company Facts。

Manual Prescription 使用同一 Handoff Schema 内的 `$defs.manualPrescriptionInput`，`source_system` 固定为 `MANUAL`；内部 Prescription 结构与 GEO-BD 完全相同，仍需 ID、priority、root_cause_ids、expected_outcome、verification_method 和 `handoff_to=GEO`。人工输入不能跳过 Strategy。

## 6. GEO → GEO-BD Retest Request V1

Schema：`schemas/geo-retest-request-v1.schema.json`。

Retest Request 只能表达“请重新检查这些诊断目标”，并引用已执行的 Prescription 和 Strategy。`source_system` 固定为 `GEO`，`target_system` 固定为 `GEO-BD`。封闭 Schema 会拒绝 `success`、新诊断结论、新 Diagnostic Score、新 RootCause 及其他未定义字段。是否优化成功必须由 GEO-BD 重新诊断。

## 7. GEO 固有职责

关键词属于 GEO，固定四类：品牌词、搜索词、问答词、意图场景词。未来每条关键词支持 `fact_ids`、`prescription_ids`、`strategy_ids`。

九大画像属于 GEO，固定顺序为：产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。未来每个画像单元支持同样的三类追溯 ID。

## 8. Trust 与 Report 边界

当前 `trust_intelligence` 保留。其 Score 只能理解为资料完整度 / Evidence Readiness，不能描述为 GEO 总分、AI 推荐概率、企业真实权威度或最终 EEAT 分数。

未来 GEO Report 可以汇总 Prescription、Strategy、Keyword / Persona / Content / Source / Execution / Retest Plan，但禁止重新诊断、生成新的 RootCause 或 Judgment、重新计算 GEO-BD Gap 或 Diagnostic Score，以及修改 GEO-BD Priority。

## 9. 阶段 0 冻结时的 Legacy 边界

阶段 0 冻结时的八阶段实现是 `Legacy-compatible V4 execution path`。该路径仍从 Fact Normalization 直接进入 Company / Product / Intent / Persona / Trust / Keyword / Report，不读取 Prescription Handoff。阶段 1 新增的 Standard Path 与它独立运行，不替换现有 10 个输出文件，不重构 `core/fixed_pipeline.py`。

当前 Standard Path 入口为 `python3 main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>`，其运行顺序和关键词/九大画像输出见 `workflows/standard_path.md`。

完整协作闭环是：

```text
GEO-BD 诊断 → Prescription Handoff → GEO Strategy
→ Keywords / Personas / Content / Sources → Execution
→ Retest Request → GEO-BD 重新诊断
```

数据可以循环，逻辑不能循环，职责不能交叉。
