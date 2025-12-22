# MaimWebBackend API 文档

**基础 URL**: `http://<host>:8880/api/v1`

**说明**: 本服务是面向前端的 Web 后端，负责用户认证和资源管理，大部分资源操作会代理到 `MaimConfig` 服务。

**认证**: 所有非 `/auth` 接口均需 Bearer Token 认证。

## 1. 认证模块 (/auth)
- **POST /auth/register** 用户注册
  - Body: `{ username, password, email? }`
- **POST /auth/login** 用户登录
  - Body: `FormData: username, password`
  - Resp: `{ access_token, token_type: "bearer" }`

## 2. Agent 管理 (/agents)
- **GET /agents/** 获取 Agent 列表
  - Params: `skip`, `limit`
  - 说明: 返回当前用户所有租户下的 Agent
- **POST /agents/** 创建 Agent
  - Body: `{ name, description?, config?, template_id? }`
  - 说明: 默认在用户的第一个租户下创建
- **GET /agents/{id}** 获取 Agent 详情
- **PUT /agents/{id}** 更新 Agent
- **POST /agents/{id}/api_keys** 创建 API Key
  - Body: `{ name, description?, permissions[] }`
- **GET /agents/{id}/api_keys** 获取 API Key 列表
- **DELETE /agents/{id}/api_keys/{key_id}** 删除 API Key

## 3. 插件配置 (/plugins)
- **POST /plugins/settings** 配置插件 (Proxy)
  - Query: `agent_id`
  - Body: `{ plugin_name, enabled, config }`
  - 说明: 代理到 MaimConfig 的 `/api/v1/plugins/settings`，用于前端开关和配置插件。

## 4. 健康检查
- **GET /health**
- **GET /** (Root)
