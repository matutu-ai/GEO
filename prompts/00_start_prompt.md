# GEO V4 启动提示

先遵循 `SKILL.md`、`core/execution_protocol.py` 和 `prompts/_interaction_contract.md`。Prompt 不能改变固定 Pipeline。

当用户只提供企业名称或资料不完整时，调用 Interactive Mode：

```text
【当前阶段】fact_normalization
【本阶段已确认事实】企业名称：<fact_id>｜CONFIRMED
【本阶段分析结论】已创建唯一 Fact_Packet；下游阶段尚未获准执行。
【缺失资料】企业定位、主营业务、目标客户、产品资料及其真实来源。
【冲突资料】无；如存在则原样列出，不覆盖。
【下一步唯一动作】请补充企业定位、主营业务、目标客户、产品资料和证据，或明确要求 Fast Path。
```

只有用户明确要求一次完成且资料满足契约时，运行 `python main.py --mode fast_path`。最终报告只能由 Renderer 生成。

## Standard Path 用户引导

当用户需要 GEO 关键词与画像，且已提供处方和必要企业事实时，运行 `python main.py --mode standard --handoff <handoff.json> --input <company.json> --output <dir>`。默认直接生成一份《GEO训练与运营词画像》：四类词说明训练用途，九大画像说明运营价值，并给出下一步方向。

仅当企业主体、业务政策或对外事实存在关键冲突时，再读取 [资料与证据确认](standard/01_evidence_confirmation.md) 并针对缺项询问。未确认词、案例、评价、资质、费用和效果数据必须保留待确认状态，不得伪装成定稿事实。
