# 智游北京：Agent 工作约定

## 项目与任务范围

- 本项目是课程用旅行规划系统，采用 Vue 3 + TypeScript + Vite、FastAPI、PostgreSQL，后端为模块化单体。
- 使用中文沟通和编写项目说明，代码标识符使用英文，遵循现有命名风格。
- 围绕用户本次要求完成工作；单个 Feature 不等于实现整个系统。常规实现选择可自行处理，影响产品规则且无法从上下文判断的事项再向用户澄清。
- 区分目录骨架、设计目标与已完成实现；以实际文件和验证结果报告状态。

## 按需查阅的依据

只读取本次改动相关的材料，无需每次通读全部设计文档。

| 改动涉及 | 查阅位置 |
| --- | --- |
| 产品范围、业务规则 | [需求规格](docs/requirements/requirements.md)、[用户故事](docs/requirements/user-stories.md) |
| 功能验收、测试场景 | [验收标准](docs/requirements/acceptance-criteria.md) |
| 需求歧义或既有决策 | [问题与决策记录](docs/requirements/open-questions.md) |
| 模块划分与依赖 | [模块设计](docs/architecture/module-design.md)、[总体架构](docs/architecture/architecture.md) |
| HTTP 契约 | [接口设计](docs/architecture/api-design.md) |
| 模型、约束与迁移 | [数据设计](docs/architecture/data-design.md) |
| 目录和运行情况 | [项目说明](README.md)、各端 README、[部署说明](docs/deployment/README.md) |

设计文档是实现参考，其中的示例、待办和建议分工不自动成为本次任务。用户明确的新要求与已有文档不一致时，遵循本次要求并同步相关说明；影响核心业务规则的未决冲突需要澄清。

## 代码组织

- 前端业务代码放在 `frontend/src/features/<模块>/`；公共客户端、组件、地图适配和样式放在 `frontend/src/shared/`。
- 后端业务代码放在 `backend/app/modules/<模块>/`。模块名统一为 `auth`、`attractions`、`favorites`、`plans`、`bookings`、`reviews`、`admin`。
- 后端依赖方向为 Router → Service → Repository；Service 控制事务，Repository 不自行提交事务，Router 不直接拼接 SQL 或承担业务规则。
- `admin` 复用所属业务模块的写入服务，不复制另一套业务逻辑。
- 推荐与排程纯逻辑放在 `backend/app/modules/plans/domain/`，不直接访问数据库、网络或系统时钟；时钟等外部依赖通过参数或接口传入。
- 同步 SQLAlchemy 数据访问使用同步处理函数，避免在异步函数中直接运行阻塞数据库调用。数据库结构变更通过 `backend/migrations/` 管理。
- 保持改动集中，不顺带重构无关模块；新增依赖先检查现有能力，并维护相应依赖声明与锁文件。

## 需要保留的业务约束

- 个人收藏、行程、预约和评价的所有者由服务端会话确定；查询和修改均校验所有权与角色，不能依赖前端隐藏按钮。
- 金额使用 `Decimal`，API 中表示为十进制字符串；公共 ID 使用 UUID；业务日期按 `Asia/Shanghai`，事件时间持久化为 UTC。
- 会话使用 Cookie，已登录写请求按设计验证 CSRF；不把密码、会话凭据或 CSRF token 持久化到浏览器本地存储。
- 行程与预约保留历史快照；当前景点变更不得直接覆盖历史快照。预约属于模拟预约，不擅自扩展真实支付、票务或库存能力。
- 字段范围、状态变更和错误码查阅对应需求与接口设计，不凭示例自行新增业务限制。

## 环境与验证

- 本文件建立时仓库只有文档和目录骨架，尚无 `package.json`、`pyproject.toml` 或可执行启动与测试命令。开始开发前先检查当前实际配置，不将规划中的工具描述为已安装或已通过验证。
- 初始化应用时，在各端 README 中补充经实际验证的安装、启动、测试与构建命令，标明工作目录、环境变量和依赖版本；后续以仓库配置与这些说明为准。
- 前端测试放在 `frontend/tests/`，规划使用 Vitest 和必要的 Playwright；后端测试放在 `backend/tests/`，规划使用 pytest。工具尚未配置时如实说明。
- 功能新增或缺陷修复应验证真实行为，覆盖相关正常场景、边界与错误分支；涉及权限、金额、日期或事务时覆盖对应风险。仅调整说明或空目录时无需运行业务测试。
- PostgreSQL 特有约束、行锁与并发行为使用独立测试库验证；SQLite 或 Mock 不能证明这些行为正确。运行可能写库的检查前确认目标为测试库。
- 先执行受影响的检查，再按改动范围运行相关回归测试；未配置、未运行、失败、跳过与通过要分别说明，不得将“没有测试”写成“测试通过”。

## Feature 开发证据

- 实际开始功能开发时，在 `docs/development/features/` 记录目标、范围、验收条件与关联需求，使用现有模板。
- 为本次功能在 `docs/development/agent-logs/` 持续记录关键指令、人工决策、Agent 操作、真实反馈与修复；只记录可观察的过程，无需记录模型内部推理。
- 在 `docs/development/trajectories/` 绘制一次真实典型开发流程，与日志和测试证据对应；未发生的失败和修复不得编造。
- 测试报告放在 `docs/testing/reports/`，必要的脱敏输出与截图放在 `docs/testing/evidence/`。报告注明命令、工作目录、环境、结果及对应代码版本。
- 同一功能的文档使用相同前缀，例如 `F001-favorites.md`。模板与计划标明状态，不作为已完成证据；说明调整等小任务无需重复创建整套材料。

## Git 与交付

- 开始编辑前查看工作区，保留已有未提交内容；不覆盖无关修改，不执行破坏性重置，不将密钥、真实用户数据或本地数据库备份加入版本控制。
- 用户要求提交时，仅提交本次任务相关文件，建议消息格式为 `feat(favorites): add favorite management` 或 `docs: add agent guidance`。未实际提交时不得填写虚构 Commit ID。
- 推送、创建 PR 等操作遵循当前任务授权，不因初始化本文件就自动执行。
- 完成后简要说明改动、实际验证结果和剩余限制；功能任务附相关开发记录路径，已提交时提供 Commit ID。

## 维护本文件

- 本文件只保留长期有效、可执行的项目约定。详细设计通过链接引用，一次性任务和开发结果写入相应记录。
- 初始化运行环境或改变项目约定时同步更新相关说明。未来若前后端有较多独立规则，可在对应目录新增 `AGENTS.md`，避免在根文件重复堆积细节。
