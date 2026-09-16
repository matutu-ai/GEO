# GEO Skill V3.2

企业 AI 可见度执行系统。GEO-BD 负责诊断问题和给出处方，本仓库将经确认的企业资料转化为可直接投入 GEO 运营的 AI 认知资产。

## 核心流程

```text
企业资料输入
→ 企业认知建模
→ 产品价值分析
→ 用户场景分析
→ 九大画像生成
→ EEAT 信任增强
→ GEO 场景词库
→ 内容规划
→ GEO 优化执行方案
```

## 快速执行

默认任务优先使用 `workflows/fast_path.md`：把企业资料归一化为一份 `Fact_Packet`，同一轮完成默认模块，减少豆包、千问、DeepSeek 等平台的重复投喂。无目录能力的平台只投喂 `SKILL.md`、`INDEX.md`、`workflows/fast_path.md` 和企业资料包。

默认按“简约版确认 → 完整版交付”生成词与画像。文章、内容正文、发布策略、外部检索和客户语料库均需用户明确确认后按需执行。

## 交互式流程

只输入客户名称时，先读取 `prompts/_interaction_contract.md`，再从 `prompts/00_start_prompt.md` 启动 Interactive Mode。默认主链为 `00 → 01 → 02 → 03 → 05 → 06 → 07 → 08 → 12 → 13`；行业研究、内容矩阵、发布策略和真实 AI 验证按需进入。每一步完成后暂停等待确认，外部检索和语料库读写也需明确确认。

已提供完整资料并要求一次完成时，继续使用 `workflows/fast_path.md`，不强制拆成 13 轮。

默认不生成文章。内容规划只在用户明确要求后，基于画像、场景词和用户意图执行。

## 最终交付

```text
output/
├── simple_keyword_persona.md
├── keyword_matrix.xlsx
├── persona_report.docx
└── geo_strategy_report.md
```

- `simple_keyword_persona.md`：简约版品牌词、搜索词、问答词、意图场景词，以及旧九大板块画像，用于客户确认。
- `keyword_matrix.xlsx`：完整版关键词矩阵，固定四个工作表：品牌词、搜索词、问答词、意图场景词。
- `persona_report.docx`：完整版旧九大板块画像：产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。
- `geo_strategy_report.md`：当前 AI 认知状态、当前缺失、优化方向、内容建设计划、30/60/90 天执行计划。

## 本地运行

使用默认验收样例：

```bash
python main.py
```

默认输入为 `input/company.json`，仅含“德州拓晟通风设备有限公司”名称。程序不会从名称推断产品、资质、客户或案例，未知字段均输出 `【需企业提供真实佐证】`。

使用自己的资料：

```bash
python main.py --input /path/to/company.json --output /path/to/output
```

JSON 输入可填写企业名称、官网、定位、主营业务、目标客户、服务区域、核心能力、应用场景、竞争优势、业务边界、产品、用户意图及证据资料。参考格式见 `input/company.json`。

## 质量规则

- 不虚构企业、产品、技术、资质、案例、客户、评价或人物资料。
- 所有场景词必须有用户需求、搜索意图和对应画像。
- EEAT 分数为资料完整度，不是信用、能力、排名或平台推荐评分。
- 没有真实 AI 搜索验证记录时，必须输出 `NOT_AVAILABLE`。

## AI 平台提速

豆包、千问、DeepSeek、Codex 等平台先读取 `SKILL.md` 和 `INDEX.md`；需要执行哪个模块时，只按 `INDEX.md` 读取对应工作流和 Schema。不要将全部仓库、全部模板和全部历史语料一次性投喂。

客户语料库使用前先询问；用户确认后才读取。无文件能力平台恢复任务时，只投喂单文件语料库第 0 节速读块，再按任务补充对应小节。

## 验证

```bash
python tests/run_tests.py
```

验证结构、Schema、四份导出文件、四类词工作表、旧九大板块完整性和报告格式。

## License

MIT. Copyright (c) 2026 matutu-ai.
