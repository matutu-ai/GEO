# GEO：四类关键词与九大画像

本项目把客户已确认资料和上游 GEO 处方整理为可直接用于 GEO 训练与运营的关键词与画像。

```text
确认资料＋Prescription
→ 四类关键词
→ 九大画像
→ 一条下一步建议
```

GEO-BD 负责诊断“为什么优化、优先优化什么”；本项目负责执行“使用哪些词、建立什么画像”。两者只通过版本化 JSON Contract 协作，GEO 不修改上游处方、根因、优先级或诊断结论。

## 默认运行

Standard 是唯一默认入口：

```bash
python3 main.py \
  --handoff tests/fixtures/geo-bd-handoff-v1.json \
  --input tests/fixtures/complete-v4-company.json \
  --output output-standard
```

只导出一份：

```text
GEO 关键词与画像.md
```

报告对用户只显示客户资料摘要、四类关键词、九大画像、待补资料和一条下一步建议。短词根、搜索角色卡、Fact ID、Prescription 和 Strategy 只用于内部生成与校验。

## 输出选择

- 完整模式：四类关键词＋九大画像。
- 仅词模式：只输出四类关键词。
- 仅画像模式：只输出九大画像。
- 画像分品牌画像与垂直业务画像，均使用同一套固定九项。
- 画像默认简约版；完整版九项每项必须 800–1000 字，不满足则阻止导出。

四类词固定为品牌词、搜索词、问答词、意图场景词。九大画像固定为产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。

默认每类推荐 3–5 个词，最多 12 个。每条词记录短词根、意向等级、搜索角色、业务线、地区、来源、确认状态及关联画像。系统推荐词是基于确认资料生成的候选，不代表平台热度、排名或 AI 推荐结果。缺少证据的简约画像标待补；完整版直接阻止导出。

## Legacy V4

旧版仅在明确指定时运行：

```bash
python3 main.py --mode interactive --input input/company.json --output output
python3 main.py --mode fast_path --input tests/fixtures/complete-v4-company.json --output output
```

Legacy 继续保留协议、Schema 和回归测试，但不进入默认用户流程。

## 验证

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_tests.py
```

系统执行 Schema 校验、事实引用检查和 Fail Closed；内容生产、信源建设、发布和真实平台验证不属于默认主交付。
