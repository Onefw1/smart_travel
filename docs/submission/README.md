# 作业提交清单

当前提交主题：**F001 注册、登录与会话权限**，包含注册确认密码、普通用户/管理员登录、会话恢复、安全退出和角色保护。以下按用户提供的课程截图逐项核对。

- [x] 完成一个真实 Feature：[功能范围及验收](../development/features/F001-auth.md)。
- [x] Commit Code：已有实际提交 `39b26758c67bec9708821ff36fc6a88c7cb9426f`，消息为 `feat(auth): implement account flow and project startup`；本轮另归档最终验收补充。
- [x] Add Tests：`backend/tests/unit/test_auth_rules.py`、`backend/tests/integration/test_auth_api.py`、`frontend/tests/`，覆盖正常、边界、权限、事务与确认密码等行为。
- [x] Pass Tests：最终账号后端 **71**、前端 **26**、真实浏览器 **20** 项通过，无跳过；[最终测试报告](../testing/reports/F001-auth-submission.md)。
- [x] Agent Development Log：[完整开发日志](../development/agent-logs/F001-auth.md)，记录实际指令、决策、操作、失败、修复与结果。
- [x] Trajectory：[Markdown 源记录](../development/trajectories/F001-auth.md)、[可直接查看的 PNG](../development/trajectories/F001-auth-submission.png)、[SVG](../development/trajectories/F001-auth-submission.svg)、[DOT 绘图源](../development/trajectories/F001-auth-submission.dot)。
- [x] 演示与证据：[演示步骤](demo/F001-auth-demo.md)、[测试与截图](../testing/evidence/)。
- [ ] “团队协同”的人数要求：用户已明确**仅本人参与**，没有多人小组协作证据；若课程必须由多人组队，需向教师确认单人是否可交，不能补写不存在的分工或评审。

## 提交内容与阅读顺序

1. 本文件：核对课程要求，明确范围、提交与单人参与情况。
2. `docs/development/features/F001-auth.md`：实际实现的 Feature。
3. `docs/development/agent-logs/F001-auth.md`：Agent Development Log。
4. `docs/development/trajectories/F001-auth-submission.png`：直接查看的一次真实典型开发过程；Markdown 保留较完整历史。
5. `docs/testing/reports/F001-auth-submission.md`：最终版本的命令、环境、结果与证据索引。
6. `backend/`、`frontend/`：代码、迁移、依赖声明/锁文件及测试；两端 README 给出复现步骤。

截图只要求一个 Feature，本包不声称完成整个旅行系统。管理员业务管理、景点、行程、预约、评价仍未实现，不影响对本次账号 Feature 的说明。人工验收尚未由用户确认，性能和真实手机硬件验收不在本次证明范围。

## 参与情况

实际人类参与者：聊天用户本人（单人，未提供姓名/学号）。用户负责选择功能范围、提供数据库配置、提出确认密码改动及检查提交要求；Codex 负责按指令实现、添加测试、执行验证、修复和整理材料。本记录体现实际人机协作，不将其改写为多人小组分工。

## 导出

提交时优先使用 Git 源码归档，保留实际提交记录（例如附 `git log --oneline -3`）。归档不能包含 `.env`、虚拟环境、node_modules、开发/测试数据库或实际管理员口令。当前真实运行环境中的这些本地文件不作为作业附件。

```powershell
git log --oneline -3
git archive --format=zip --output=F001-auth-submission.zip HEAD
```

本轮生成的可下载归档位于被忽略的 `data/local/submission/`；归档以最终提交为源，不把未跟踪的本地数据打包。
