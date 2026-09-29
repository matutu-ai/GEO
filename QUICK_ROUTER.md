# GEO 快速路由

先读 `INDEX.md` 选择路径，再只读该路径需要的入口文件。此文件不能覆盖 `SKILL.md`、程序协议、Schema 或 Validator。

1. 有 GEO-BD Handoff 或人工处方，且企业关键事实已确认：使用 `standard`，读取 `workflows/standard_path.md`，导出一份 GEO 训练与运营词画像。
2. 只需资料收集或运行旧版 V4：按 `README.md` 选择 `interactive` 或 `fast_path`，读取 `workflows/fixed_pipeline.md`。
3. 不得自行跳过、重排阶段；未知、推断和冲突必须保留状态，校验失败即停止导出。
4. Standard Path 最终文件由 `core/standard_renderer.py` 生成；Legacy V4 由 `core/output_renderer.py` 生成。两条路径隔离，不回退。
