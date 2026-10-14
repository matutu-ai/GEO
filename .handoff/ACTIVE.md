# Active Task

- Current task: 按 `/Users/matutu/Downloads/geo词&画像.md` 更新 GEO 主 Skill 与 Standard 导出，并同步 GitHub。
- Objective: 以附件为主，落实完整/仅词/仅画像三种输出、六类词根、四类词、九大画像、简短互动和事实边界；保留 Legacy 与版本化执行合同。
- Current progress: Standard 代码、Skill、提示、参考文档和测试已更新；整库 79 项测试、讯灵案例导出与 Skill quick validation 均通过；本地提交 `57efd87` 已完成。
- Current blocker: GitHub CLI Connector 未连接；HTTPS push 返回 `could not read Username ... Device not configured`。工作区无凭据，远端尚未更新。
- Exact next action: 在本机完成 GitHub 登录/凭据配置后执行 `git push origin main`，再验证 `HEAD` 与 `origin/main` 一致；不需重做本地测试。
