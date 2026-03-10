# Rule Engine Explainer - Copilot Instructions

## Project Overview

Rule Engine Interface Data Translation Tool: A system that fetches rules via API, retrieves detailed rule strategy policies, translates the API response data into readable text format, and generates summaries with tags.

## API Configuration

### Base URL
```
https://data.ct108.net/ncs-ruleengine-api
```

### Authentication & Headers

All API requests require:

1. **Teamid Header**: Default `Teamid: 93` (add to request headers)
2. **Authentication Cookie**: 
   - Name: `ncs-user-token`
   - Value: `eyJ0eXAiOiJKV1QiLCJ0eXBlIjoiSldUIiwiYWxnIjoiSFMyNTYifQ.eyJ1aWQiOiJGRUEzNjhCNjNCNkNERDdFOUMxQzU3OUYxRjlFREJGOCIsInJlcXVlc3RfdXVpZCI6IiIsImVuYWJsZSI6MSwiZG9tYWluIjoiZGF0YS5jdDEwOC5uZXQiLCJndWlkIjpudWxsLCJvcmlHdWlkIjpudWxsLCJmdWxsbmFtZSI6IkQyMDE3NEQzOERFNzk0N0QyRTc3QzU0QTBFRkM0NEIxIiwiZXhwIjoyMDg3ODc4ODY0LCJ1c2VybmFtZSI6IkI2MkIxMTUzQzhFNkQ5MUY3MjA5RTU2RThENEJBNDRGIn0.at6118GorFosuq660EEeJZgiTy1VGxpEKzWhiQqVMpo_1st`
   - Note: Token expires at 2066-05-27 (Unix timestamp: 2087878864)

Example request headers:
```
Teamid: 93
Cookie: ncs-user-token=<token_value>
```

## API Endpoints

### Rules List (Paginated)
```
GET /admin/rule/page
```

**Parameters:**
- `pageNum`: Page number (1-indexed)
- `pageSize`: Number of rules per page
- `disabled`: Filter by status — pass `false` to return only enabled rules (server-side filtering)

**Example:**
```
GET https://data.ct108.net/ncs-ruleengine-api/admin/rule/page?pageNum=1&pageSize=50&disabled=false
Headers:
  Teamid: 93
  Cookie: ncs-user-token=<token>
```

### Rule Details
```
GET /admin/rule/{ruleId}
```

**Parameters:**
- `ruleId`: The rule ID (corresponds to `id` field from paginated rules list)

**Example:**
```
GET https://data.ct108.net/ncs-ruleengine-api/admin/rule/1082
Headers:
  Teamid: 93
  Cookie: ncs-user-token=<token>
```

## Architecture

The application translates rule API response into Tab1 "规则配置" (Rule Configuration) format:

**Single-Stage Pipeline:**
1. **API Retrieval**: Fetch rule detail via `/admin/rule/{ruleId}`
2. **Translation**: Convert JSON response to human-readable "规则配置" text format matching the UI display

## Rule Detail Response Structure

Each rule detail response (`GET /admin/rule/{ruleId}`) contains:

- **Basic Info**: ruleName, id, comment, sourceId, sourceName
- **Timing**: startTime, endTime, createTime, updateTime
- **Creator**: createBy, updateBy (user objects)
- **outputFields**: List of output data fields with fieldCode, fieldName, valueType
- **outputMessages**: Alert/notification messages triggered by the rule, including:
  - Cooldown configuration (cdTime, cdFields)
  - Associated robots/systems (robots, robotNames)
  - Message templates
- **strategies**: Complex nested rule logic with base and additional criteria
  - `strategies.base`: Array of condition groups (usually one)
  - `strategies.additional`: Array of additional condition groups
  - Each condition node contains:
    - `data.fieldName` / `data.fieldCode`: Field being evaluated
    - `data.operatorName`: Human-readable operator (e.g., "等于", "不为空")
    - `data.threshold`: The comparison value (parameter)
    - `children`: Sub-conditions for nested logic

## Implementation Notes

- Store the Teamid and authentication token in configuration (environment variables or config file) rather than hardcoding
- Consider token expiration and implement refresh/renewal logic before the token expires
- The `strategies` field contains complex nested rule definitions with base and additional criteria
- Each rule can have multiple output messages with different trigger conditions
- Handle field value types: NUMBER, STRING, etc. (valueTypeName provides Chinese display names)
- When listing rules, filter out disabled rules (disabled: true) to show only active rules

## Translation Output Format - "规则配置" Tab Only

Convert rule JSON into text format matching the management UI's Tab1 display:

**Exact Output Format:**

```
规则名称    {ruleName}
规则ID      {id}
数据源      {sourceName}

基础条件①
  {fieldName}({fieldCode})      {operatorName}      {threshold}
  且
  {fieldName}({fieldCode})      {operatorName}      {threshold}
  [继续显示其他条件，以"且"连接]

附加条件②
  [如果有additional条件，同样显示；如果无则不显示此段]

生效时间③
  {startTime} - {endTime}     (HH:MM:SS 格式)

规则说明
  {comment}

创建人    {creatorFullname}({creatorUsername})
创建时间   {formatCreatedDate} {formatCreatedTime}
最后更新   {formatUpdatedDate} {formatUpdatedTime}
```

**示例输出 (Rule 373):**

```
规则名称    房间丨万州撞大胡丨丨丨辅助丨莫
规则ID      373
数据源      用户房间登录风控数据源

基础条件①
  游戏ID(game_id)      等于      265
  且
  房间ID(room_id)      等于      13555
  且
  客户端IPv4(client_ipv4)      不为空

生效时间③
  00:00:00 - 23:59:59

规则说明
  

创建人    莫晓波(moxb2705)
创建时间   2024-11-21 10:55:17
最后更新   2025-06-12 22:00:22
```
