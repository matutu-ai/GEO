# GEO：四类关键词与九大画像

本项目把客户已确认资料和上游 GEO 处方整理为可直接用于 GEO 训练与运营的关键词与画像。

```text
确认资料＋Prescription
→ 四类候选词（推荐词｜短词根）
→ 用户一次选词＋选择画像范围
→ 品牌画像或指定业务画像（九项，每项800–1000字）
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

首轮只显示资料摘要、四类候选词、待补资料和一条选词引导，不生成画像。四类词表统一两列：推荐词、短词根；每类用途放在标题下面。搜索角色、业务线、来源状态、Fact ID、Prescription 和 Strategy 留在内部。

唯一输出模板是 `templates/delivery.md`，程序直接读取，独立 Skill 使用同一文件。导出时只做一次 `scripts/check_delivery.py` 检查，固定标题、两列表头和九项顺序；完整版另检查每项字数。固定结构不要求不同模型逐字生成相同内容。

## 输出选择

- 仅词模式（初次默认）：只输出四类候选词，等待用户一次选词并指定画像范围。
- 仅画像模式（选定后默认）：只输出绑定已选词的九大画像，不重出候选词表。
- 完整模式：用户已选词并明确要求合并导出时使用，只包含已选词＋九大画像。
- 画像分品牌画像与垂直业务画像，均使用同一套固定九项。
- 画像默认完整版；九项每项必须 800–1000 字，不满足则列缺口并阻止导出。简约版仅明确要求时提供。

CLI 第二阶段在 `geo_preferences.approved_keywords` 记录用户所选原文，设置 `output_mode: 仅画像模式`；品牌画像不设 `vertical_business`，业务画像指定一条已确认业务。跨轮用 `requested_keywords` 保留已选条目的原文、类型、短词根与业务线。未选词不生成画像，候选状态不等于批准。CLI 不调用模型写长文，需提供已确认的 `complete_personas` 九项正文或满足字数的事实正文；独立 Skill 可根据确认资料展开正文。

四类词固定为品牌词、搜索词、问答词、意图场景词。九大画像固定为产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍。

推荐词数量不设固定上下限；按已确认业务的核心程度、需求差异和意向强度动态推荐，不用同义词凑数。多业务候选按业务优先级分组/排序，客户补充词原样保留且不因条数限制被丢弃；训练画像时仍只围绕用户选定的范围。客户企业品牌与经营产品品牌分别处理；搜索词不带地区。每条词内部记录短词根、搜索角色、业务线、地区、来源、确认状态及关联画像。系统推荐不代表平台热度或 AI 推荐结果。简约画像缺证据标待补；完整版不满足条件则阻止导出。

## 安装与分发同一版本 Skill

客户可补充推荐表外的词或需求。Skill核对业务后保留清晰原词，或给1–2个优化候选；CLI通过`requested_keywords`接入。仅补词不自动批准，改写不替代原词记录；明确选定后再写`approved_keywords`。意向程度仅作内部需求阶段判断，不是热度或转化概率。

仓库是唯一编辑源。给客户完整安装包，不只复制启动提示词；不要另行手写本机 Skill。

```bash
python3 scripts/package_skill.py --archive output/geo-keyword-persona.zip
python3 scripts/package_skill.py --install-to <技能安装目录>/geo-keyword-persona
```

打包包含入口、关键词/画像规则、固定模板和独立检查脚本；安装时备份被覆盖的旧文件，并逐文件核对与源码一致。独立 Skill 不要求客户提供处方 JSON；仓库程序继续使用现有 Handoff 合同。

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
