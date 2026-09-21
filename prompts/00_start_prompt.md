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

当用户需要关键词、用户决策画像和企业九大画像时，进入 [Standard Guided Flow](standard/README.md)，按以下顺序逐段确认：

```text
选择交付 → 资料与证据 → 用户决策画像 → 关键词分层 → 企业九大画像 → 下一步技能决策
```

每次只给一个下一步提示。未确认的词、主体、案例、评价、资质、费用和效果数据只能进入待确认或排除层，不得直接导出为对外事实。
