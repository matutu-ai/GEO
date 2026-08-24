# geo-keyword-profile-template

基于《GEO核心词&画像套用模版参考建议》整理的 Codex Skill，用于生成 GEO 核心词、画像段落、发布数量策略和讯灵GEO发布规则。

## 功能

- 核心词：品牌词、问答/搜索词、场景意图词
- 画像：10 个画像字段
- 两版流程：先输出简约版，确认后再生成完整版
- 完整版：每个画像段落基本控制在 800-1000 字
- 业务垂直画像：针对单一业务类型单独输出专属画像
- 发布数量策略与讯灵GEO发布规则

## 目录

```text
geo-keyword-profile-template/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
`-- references/
    `-- template-guide.md
```

## 使用

将本目录放入 `~/.codex/skills/`，或在 Codex 中加载 `SKILL.md`。

适合以下场景：

- 配置 GEO 核心词
- 生成企业画像、用户画像
- 生成业务垂直画像
- 配置词包训练
- 制定发布数量计划

## 来源

《GEO核心词&画像套用模版参考建议》（飞书文档，2026-08-07 修改）。

## License

MIT
