# GEO 测试

运行：

```bash
python3 tests/run_tests.py
```

测试覆盖：

- Standard 为默认入口，缺少 Handoff 时 Fail Closed。
- Standard 固定 12 阶段、Prescription 只读和完整引用链。
- 完整模式、仅词模式、仅画像模式互不泄漏其他章节。
- 简约版与完整版画像真实生效。
- 四类关键词、九大画像、来源状态和地区边界。
- Standard 只导出一份 `GEO 关键词与画像.md`。
- Legacy V4 只有显式调用时运行，既有10份输出继续兼容。
- Schema、Agent 权限、阶段顺序和 Renderer 绕过防护。

测试不连接外部 AI 平台或搜索引擎，也不把系统推荐词解释为真实热度或推荐结果。
