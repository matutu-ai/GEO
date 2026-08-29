# Data Gap Detection 资料缺失检测

## 输出标签

- `FACT`：已确认事实
- `VERIFIABLE`：可以公开验证的信息
- `INFERRED`：AI 合理推断
- `MISSING`：完全缺失
- `RISK`：有风险或疑似虚假

## 规则

1. 企业资料直接出现 → `FACT`
2. 企业提供但未外部验证 → `VERIFIABLE`，标记待验证
3. 公开网络可查 → 验证后转为 `FACT`
4. AI 推测 → `INFERRED`，不能写入企业事实
5. 没有信息 → `MISSING`
6. 有矛盾或疑似虚假 → `RISK`

## 输出

- Data Gap Report
- 九大画像中缺失项不得虚构
