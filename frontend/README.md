# 前端目录

规划技术栈：Vue 3、TypeScript、Vite、Vue Router、Pinia。当前只创建目录，尚无运行入口或依赖配置。

| 路径 | 放置内容 |
| --- | --- |
| `src/app/` | 后续的 `main.ts`、`App.vue`、`router.ts` |
| `src/features/<模块>/pages/` | 业务页面 |
| `src/features/<模块>/components/` | 业务专属组件 |
| `src/features/<模块>/` | 后续的 `api.ts`、`types.ts` 和必要的状态管理 |
| `src/shared/api/` | 统一客户端、错误解析和接口公共类型 |
| `src/shared/components/` | 分页、加载、空状态等通用组件 |
| `src/shared/adapters/` | 地图等适配器 |
| `src/shared/styles/` | 全局样式 |
| `src/assets/` | 构建时处理的图片和图标 |
| `public/` | 原样发布的公开静态资源，不放敏感信息 |
| `tests/unit/` | 工具与状态逻辑测试 |
| `tests/components/` | 组件交互测试 |
| `tests/e2e/` | 完整用户流程测试 |
| `tests/fixtures/` | 测试专用输入与模拟响应 |

开发时按架构设计将 `/api` 和 `/health` 代理到后端。具体依赖版本、配置文件和测试命令在初始化应用时确认。
