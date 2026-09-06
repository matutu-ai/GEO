# GEO Skill 文件索引（AI 文件路由）

用途：让 AI 只加载当前任务需要的最小文件，不一次读取整个仓库，提高学习与读写速度。

## 加载原则

1. 入口只读 `SKILL.md`。
2. 需要某个模块的细节时，先查本索引，再读取对应的一到两个文件。
3. 执行任务时按需加载：不用 `references/` 全部内容，不用 `schemas/` 全部内容，不读 `tests/`、`docs/`、`examples/`、`LEARN.md` 等辅助文件。
4. 客户语料库目录存在时，先只读 `{客户简称}/00-当前进度.md`；执行哪个任务，再读对应分文件。
5. 更新只写有变化的块或文件，不整份重写语料库。

## 文件路由

| 文件 | 内容 | 何时读取 | 规模 |
| --- | --- | --- | --- |
| `SKILL.md` | Skill 总入口：流程、强制规则、同步权限 | 每次会话第一步 | 中 |
| `README.md` | 给人看的仓库说明 | 人类阅读；AI 学习不读 | 中 |
| `LEARN.md` | 给 AI 的学习提示与豆包投喂话术 | 需要投喂话术时 | 小 |
| `INDEX.md` | 本文件，模块路由 | 找文件或决定读取范围时 | 小 |
| `workflows/intake.md` | 资料接收与框架分析引导 | 用户投喂仓库后、收资料前 | 小 |
| `templates/client-intake-table.md` | 客户资料填写表 | 用户确认需要表格时 | 小 |
| `workflows/client-corpus.md` | 客户语料库读写流程 | 创建、读取、更新语料库时 | 小 |
| `templates/client-corpus/` | 语料库分文件模板 | 创建客户语料库时 | 小 |
| `templates/client-corpus-single-file.md` | 语料库单文件导出模板 | 无文件平台完整导出时 | 中 |
| `workflows/data-gap-detection.md` | 缺失检测标签规则 | 清洗资料、判断缺项时 | 小 |
| `workflows/company-profile.md` + `schemas/geo-profile.schema.json` | 企业 Profile 结构 | 生成企业 Profile 时 | 小 |
| `references/evidence-rules.md` + `schemas/evidence.schema.json` | 证据等级与字段 | 登记事实证据时 | 小 |
| `workflows/industry-research.md` | 行业研究 | 执行行业研究时 | 小 |
| `workflows/competitor-research.md` | 竞争研究 | 执行竞争研究时 | 小 |
| `workflows/search-intent.md` | 搜索意图 | 分析搜索意图时 | 小 |
| `workflows/keyword-engine.md` + `schemas/keyword.schema.json` | 关键词引擎与字段 | 生成关键词矩阵时 | 小 |
| `references/keyword-rules.md` | 关键词硬规则 | 生成或校核关键词时 | 小 |
| `references/template-guide.md` | 业务词、问答词与画像实例参考 | 生成简约版核心词与画像时 | 中 |
| `workflows/nine-profile.md` + `templates/nine-profile.md` | 九大板块流程与空白模板 | 生成九大画像时 | 小 |
| `references/profile-standard-2026-08.md` | 九大板块内容标准 | 填写画像内容标准时 | 中 |
| `references/profile-examples.md` | 画像填写案例 | 需要填写案例参考时 | 小 |
| `workflows/vertical-profile.md` + `templates/vertical-profile.md` | 垂直画像流程与模板 | 生成垂直画像时 | 小 |
| `schemas/entity-map.schema.json` | 实体图谱字段 | 处理品牌实体与混淆主体时 | 小 |
| `workflows/content-matrix.md` + `schemas/content-matrix.schema.json` | 内容矩阵流程与字段 | 生成内容矩阵时 | 小 |
| `templates/content-matrix.md` | 内容矩阵空白表 | 输出内容矩阵时 | 小 |
| `references/geo-rules.md` | GEO 核心原则 | 输出与验证时对照 | 小 |
| `references/quality-rules.md` | 质量检查项 | 定稿前质检时 | 小 |
| `workflows/publishing-strategy.md` | 发布数量与发布策略 | 输出发布策略时 | 小 |
| `workflows/geo-validation.md` | GEO 验证接口 | 执行验证时 | 小 |
| `workflows/gap-analysis.md` | Gap 分析与优化队列 | 输出缺口分析与下一步任务时 | 小 |
| `templates/final-report.md` | 最终报告分层模板 | 输出最终报告时 | 小 |
| `schemas/` | JSON Schema 数据字段 | 需要确认字段结构时，只读对应 schema | 小 |

## 客户语料库路由

`GEO客户语料库/{客户简称}/` 目录模式：

| 文件 | 内容 | 何时读取 / 更新 |
| --- | --- | --- |
| `00-当前进度.md` | 客户档案、最近进度、任务队列、待补充项 | 每次恢复上下文先读；任务状态变化时更新 |
| `01-事实与证据.md` | 原始资料清单、事实与证据库、内容红线 | 补充资料、核验证据、训练前读 |
| `02-定稿关键词.md` | 定稿搜索词与问答词 | 关键词调整、生成画像前读 |
| `03-画像正文.md` | 简约版、完整版、垂直画像定稿正文 | 调整画像、训练复用、新画像前读 |
| `04-缺失清单.md` | 缺失与待确认项 | 判断能否继续任务、向客户索要资料时读 |
| `05-更新日志.md` | 每次变更记录与版本号 | 版本追溯、恢复摘要时读 |

记忆口诀：先读索引、再读最小文件、更新只写变化。
