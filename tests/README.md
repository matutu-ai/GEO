# GEO V4 Tests

## 覆盖范围

- 默认 Interactive Mode 只创建 Fact_Packet 并暂停。
- 完整 Fast Path 按八个固定阶段运行并导出 10 份工件。
- Pipeline 策略禁用 dynamic routing、Agent override 和 legacy 流程。
- JSON Schema 文件可解析，输出结构、固定四类词和九大画像可验证。
- 25 项协议测试覆盖缺失资料、冲突资料、字段越权、跳过阶段、无来源关键词、未标记推断、虚构背书、覆盖上游工件与绕过 Renderer 等行为。

## 运行

```bash
python tests/run_tests.py
```

所有 `ERROR` 必须 Fail Closed；不连接外部 AI 平台或 Web Search，也不会生成平台验证结论。
