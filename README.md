# GEO Skill V4

GEO 是企业 AI 可见度的执行系统：将已确认资料转为可追溯的四类关键词、固定九大画像和 GEO 优化报告。GEO-BD 未被本次改造修改。

## 不可覆盖规则

执行顺序、Agent 权限、事实状态、Schema 校验和导出均由程序控制。模型、平台和用户不能自行跳过阶段、修改定位、虚构事实、加载 legacy 流程或在校验失败后导出报告。

## 运行

只输入企业名称或资料不完整时，默认进入交互暂停状态：

```bash
python main.py
```

该模式只生成 `fact_packet.json`、`interactive_state.json` 与执行轨迹，并要求补充资料。

用户明确要求一次完成且资料满足契约时：

```bash
python main.py --mode fast_path --input tests/fixtures/complete-v4-company.json --output output
```

最终输出固定为 `fact_packet.json`、`company_profile.json`、`product_profile.json`、`intent_keyword_matrix.json`、`persona_report.docx`、`trust_report.json`、`keyword_matrix.xlsx`、`geo_strategy_report.md`、`final_summary.json` 和 `execution_trace.json`。

## 验证

```bash
python tests/run_tests.py
```

此命令验证 V4 策略、默认交互暂停、完整 Fast Path、固定四类词、Fail Closed 和 25 项协议合规测试。

详细执行合同见 [SKILL.md](SKILL.md)，历史 V3 流程只保留在 `workflows/legacy/` 和 `prompts/legacy/`，不会自动执行。
