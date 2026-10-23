# Handoff

## 2026-10-22：4.4.2去掉意向程度列（历史，格式规则继续沿用）

- 用户“还是去掉吧”按取消意向程度列执行，恢复推荐词/短词根两列；补词入口与先选词再画像流程保留。内部intent_level合同不变。
- 用户要求继续跑流程：新版大作美居两列候选词已生成，通过格式检查；用户尚未明确所选词与画像范围，不能将“继续”视为全选。九项完整版仍缺品牌故事、背书、案例评价、创始人等材料。
- 整库回归通过，后续安装状态见ACTIVE.md。未提交、未推送GitHub。

## 2026-10-22：4.4.1意向程度与客户补词（历史，词数限制已被4.5.0取代）

- 用户要求增加意向程度；词表恢复三列，列名统一“推荐词｜短词根｜意向程度”。四类词与先选词后画像流程不变。
- 补词：保留原词，核对业务、分类、词根及意向；必要时给1–2个优化候选，不默改、不自动批准。CLI复用requested_keywords，未知已选词提示补词入口；字段校验不能代替语义核对。
- 验证：整库回归、两处Skill验证、8文件安装包同步通过；新增补词待确认→明确选定→画像绑定测试。大作美居三列案例一次分隔符错误已修正，通过格式检查。
- 安装：output/geo-keyword-persona-4.4.1.zip；旧安装备份 /var/folders/l6/jwyqnq450c786fjrxkwvrxn00000gn/T/geo-skill-backup-1ccsr95y。未提交、未推送GitHub。

## 2026-10-22：4.4.0先选词、再生成画像（历史，阶段流程继续沿用）

- Flow: 首轮默认仅词模式，四类词统一推荐词/短词根两列；用户一次选择词和画像范围后，再生成品牌或单一业务画像。画像默认完整版，固定九项每项800–1000字；简约版显式选择。
- Current keyword policy (added 2026-10-23; supersedes earlier quantity limits): recommend all distinct, fact-supported candidates with no fixed per-category cap; order/group by confirmed business core priority, then intent strength. Keep the two-column delivery format. User confirms terms and profile scope before profile generation; a vertical profile remains limited to the one business the user names.
- Gate: approved_keywords必须是本轮有效原词；拒绝未知、已排除、禁用地区和业务不符的选择。候选不是批准；合并导出只列已选词。仅画像模式章首记录所选词。跨轮通过requested_keywords保留所选条目。
- Scope: 搜索词以场景/人群＋产品业务为主，不机械追加定位；意向保留内部合同。12阶段及Legacy/GEO-BD边界不变。CLI不调用模型写长文，完整版需要确认正文，不能凑字数或编造。
- Validation: 48项定向测试首次有1条旧断言失败（要求首轮显示画像中的原场景文字），已修正；整库tests/run_tests.py通过，两处Skill quick_validate通过，git diff --check通过；本机与4.4.0安装包8文件逐字节一致。未做本版独立模型长文生成或实测推广效果验证。
- Installed: output/geo-keyword-persona-4.4.0.zip；原安装文件备份 /var/folders/l6/jwyqnq450c786fjrxkwvrxn00000gn/T/geo-skill-backup-2w6kcd54。
- Git: 未提交、未推送；以下4.3.0及更早记录是历史，不代表当前格式。

## 2026-10-22：统一三列词表、九项画像与独立 Skill 包

- Completed: templates/delivery.md 为唯一版式，程序直接读取，独立 Skill 同包提供；词表固定推荐词/短词根/意向三列，画像九项顺序固定，待补资料与下一步建议固定结尾。
- Generation: 客户主体不再从业务名公共前缀推断；问答/意图使用产品或服务表达，不再机械拼接“零售怎么选/用业务解决需求”；短词根逐条提取；标点差异的重复词合并并保留客户原句；不因“需要”或类型标签一律判高意向。
- Skill: 4.3.0；scripts/package_skill.py 从同一源码打包8个文件并逐文件核对。本机旧文件备份在 /var/folders/l6/jwyqnq450c786fjrxkwvrxn00000gn/T/geo-skill-backup-u98firax。
- Validation: scripts/check_delivery.py 是程序与独立 Skill 共用的最终结构检查；完整模式/仅词/仅画像及简约/完整版分别检查。程序按画像名称匹配模板位置，避免输入顺序变化导致正文错位。
- Verification: python3 tests/run_tests.py 通过；仓库及本机 Skill quick_validate.py 通过；独立安装包实际生成大作美居简约完整案例并通过检查；主代理复核后统一了两处品牌词根。相同资料的程序案例与 Skill 案例章节一致，均为四张三列表。git diff --check 通过。
- Limits: 案例基于用户提供事实，未执行平台搜索热度或推荐效果验证。独立模型验证仅一轮，不保证不同模型逐字一致；统一模板与检查固定结构。
- Git: 本轮未提交、未推送。以下记录是旧版本历史。

## 2026-10-21：最新词与画像规则严格落地

- Completed: 四类词新增短词根、意向等级、搜索角色、业务线、地区、来源与确认状态；内部搜索角色卡补齐规模、决策权限、内容偏好和排除项。
- Persona: 品牌画像与垂直业务画像统一固定九项；完整版九项每项强制 800–1000 字，不合规时 Standard Fail Closed；简约版继续快速输出核心事实。
- Training: 新增文章训练约束，一文只绑定一个业务线、一个搜索角色、一个意向阶段、1–2 个主词和 3–5 个自然问法。
- Skill: 仓库和本机 `geo-keyword-persona` 更新到 4.2.0，并同步默认提示。
- Verification: `python3 tests/run_tests.py` 通过；默认 Standard 案例导出成功；两个 Skill quick validation 通过；JSON Schema 解析和 `git diff --check` 通过。
- Git: 主功能提交 `debe3e7` 已成功推送至 `origin/main`；本地与远端将在本记录提交后再次核对。

## 2026-10-20：Standard 收口与默认路径清理

- Completed: Standard 改为 CLI 默认路径；修复 `delivery_mode` 被强制改回完整版的问题；画像默认简约版，完整版按确认资料展开。
- Output: Standard 对外只保留客户资料摘要、四类关键词、九大画像、待补画像和一条下一步建议；输出文件更名为 `GEO 关键词与画像.md`。六类词根与用户决策画像继续作为内部依据，不独立输出。
- Historical rule, superseded: system recommendations previously used per-type count limits. Do not apply this archived limit; follow the current dynamic quantity policy above.
- Skill: 仓库 Skill 与 `/Users/matutu/.codex/skills/geo-keyword-persona` 统一为 `geo-keyword-persona` 4.1.0；两处 quick validation 均通过。
- Cleanup: 客户专属文档和旧工作稿移入 `cases/xunling-ai/archive/`；旧客户语料库模板移入 `templates/legacy/`；Legacy 程序、Schema 和测试保留。
- Verification: 80 项单元/协议/合同测试通过；`python3 tests/run_tests.py` 通过；讯灵案例只生成一份 `GEO 关键词与画像.md` 且章节只有摘要、四类词、九大画像、待补画像、下一步建议；`git diff --check` 通过。
- Git: 本次未提交、未推送。用户明确授权后再提交并同步 GitHub。

- Completed work: Standard 用户流程已收敛为一次资料收集、自动处理、仅必要时集中追问一次；指导产物只给一条下一步动作和一个相关技能建议。统一四类关键词、九大画像、简约/完整版/垂直完整版规则，并澄清 CLI 精简输出与 Skill 长版生成的边界。
- Changed files: `SKILL.md`、入口/路由/README/架构文档、Standard 与 Legacy 交互边界提示、关键词/画像规则与模板、`core/standard_pipeline.py`、`core/standard_renderer.py`、测试、删除未引用的旧 `geo-rules.md` / `quality-rules.md` / `profile-examples.md`。
- Verification results: `python3 -m unittest tests.test_standard_path tests.test_prompt_contract` 通过（26 项）；`python3 tests/run_tests.py` 通过（Standard Path、Legacy V4、协议与阶段检查）；讯灵 AI 案例仅生成 `GEO训练与运营词画像.md`；`git diff --check` 通过；已同步至 `origin/main`（`051edc3827e9bcd24bb5439263171dc26e88fb36`）。
- Blockers: TypeSafe Jev 多次返回 ByteString 编码错误，本轮未获得模型判断；按用户规则、源码、Schema 和本地测试完成。
- Pending verification: 讯灵 AI 部分主体关系、招商政策、案例与资质继续按现有证据状态标待确认；不阻塞结构交付。
- Latest task: Standard 报告新增短词根列，分别对应已确认业务、决策疑问和需求场景；客户原词仍原样展示。
- Latest changed files: `README.md`、`core/standard_renderer.py`、`references/keyword-rules.md`、`tests/test_standard_path.py`；本地提交 `055884a`。
- Latest verification: `python3 tests/run_tests.py` 通过；讯灵案例 Standard CLI 导出成功；Skill quick validation 与 `git diff --check` 通过。GitHub 同步未完成。
- Current blocker: GitHub CLI 默认账号令牌无效、GitHub 连接器未连接、浏览器未登录、SSH 443 无可用公钥；HTTPS push 返回凭据不可用。
- Exact next action: 用户重新登录 GitHub 后执行 `git fetch origin main`、确认无远端分叉，再 `git push origin main`；验证 `HEAD` 与 `origin/main` 一致。

## 2026-10-14：按附件规则重整并同步 GEO Skill

- Objective: 严格以 `/Users/matutu/Downloads/geo词&画像.md` 为主，完成 Standard 规则、程序、测试和 GitHub 同步；Legacy 与现有 JSON 合同保持隔离。
- Implemented: 新增完整/仅词/仅画像三种报告模式；六类短词根、真实使用场景筛选、地区词清理、每类最多 12 词；完整画像按确认事实输出，不凑字数。更新 `SKILL.md`、Standard 提示/参考文档、讯灵样例和回归测试。
- Changed: `core/keyword_terms.py`、`core/standard_pipeline.py`、`core/standard_renderer.py`、相关 Skill/README/路由/提示/参考文档、`agents/openai.yaml`、讯灵样例、测试、移除已确认过时且无引用文件。
- Verification: `PYTHONDONTWRITEBYTECODE=1 python3 tests/run_tests.py` 通过（全库 79 项含 Legacy/契约回归）；讯灵样例成功只导出一份 Markdown，检查三类主章节；Skill `quick_validate.py` 通过；`git diff --check` 通过。
- Decision support: TypeSafe Jev 在本任务连续返回 ByteString Unicode 错误；未取得决策结果，按附件、代码契约和测试完成。
- GitHub: 用户已明确授权推送；`origin/main` 无额外领先提交，本地含两个既有提交及本次提交 `57efd87`。提交成功；`git push origin main` 失败：HTTPS 凭据不可用 (`could not read Username ... Device not configured`)。GitHub Connector 也未连接。远端未更新。
- Exact next action: 用户在本机登录 GitHub/配置凭据后运行 `git push origin main`，然后确认 `git status --short --branch` 显示与 `origin/main` 同步。

## 2026-10-14：四类关键词逻辑优化

- Completed: 按用户确认完善四类词的意图边界与训练顺序；收紧 Standard 自动生成的问答词和明确需求词，报告注明系统建议并非平台实测热词。外部平台研究仍需用户明确要求；需记录原句、平台/页面和日期，现有 JSON 合同暂不支持将平台来源写入结构化产物。
- Changed: `references/keyword-rules.md`、`core/standard_pipeline.py`、`core/standard_renderer.py`、`prompts/standard/00_quick_start.md`、`workflows/standard_path.md`、`SKILL.md`、`README.md`、`tests/test_standard_path.py`、`tests/test_prompt_contract.py`。
- Verification: `PYTHONDONTWRITEBYTECODE=1 python3 tests/run_tests.py` 通过（Standard Path、Legacy V4、协议和合同检查）；`git diff --check` 通过。
- Decision support: 已尝试 TypeSafe Jev 两次，均因 ByteString Unicode 编码错误失败；当前可用技能列表未提供 `typesafe-ai` 安装说明。按已确认用户边界和仓库合同实施，不更改 JSON 合同、不添加抓取依赖。
- GitHub: 未提交或推送；工作区含本任务之前已有的未提交修改和 2 个本地领先提交。
- Exact next action: 若后续要导入平台观察词，先升级关键词来源合同/Schema 和验证测试，再实现授权后的采集；否则当前默认保持事实约束下的系统建议词生成。

## 2026-10-08：按最新业务词根与画像规则更新

- Completed: Standard 单份 Markdown 改为 `GEO 业务词根与画像.md`，从确认事实提炼六类短根；四类关键词默认每类三条系统建议并保留客户原词；核心业务根生成画像卡，九大画像按简约/完整版显示。垂直版只接受已确认单一业务，未确认跨业务关联标待补。Legacy 与 JSON 合同未改。
- Changed: `core/standard_pipeline.py`、`core/standard_renderer.py`、讯灵示例偏好、测试及 Standard 文档和 Skill 规则；删除已被新规则替代的旧版讯灵输出样例（可由 Git 恢复）；当前为未提交工作树。
- Verification: `python3 tests/run_tests.py` 通过；Skill quick_validate 通过；讯灵示例 Standard CLI 成功导出一份 Markdown；`git diff --check` 通过。真实 AI 搜索效果、公开材料授权及 GitHub 同步未验证。
- Limit: CLI 不调用模型生成九项 800–1000 字长文；资料不足时输出已有事实并标注缺口。旧 GitHub 鉴权失败状态尚未复检。
- Next: 审阅本地 diff 和讯灵案例，按用户明确同步授权及可用认证完成提交/推送；若需要实际长版九项正文，先提供每项可引用且已授权的事实材料。

## 2026-10-09：无关内容清理（安全范围）

- Inventory: 140 个已追踪文件；`main.py` 与完整测试仍调用 Legacy V4。旧客户研究、案例稿和大量 Legacy 模板存在，但不能仅凭未被 Standard 引用认定为可删。
- Removed (Git 可恢复): `LEARN.md`（声称旧 Excel/DOCX 为当前主交付）、`examples/README.md`（空 V3 示例占位）、`templates/simple-keyword-persona.md`（与六类词根/画像卡新规则不符且无引用）。未删除客户资料、运行代码、Schema、测试或 Legacy 文档。
- Simplified: `SKILL.md` 从 143 行缩至 89 行，旧路径细节改为按需链接；`QUICK_ROUTER.md` 改正旧版 CLI 描述。
- Verified: `python3 tests/run_tests.py`、Skill quick_validate、`git diff --check` 通过。TypeSafe Jev 仍因 ByteString 编码错误不可用；按实际引用与合同作决定。
- Pending decision: 用户是否要求删除 Legacy V4 运行能力；若是，属于改变 CLI/测试合同的独立高风险清理。旧客户案例与语料模板是否视为待删除仍需明确；当前保留。
- GitHub: 本次未提交/推送；原有未提交工作树和本地领先远端的 2 个提交继续保留。
