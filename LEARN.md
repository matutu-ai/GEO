# GEO 学习与平台投喂说明

先建立系统边界：

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

推荐最短阅读顺序：

1. `README.md`：产品定位和当前实现状态。
2. `docs/phase-0-system-boundaries.md`：GEO-BD / GEO 隔离、只读处方和闭环。
3. `workflows/standard_path.md`：Prescription-driven Standard Path 的固定运行顺序。
4. `schemas/geo-bd-handoff-v1.schema.json`：诊断处方向 GEO 的唯一标准入口。
5. `schemas/geo-strategy-v1.schema.json`：Prescription → Strategy 的强制引用。
6. `schemas/geo-retest-request-v1.schema.json`：GEO 只能请求复测，不能宣布诊断结果。
7. `SKILL.md`：Standard Path 与 Legacy-compatible V4 执行规则。

豆包、千问、DeepSeek、Codex 等平台必须保持两个系统的代码和逻辑隔离。只能读取 JSON Contract，不得导入或调用另一个仓库的模块、Engine 或 Pipeline。

当前同时保留两条路径：`standard` 是关键词与九大画像主路径；`interactive` / `fast_path` 是 Legacy-compatible V4。标准模式必须有 GEO-BD 或 Manual Prescription，资料不足或 Contract 不合法时直接 Fail Closed。

当前主交付只有关键词和九大画像：`keyword_matrix.xlsx`、`persona_report.md`，JSON 文件用于机器追溯。内容、信源、发布和复测不进入主交付。

当前 Trust Score 仅表示资料完整度 / Evidence Readiness。GEO Report 只能汇总执行结果，不能重新生成 Judgment、RootCause、Diagnostic Score 或修改 GEO-BD Priority。
