---
name: geo-keyword-profile-template
description: "按不可覆盖的 GEO V4 固定流水线，将已确认企业资料转为可追溯的词库、九大画像和优化报告。"
metadata:
  version: 4.0.0
---

# GEO Skill V4 执行合同

## 1. Skill 身份

GEO Skill 只执行已确认的企业资料和 GEO-BD 已给出的处方，不修改 GEO-BD。本 Skill 的程序执行协议优先于用户临时要求、模型判断、旧工作流、旧 Prompt 和输出偏好。

## 2. 强制执行规则

【强制执行声明】

使用本 Skill 时，必须严格按照固定 Pipeline 执行。本 Skill 不允许模型自行选择流程，不允许智能体自行改变企业定位，不允许跳过必需阶段，不允许将推断内容当作确认事实，不允许在缺少证据时生成确定性营销声明。本 Skill 的最终输出必须通过程序校验。

任何模型、智能体、平台或用户都不能改变阶段顺序、删除必需阶段、增加未授权阶段、重新生成事实、覆盖上游结果、将未知写成已知、将推断写成事实，或生成未经证实的案例、客户、评价、资质、数据和能力。校验失败时必须停止最终导出。

## 3. 固定执行顺序

程序加载 `core/execution_protocol.py` 与 `config/pipeline_policy.json`，固定执行：

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

## 4. Agent 权限

每个 Agent 在 `core/agent_contracts.py` 中拥有字段级读写权限，执行前必须通过 `protocol.check_agent_permission(agent_name)`。

- Fact Normalizer 是唯一原始资料读取者和 Fact_Packet 写入者。
- Company Intelligence 是唯一企业定位、业务范围和边界所有者。
- Keyword Intelligence 是唯一最终关键词所有者。
- GEO Report 只能汇总已校验工件；`core/output_renderer.py` 是唯一最终文件渲染器。

Agent 不得读取原始自由文本、调用其他 Agent、加载 legacy 工作流、修改 Schema、覆盖工件或写入其他 Agent 的结果。

## 5. 输入和输出契约

所有输入先进入 `Fact_Packet`。下游只能读取通过校验的 Artifact，所有事实声明必须引用 `fact_id`。最终导出固定为：

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

不得跳过阶段、动态路由、修改上游 Artifact、重新定义企业定位、无事实生成关键词、输出无 `fact_id` 的声明，或将未授权研究和 legacy 流程带入默认执行。

九大画像的名称和顺序固定为：产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。关键词只能是品牌词、搜索词、问答词、意图场景词，且必须包含场景、意图、画像和 `fact_ids`。

## 8. 错误处理

`validators/v4_validator.py` 产生 `ERROR`、`WARNING` 或 `INFO`。任何 `ERROR` 均 Fail Closed：停止下游、停止最终导出，并记录错误编号、字段、来源 Agent 和修复建议；不得自动修复为通过。

## 9. 用户交互规则

默认使用 Interactive Mode。只输入企业名称时，名称为 `CONFIRMED`，其余字段为 `UNKNOWN`，系统只输出当前阶段、已确认事实、分析结论、缺失资料、冲突资料和下一步唯一动作。不得直接生成完整画像、关键词或营销内容。

Fast Path 仅在用户明确要求一次完成且最低资料契约完整时启用。客户语料库、外部研究、内容生成和真实平台验证均需独立确认，且不属于默认固定 Pipeline。

## 10. 最终输出规则

最终报告只能汇总已校验的结构化上游结果，不得重新分析企业、定位或关键词。运行前参照 [INDEX.md](INDEX.md)；执行细节由程序而非 Markdown 决定。
