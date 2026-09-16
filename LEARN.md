# GEO V4 平台投喂说明

豆包、千问、DeepSeek、Codex 等平台先投喂 `QUICK_ROUTER.md` 和 `SKILL.md`。平台只能选择以下入口，不能改写 Pipeline：

- 资料不足：Interactive Mode，仅创建 Fact_Packet 并提出唯一补料动作。
- 用户明确要求一次完成且资料完整：Fast Path，执行固定八阶段。

可直接使用以下提示：

```text
执行 GEO Skill V4。严格遵循 SKILL.md、QUICK_ROUTER.md 与程序协议。
不得自行选择、跳过、重排或增加阶段；不得修改企业定位；不得虚构事实；不得读取 legacy 流程。
资料不足时，只创建 Fact_Packet 并输出缺失资料和下一步唯一动作。
只有我明确要求一次完成且资料契约完整时，才执行固定 Fast Path。
未知、推断与冲突必须保留状态；最终文件必须由程序校验和 Renderer 输出。
```
