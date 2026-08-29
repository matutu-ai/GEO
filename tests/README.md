# GEO V3 Tests

## 场景

1. 完整制造企业资料
2. 资料严重缺失企业
3. 本地服务企业
4. B2B工业企业
5. 多个产品企业
6. 多个业务垂直企业
7. 存在虚假/未经验证信息的资料
8. 批量企业输入

## 验证内容

- Profile
- Evidence
- Keywords
- Intent
- Nine Profiles
- Vertical Profile
- Content Matrix
- Quality Check

## 运行

```bash
python tests/run_tests.py
```

## 说明

当前测试为模块完整性与 schema 可解析性测试。实际 GEO 效果验证依赖外部 AI Search / Web Search，未连接时输出 `NOT_AVAILABLE`。
