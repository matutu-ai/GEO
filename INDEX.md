# GEO V4 固定执行索引

本索引只路由 V4 程序约束；不能替代或修改执行协议。

| 目标 | 唯一入口 | 结果 |
| --- | --- | --- |
| 资料不足或只给企业名称 | `python main.py --mode interactive` | `fact_packet.json`、`interactive_state.json`、执行轨迹；流程暂停 |
| 用户明确要求一次完成且资料完整 | `python main.py --mode fast_path --input <company.json>` | 10 份经过验证的 V4 最终工件 |
| 检查协议和权限 | `core/execution_protocol.py`、`core/agent_contracts.py` | 固定顺序、字段级权限 |
| 检查事实与结构 | `schemas/*-v4.schema.json`、`validators/v4_validator.py` | Fail Closed 校验 |
| 了解兼容历史资料 | `workflows/legacy/`、`prompts/legacy/` | 仅供人工参考，不可默认执行 |

外部 AI 平台先投喂 `QUICK_ROUTER.md`。该路由只能决定交互或 Fast Path，不允许平台自行改变 Pipeline。
