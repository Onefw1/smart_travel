# 智游北京

基于 Vue 3、TypeScript、Vite、FastAPI 和 PostgreSQL 的旅行规划项目。

当前状态：已建立项目目录骨架，已有需求与架构设计文档。业务代码、依赖配置、数据库迁移和启动入口尚未实现，当前不能直接启动应用。已有文档中的计划和验收目标不代表功能已完成。

## 项目目录

```text
travel/
├── frontend/                  # Vue 前端
│   ├── public/                # 直接发布的静态资源
│   ├── src/
│   │   ├── app/               # 应用入口、根组件、路由
│   │   ├── assets/            # 参与构建的图片、图标
│   │   ├── features/          # 按业务模块组织页面和组件
│   │   └── shared/            # API 客户端、通用组件、适配器、样式
│   └── tests/                 # 单元、组件和端到端测试
├── backend/                   # FastAPI 模块化单体
│   ├── app/
│   │   ├── core/              # 配置、权限、时钟、规则和错误处理
│   │   ├── db/                # 数据库连接、模型基类、事务
│   │   ├── modules/           # 账号、景点、收藏、行程、预约、评价、后台
│   │   └── scripts/           # 数据初始化等需要导入应用的脚本
│   ├── migrations/versions/   # Alembic 数据库迁移
│   └── tests/                 # 单元、集成测试和测试夹具
├── data/                      # 种子、示例和本地运行数据
├── scripts/                   # 项目级启动、检查、备份等脚本
├── deploy/                    # 部署配置、环境变量示例
└── docs/
    ├── requirements/          # 已有需求、用户故事、验收标准
    ├── architecture/          # 已有总体架构、模块、接口和数据设计
    ├── development/           # 单次功能任务及开发过程记录
    │   ├── features/          # Feature 范围、验收标准和完成证据
    │   ├── agent-logs/        # Agent Development Log
    │   └── trajectories/      # 典型开发过程图
    ├── testing/               # 测试方案与执行报告
    ├── deployment/            # 环境准备和部署操作说明
    └── submission/            # 作业提交清单与演示材料
```

## 业务模块

前后端统一使用 `auth`（账号）、`attractions`（景点）、`favorites`（收藏）、`plans`（行程）、`bookings`（模拟预约）、`reviews`（评价）、`admin`（管理后台）。具体边界以 [模块设计](docs/architecture/module-design.md) 为准。

后端依赖方向为 Router → Service → Repository。行程推荐与排程纯逻辑放在 `backend/app/modules/plans/domain/`，便于独立测试。前端通用能力放在 `shared/`，业务专属组件留在对应的 `features/` 中。

## 开发与作业记录

1. 从 [需求规格](docs/requirements/requirements.md) 和 [验收标准](docs/requirements/acceptance-criteria.md) 中选定一个 Feature。
2. 复制 [功能记录模板](docs/development/features/TEMPLATE.md)，明确本次范围。
3. 实现功能、编写测试，同时记录 [Agent Development Log](docs/development/agent-logs/TEMPLATE.md)。
4. 根据实际开发过程填写 [Trajectory 模板](docs/development/trajectories/TEMPLATE.md)。
5. 保存真实测试输出、人工验收证据和代码提交 ID，核对 [提交清单](docs/submission/README.md)。

文件命名建议：同一个任务使用相同前缀，例如 `F001-favorites.md`。模板中的内容需替换为实际记录，未执行的步骤保持“待执行”。

空目录中的 `.gitkeep` 用于让 Git 保留目录；加入实际文件后可删除。依赖和运行配置应在初始化前后端时加入，并保存经过验证的锁文件。
