# GEO V4 快速路由

适用于豆包、千问、DeepSeek、Codex 等平台。此文件不能覆盖 `SKILL.md`、程序协议、Schema 或 Validator。

1. 只有企业名称、资料不完整，或没有明确要求一次完成：进入 `Interactive Mode`。只创建 Fact_Packet，输出唯一下一步资料收集动作。
2. 用户明确要求一次完成，且已提供企业名称、企业定位、主营业务、目标客户和产品资料：进入 `Fast Path`，固定执行八阶段 Pipeline。
3. 不得自行选择、跳过、重排、添加任何阶段；不得读取 `workflows/legacy/` 或 `prompts/legacy/`。
4. 未知、推断与冲突必须保留状态；关键词必须有 `fact_ids`、用户场景、搜索意图和固定画像绑定。
5. 最终文件只能由程序 `main.py` 和 `core/output_renderer.py` 生成。任何校验错误均停止导出。
