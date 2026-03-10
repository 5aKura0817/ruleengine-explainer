# Rule Engine Explainer - Copilot Instructions

## Project Overview

Rule Engine Interface Data Translation Tool: A system that fetches rules via API, retrieves detailed rule strategy policies, translates the API response data into readable text format, and generates summaries with tags.

## Project Structure

```
.
├── ruleengine/            # Core package
│   ├── __init__.py
│   ├── config.py          # Configuration management (env vars)
│   ├── api_client.py      # API client for rule engine
│   ├── translator.py      # Rule translation logic (ASCII tree renderer)
│   └── html_exporter.py   # Interactive HTML report generator
├── main.py                # CLI entry point (subcommands: translate, list, export)
├── requirements.txt
├── .env.example
└── .github/
    └── copilot-instructions.md
```

## Architecture

**Single-Stage Pipeline:**
1. **API Retrieval** — `api_client.py` fetches rule data via REST API
2. **Translation** — `translator.py` converts JSON to human-readable text with ASCII tree conditions
3. **Export** — `main.py` writes plaintext and/or calls `html_exporter.py` for HTML report

**Module Responsibilities:**

- **`config.py`** — Reads `NCS_USER_TOKEN`, `TEAM_ID`, `BASE_URL` from `.env` / environment
- **`api_client.py`**
  - `get_rule_list(page, size)` — Paginated rule list, filters disabled rules server-side (`disabled=false`)
  - `get_rule_detail(rule_id)` — Full rule JSON including strategies
- **`translator.py`**
  - `RuleTranslator` — Extracts fields, formats metadata, delegates strategy rendering
  - `StrategyParser` — Recursively parses condition node tree; `nodeType=1` → `[且]`, `nodeType=2` → `[或]`, `nodeType=-1` → leaf
- **`html_exporter.py`**
  - `HtmlExporter.generate(rules_data)` — Produces self-contained HTML string
  - `_render_card()` — Single rule card (header-top + header-meta two-row layout)
  - `_render_leaf()` — Leaf condition row with threshold-collapse wrapper
  - `_css()` / `_js()` — Inline styles and JS (`toggleCard`, `expandAll`, `collapseAll`, `applyFilters`, `toggleThreshold`, `toggleThresholdCollapse`)

## API Configuration

### Base URL
```
https://data.ct108.net/ncs-ruleengine-api
```

### Authentication & Headers

All API requests require:

1. **Teamid Header**: Default `Teamid: 93`
2. **Authentication Cookie**: `ncs-user-token=<JWT>` — Token expires 2066-05-27 (Unix: 2087878864), no renewal needed in the near term

Example:
```
Teamid: 93
Cookie: ncs-user-token=<token_value>
```

Credentials are loaded from `.env` — never hardcode them.

## API Endpoints

### Rules List (Paginated)
```
GET /admin/rule/page?pageNum={n}&pageSize={s}&disabled=false
```

### Rule Details
```
GET /admin/rule/{ruleId}
```

### Rule Detail Response Structure

- **Basic Info**: `ruleName`, `id`, `comment`, `sourceId`, `sourceName`
- **Timing**: `startTime`, `endTime`, `createTime`, `updateTime` (timestamps in ms)
- **Creator**: `createBy`, `updateBy` (user objects with `fullname`, `username`)
- **`outputFields`**: List of output fields — `fieldCode`, `fieldName`, `valueType` / `valueTypeName`
- **`outputMessages`**: Alert messages — cooldown (`cdTime`, `cdFields`), robots, message templates
- **`strategies`**: Nested rule logic
  - `strategies.base` — Array of condition groups (usually one root node)
  - `strategies.additional` — Array of additional condition groups (omitted from output if empty)
  - Each node: `nodeType` (`1`=AND, `2`=OR, `-1`=leaf), `data.fieldName`, `data.fieldCode`, `data.operatorName`, `data.threshold`, `children[]`

## Translation Output Format

```
规则名称    {ruleName}
规则ID      {id}
数据源      {sourceName}

基础条件①
  └─[且]
     ├─ {fieldName}({fieldCode})      {operatorName}      {threshold}
     └─ {fieldName}({fieldCode})      {operatorName}      {threshold}

附加条件②
  └─[且]
     └─ {fieldName}({fieldCode})      {operatorName}      {threshold}
  [无 additional 条件时不显示此段]

生效时间③
  {startTime} - {endTime}     (HH:MM:SS)

规则说明
  {comment}

创建人    {creatorFullname}({creatorUsername})
创建时间   {date} {time}
最后更新   {date} {time}
```

**Threshold truncation**: Plaintext truncates at 60 chars with `...`; HTML never truncates data — UI shows truncated text with click-to-expand.

## Implementation Notes

- `strategies` field contains complex nested trees; handle both `base` and `additional` arrays
- Null `threshold` is normal for operators like "不为空" (NOT_NULL) — render as empty string
- Field value types: `NUMBER`, `STRING`, etc. — `valueTypeName` provides Chinese display names
- Disabled rules (`disabled: true`) are filtered server-side via `disabled=false` query param
