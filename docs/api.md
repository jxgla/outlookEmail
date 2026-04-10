# 📡 API 文档

本文档描述 `outlookEmail` 当前版本已经实现并可直接使用的 API，包括：

- 对外注册 / 邮箱池 API：`/api/external/*`
- 登录后内部管理 API：`/api/*`

当前版本已经覆盖注册接入常用的整套接口：

- `health`
- `capabilities`
- `account-status`
- `messages`
- `messages/latest`
- `messages/{id}`
- `messages/{id}/raw`
- `verification-code`
- `verification-link`
- `wait-message`
- `probe/{probe_id}`
- `pool/claim-random`
- `pool/claim-release`
- `pool/claim-complete`
- `pool/stats`

---

## 对外 API

### 鉴权方式

所有 `/api/external/*` 接口都要求提供 API Key：

```text
X-API-Key: YOUR_API_KEY
```

也支持通过查询参数传递：

```text
?api_key=YOUR_API_KEY
```

当前版本使用单一外部 Key：

- 来源：`设置 -> 对外 API Key`
- 后端配置项：`settings.external_api_key`

如果未配置或不正确，会返回：

```json
{ "success": false, "code": "UNAUTHORIZED", "message": "..." }
```

或兼容旧接口风格：

```json
{ "success": false, "error": "..." }
```

### 统一响应格式

除兼容旧接口 `GET /api/external/emails` 外，当前推荐使用的对外接口统一返回：

成功：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {}
}
```

失败：

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "错误说明",
  "data": null
}
```

时间字段统一使用 ISO 8601 UTC：

```text
2026-04-10T11:00:00Z
```

---

## 对外接口总览

### 服务探测

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/external/health` | 服务健康检查 |
| GET | `/api/external/capabilities` | 查看当前开放能力 |
| GET | `/api/external/account-status` | 检查某个邮箱是否存在且可读 |

### 邮件读取

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/external/messages` | 列出邮件摘要 |
| GET | `/api/external/messages/latest` | 获取最新匹配邮件 |
| GET | `/api/external/messages/{message_id}` | 获取邮件详情 |
| GET | `/api/external/messages/{message_id}/raw` | 获取原始邮件内容 |
| GET | `/api/external/verification-code` | 提取验证码 |
| GET | `/api/external/verification-link` | 提取验证链接 |
| GET | `/api/external/wait-message` | 等待新邮件 |
| GET | `/api/external/probe/{probe_id}` | 查询异步等待状态 |

### 邮箱池

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/external/pool/claim-random` | 随机领取一个可用邮箱 |
| POST | `/api/external/pool/claim-release` | 释放已领取邮箱 |
| POST | `/api/external/pool/claim-complete` | 回传注册结果 |
| GET | `/api/external/pool/stats` | 查看池状态统计 |

### 兼容旧接口

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/external/emails` | 旧版摘要接口，仍可用，建议新接入改用 `/api/external/messages` |

---

## 推荐接入流程

1. `GET /api/external/health`
2. `GET /api/external/capabilities`
3. `POST /api/external/pool/claim-random`
4. 从领取结果拿到 `email`
5. 调用 `verification-code` / `verification-link` / `wait-message`
6. 成功时调用 `claim-complete`
7. 放弃时调用 `claim-release`

---

## 服务探测接口

### GET /api/external/health

用途：

- 检查服务本身是否正常
- 检查数据库是否可用
- 给接入方一个简单的上游探测结果

示例：

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:5000/api/external/health"
```

关键返回字段：

- `status`
- `service`
- `version`
- `server_time_utc`
- `database`
- `upstream_probe_ok`
- `last_probe_at`
- `last_probe_error`

### GET /api/external/capabilities

用途：

- 查看当前实例开放了哪些能力
- 判断邮箱池接口是否启用

关键返回字段：

- `public_mode`
- `features`
- `restricted_features`

当前版本常见 `features` 包含：

- `message_list`
- `message_detail`
- `raw_content`
- `verification_code`
- `verification_link`
- `wait_message`
- `pool_claim_random`
- `pool_claim_release`
- `pool_claim_complete`
- `pool_stats`

### GET /api/external/account-status

参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 要检查的 Outlook 邮箱 |

关键返回字段：

- `exists`
- `email`
- `account_type`
- `provider`
- `group_id`
- `status`
- `last_refresh_at`
- `preferred_method`
- `can_read`
- `upstream_probe_ok`
- `probe_method`
- `last_probe_at`
- `last_probe_error`

---

## 邮件读取公共参数

以下参数适用于大多数对外读信接口：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 邮箱地址 |
| `folder` | string | 否 | `inbox` / `junkemail` / `deleteditems`，默认 `inbox` |
| `skip` | integer | 否 | 分页偏移，默认 `0` |
| `top` | integer | 否 | 返回数量，范围 `1-50`，默认 `20` |
| `from_contains` | string | 否 | 发件人模糊筛选 |
| `subject_contains` | string | 否 | 标题模糊筛选 |
| `since_minutes` | integer | 否 | 仅筛选最近 N 分钟邮件，必须大于 `0` |

说明：

- 当前项目是“按邮箱读信”，不是“按 claim_id 读信”
- `verification-code` / `verification-link` / `wait-message` 默认会带最近时间窗口来降低误匹配

---

## 邮件读取接口

### GET /api/external/messages

用途：

- 返回邮件摘要列表

关键返回字段：

- `email`
- `folder`
- `count`
- `has_more`
- `method`
- `emails`

### GET /api/external/messages/latest

用途：

- 返回“最新且符合筛选条件”的一封邮件摘要

### GET /api/external/messages/{message_id}

用途：

- 返回指定邮件详情

关键返回字段：

- `id`
- `email_address`
- `from_address`
- `to_address`
- `subject`
- `content`
- `html_content`
- `raw_content`
- `timestamp`
- `created_at`
- `has_html`
- `method`

### GET /api/external/messages/{message_id}/raw

用途：

- 返回指定邮件的原始 MIME / 原始正文内容
- 适合调试或接入方自己做二次解析

### GET /api/external/verification-code

用途：

- 从最近匹配邮件中提取高置信度验证码

额外参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code_length` | string | 否 | 限定验证码长度 |
| `code_regex` | string | 否 | 自定义验证码正则 |
| `code_source` | string | 否 | `subject` / `content` / `html` / `all`，默认 `all` |

默认行为：

- 如果未传 `since_minutes`，默认只搜索最近 `10` 分钟邮件
- 默认只接受带数字的验证码，避免把正文普通英文单词误判成 code

示例：

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:5000/api/external/verification-code?email=user@outlook.com&subject_contains=verify"
```

### GET /api/external/verification-link

用途：

- 从最近匹配邮件中提取验证链接

默认行为：

- 如果未传 `since_minutes`，默认只搜索最近 `10` 分钟邮件
- 会优先返回包含 `verify / activate / confirm / 验证 / 激活` 等关键字的链接

### GET /api/external/wait-message

用途：

- 等待“请求发起之后才出现”的新邮件

额外参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `timeout_seconds` | integer | 否 | 范围 `1-120`，默认 `30` |
| `poll_interval` | integer | 否 | 范围 `1-timeout_seconds`，默认 `5` |
| `mode` | string | 否 | `sync` 或 `async`，默认 `sync` |

行为说明：

- `mode=sync`：阻塞等待，命中后直接返回邮件摘要
- `mode=async`：立即返回 `probe_id`，HTTP 状态码为 `202`

### GET /api/external/probe/{probe_id}

用途：

- 查询 `wait-message?mode=async` 创建的异步任务

当前状态值：

- `pending`
- `matched`
- `timeout`
- `error`

说明：

- 当前版本的 `probe` 数据保存在进程内存中
- 服务重启后，历史 `probe_id` 不会保留

---

## 邮箱池接口

### 状态模型

当前邮箱池使用以下状态：

| 状态 | 含义 |
|------|------|
| `available` | 可领取 |
| `claimed` | 已领取，租约中 |
| `used` | 注册成功，已消耗 |
| `cooldown` | 冷却中，暂不分配 |
| `frozen` | 冻结，通常用于风控/提供商限制 |
| `retired` | 退役，不再参与分配 |

### 默认配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `pool_external_enabled` | `true` | 对外邮箱池接口开关 |
| `pool_default_lease_seconds` | `600` | 默认租约秒数 |
| `pool_cooldown_seconds` | `86400` | 默认冷却秒数 |

### POST /api/external/pool/claim-random

请求体参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `caller_id` | string | 是 | 调用方实例 / worker 标识 |
| `task_id` | string | 是 | 当前任务唯一 ID |
| `provider` | string | 否 | 当前建议传 `outlook` |

返回字段：

- `account_id`
- `email`
- `provider`
- `claim_token`
- `lease_expires_at`

无可用邮箱时，当前行为是：

- HTTP 状态码仍然是 `200`
- 响应体：`success=false`
- 错误码：`NO_AVAILABLE_ACCOUNT`

### POST /api/external/pool/claim-release

请求体参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | 是 | 领取时返回的账号 ID |
| `claim_token` | string | 是 | 领取时返回的令牌 |
| `caller_id` | string | 是 | 必须与领取时一致 |
| `task_id` | string | 是 | 必须与领取时一致 |
| `reason` | string | 否 | 释放原因 |

释放后账号会回到：

- `available`

### POST /api/external/pool/claim-complete

请求体参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | 是 | 领取时返回的账号 ID |
| `claim_token` | string | 是 | 领取时返回的令牌 |
| `caller_id` | string | 是 | 必须与领取时一致 |
| `task_id` | string | 是 | 必须与领取时一致 |
| `result` | string | 是 | 结果枚举 |
| `detail` | string | 否 | 附加说明 |

当前支持的 `result` 与状态映射：

| `result` | 含义 | 回写后的 `pool_status` |
|----------|------|------------------------|
| `success` | 注册成功 | `used` |
| `verification_timeout` | 长时间未收到验证码 | `cooldown` |
| `provider_blocked` | 提供商风控 / 受限 | `frozen` |
| `credential_invalid` | 凭据失效 | `retired` |
| `network_error` | 临时网络问题 | `available` |

### GET /api/external/pool/stats

用途：

- 返回池内各状态数量

关键返回字段：

- `pool_counts.available`
- `pool_counts.claimed`
- `pool_counts.used`
- `pool_counts.cooldown`
- `pool_counts.frozen`
- `pool_counts.retired`

### 租约超时行为

当前实现里，领取后如果长时间未回传，不会直接回到 `available`。

实际流程：

1. `claimed` 到期后自动转为 `cooldown`
2. 冷却期结束后自动恢复为 `available`

---

## 兼容旧接口

### GET /api/external/emails

这是旧版对外接口，当前仍然保留。

返回格式：

```json
{
  "success": true,
  "emails": [],
  "method": "Graph API",
  "has_more": false
}
```

新接入建议优先改到：

- `GET /api/external/messages`
- `GET /api/external/messages/latest`

---

## 内部 API（需登录）

以下接口需要登录 Web 后使用。

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/login` | 登录页 |
| POST | `/login` | 登录验证 |
| GET | `/logout` | 退出登录 |

### 分组管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/groups` | 获取所有分组 |
| GET | `/api/groups/{id}` | 获取分组详情 |
| POST | `/api/groups` | 创建分组 |
| PUT | `/api/groups/{id}` | 更新分组 |
| DELETE | `/api/groups/{id}` | 删除分组 |
| GET | `/api/groups/{id}/export` | 导出分组账号 |

### 账号管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/accounts` | 获取账号列表 |
| GET | `/api/accounts/search` | 全局搜索账号 |
| GET | `/api/accounts/{id}` | 获取单个账号详情 |
| POST | `/api/accounts` | 导入账号 |
| PUT | `/api/accounts/{id}` | 更新账号 |
| DELETE | `/api/accounts/{id}` | 删除账号 |
| DELETE | `/api/accounts/email/{email}` | 按邮箱删除账号 |
| POST | `/api/accounts/tags` | 批量打/去标签 |
| POST | `/api/accounts/batch-update-group` | 批量移动分组 |
| POST | `/api/accounts/{id}/pool-state` | 手动调整邮箱池状态 |
| GET | `/api/accounts/export` | 导出所有账号 |
| POST | `/api/accounts/export-selected` | 导出选中分组账号 |

### Token 刷新

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/accounts/refresh-all` | 全量刷新所有账号 |
| POST | `/api/accounts/{id}/refresh` | 刷新单个账号 |
| POST | `/api/accounts/refresh-failed` | 重试失败账号 |
| POST | `/api/accounts/{id}/retry-refresh` | 重试单个失败账号 |
| GET | `/api/accounts/refresh-logs` | 刷新历史 |
| GET | `/api/accounts/{id}/refresh-logs` | 单账号刷新历史 |
| GET | `/api/accounts/refresh-logs/failed` | 失败记录 |
| GET | `/api/accounts/refresh-stats` | 刷新统计 |
| GET | `/api/accounts/trigger-scheduled-refresh` | 手动触发定时刷新检查 |

### 邮件

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/emails/{email}` | 获取邮件摘要 |
| GET | `/api/email/{email}/{message_id}` | 获取邮件详情 |
| POST | `/api/emails/delete` | 批量删除邮件 |

### 临时邮箱

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/temp-emails` | 获取所有临时邮箱 |
| POST | `/api/temp-emails/import` | 批量导入临时邮箱 |
| POST | `/api/temp-emails/generate` | 生成临时邮箱 |
| DELETE | `/api/temp-emails/{email}` | 删除临时邮箱 |
| GET | `/api/temp-emails/{email}/messages` | 获取临时邮箱邮件 |
| GET | `/api/temp-emails/{email}/messages/{id}` | 获取临时邮件详情 |
| DELETE | `/api/temp-emails/{email}/messages/{id}` | 删除临时邮件 |
| DELETE | `/api/temp-emails/{email}/clear` | 清空临时邮箱 |
| POST | `/api/temp-emails/{email}/refresh` | 刷新临时邮箱 |
| GET | `/api/duckmail/domains` | 获取 DuckMail 域名 |

### 标签

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tags` | 获取标签列表 |
| POST | `/api/tags` | 创建标签 |
| DELETE | `/api/tags/{id}` | 删除标签 |

### 系统 / 设置 / 池状态

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/settings` | 获取系统设置 |
| PUT | `/api/settings` | 更新系统设置 |
| POST | `/api/settings/validate-cron` | 校验 Cron 表达式 |
| GET | `/api/pool/stats` | 获取页面端邮箱池统计 |
| GET | `/api/csrf-token` | 获取 CSRF Token |

### OAuth2 助手

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/oauth/auth-url` | 生成授权 URL |
| POST | `/api/oauth/exchange-token` | 换取 Refresh Token |

---

## 读取优先级与代理说明

当前 Outlook 读信相关接口会按以下优先级自动尝试：

| 优先级 | 方式 | 说明 |
|--------|------|------|
| 1 | Graph API | 推荐方式，支持最完整 |
| 2 | IMAP（新） | `outlook.live.com` |
| 3 | IMAP（旧） | `outlook.office365.com` |

说明：

- 如果 Graph API 失败原因是代理连接错误，则不会继续回退 IMAP
- 仅 Graph API 请求支持分组代理
- IMAP 当前不支持代理

支持的代理格式：

```text
http://127.0.0.1:7890
socks5://127.0.0.1:7891
socks5://user:pass@proxy.example.com:1080
```

---

## 常见错误码

| 错误码 | 典型场景 |
|--------|----------|
| `UNAUTHORIZED` | 缺少 API Key 或 Key 不正确 |
| `FEATURE_DISABLED` | 邮箱池接口已被关闭 |
| `INVALID_PARAM` | 参数错误 |
| `ACCOUNT_NOT_FOUND` | 账号不存在 |
| `ACCOUNT_ACCESS_FORBIDDEN` | 账号存在但当前不可读 |
| `MAIL_NOT_FOUND` | 未找到匹配邮件 |
| `VERIFICATION_CODE_NOT_FOUND` | 未提取到验证码 |
| `VERIFICATION_LINK_NOT_FOUND` | 未提取到验证链接 |
| `UPSTREAM_READ_FAILED` | Graph / IMAP 读取失败 |
| `PROXY_ERROR` | 代理连接失败 |
| `NO_AVAILABLE_ACCOUNT` | 池中没有可用账号 |
| `TOKEN_MISMATCH` | `claim_token` 不匹配 |
| `CALLER_MISMATCH` | `caller_id` 或 `task_id` 与领取记录不一致 |
| `NOT_CLAIMED` | 账号当前不在 `claimed` 状态 |

---

## 备注

- 本项目的接口文档以当前仓库实际实现行为为准
- 如果你之前只使用 `GET /api/external/emails`，建议迁移到 `/api/external/messages*` + `/api/external/pool/*`
- 页面端已经内置“注册 / 邮箱池 API”面板，可直接查看池统计、当前账号池状态、API 示例
