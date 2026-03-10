# Rule Engine Explainer

将规则引擎API返回的复杂JSON数据转译为易读的规则配置文本/HTML格式。

## Features

✅ 分页查询规则列表（自动过滤已禁用规则）  
✅ 获取单条规则详情  
✅ 将嵌套与或树条件翻译为可读文本（`[且]` / `[或]` + ASCII树形结构）  
✅ 格式化时间戳与生效时间段  
✅ 支持基础条件与附加条件双树渲染  
✅ 批量导出为纯文本报告  
✅ **导出为交互式单文件 HTML 报告**  
✅ HTML 支持搜索过滤、一键展开/折叠所有卡片  
✅ 阈值过长时自动折叠，可手动展开查看完整内容  
✅ 卡片 header 直接显示创建人、创建时间、更新时间  

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and add credentials
cp .env.example .env
# Edit .env and add your NCS_USER_TOKEN
```

## Usage

### Translate a Single Rule

```bash
python main.py translate 373
```

Output:
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

### List Rules

```bash
# List first page of rules (default: 20 per page, only enabled rules)
python main.py list

# List with custom pagination
python main.py list -p 2 -s 50
```

**Note:** Only enabled rules are displayed. Disabled rules are automatically filtered out.

### Batch Translate and Export (Plain Text)

```bash
# 导出所有启用规则到自动命名文件
python main.py batch --all

# 导出前 N 条
python main.py batch -n 10

# 导出到指定文件
python main.py batch -n 5 -o my_rules.txt
```

**Output File Example:**
```
======================================================================
规则引擎数据转译 - 批量导出报告
生成时间: 2026-03-09 22:47:13
规则总数: 3
======================================================================

【第 1 条规则】
──────────────────────────────────────────────────────────────────────
规则名称    对局丨苏州麻将丨丨丨丨低充值低经验丨莫
规则ID      1082
数据源      用户对局风控数据源

基础条件①
  游戏ID(game_id)      等于      40
  且
  房间ID(room_id)      等于      24067,19013
  且
  历史胜局数(history_win)      小于或等于      200

附加条件②
  用户过去7天充值金额_分_全平台(dl_ct_pay_money_7d)      小于或等于      1000

生效时间③
  00:00:00 - 23:59:59
...
```

### Export as Interactive HTML

```bash
# 导出所有启用规则为单文件 HTML（默认输出 rules_report.html）
python main.py html

# 指定输出路径
python main.py html -o /path/to/output.html
```

**HTML 功能特性：**
- 🔍 **搜索过滤**：右上角搜索框，实时按规则名过滤卡片
- 📂 **展开/折叠**：每张卡片可独立点击展开查看完整条件树
- ⚡ **全局操作**：顶部 `展开全部` / `折叠全部` 一键操作所有卡片
- 📋 **Header 元信息**：无需展开即可在卡片标题行看到创建人、创建时间、更新时间
- 📝 **阈值折叠**：阈值超过 60 字符时自动截断，点击 `展开` 查看完整值，点击 `收起` 折回

## Project Structure

```
.
├── config.py          # Configuration management
├── api_client.py      # API client for rule engine
├── translator.py      # Rule translation logic (ASCII tree renderer)
├── html_exporter.py   # Interactive HTML report generator
├── main.py            # Command-line interface
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
└── .github/
    └── copilot-instructions.md  # AI assistant instructions
```

## API Configuration

The tool requires:
- **Base URL**: `https://data.ct108.net/ncs-ruleengine-api`
- **Authentication**: 
  - Header: `Teamid: 93`
  - Cookie: `ncs-user-token=<JWT_TOKEN>`

These are configured in `.env` file.

## Architecture

### 1. API Client (`api_client.py`)
- `get_rule_list()`: Fetch paginated rule list
- `get_rule_detail()`: Fetch detailed rule configuration

### 2. Translator (`translator.py`)
- `RuleTranslator`: Main translation engine
  - Extracts fields from API response
  - Formats conditions and metadata
- `StrategyParser`: Handles nested strategy tree
  - Recursively parses condition nodes
  - Converts to human-readable format

### 3. HTML Exporter (`html_exporter.py`)
- `HtmlExporter.generate(rules_data)`: 生成完整 HTML 字符串
- `_render_card()`: 单条规则卡片 HTML（含 header-top + header-meta 两行布局）
- `_render_leaf()`: 叶节点条件行，含阈值折叠 wrapper
- `_css()`: 所有内联样式
- `_js()`: `toggleCard`, `expandAll`, `collapseAll`, `filterCards`, `toggleThreshold`, `toggleThresholdCollapse`

### 4. Main Entry Point (`main.py`)
- CLI interface with subcommands
- Integrates API client and translator

## Output Format

The translator converts API JSON into structured text matching the management UI:

```
规则名称    {ruleName}
规则ID      {id}
数据源      {sourceName}

基础条件①
  {field1}({code1})      {operator1}      {value1}
  且
  {field2}({code2})      {operator2}      {value2}

附加条件②
  [Additional conditions if any]

生效时间③
  {startTime} - {endTime}

规则说明
  {comment}

创建人    {creatorName}({username})
创建时间   {createdDate} {createdTime}
最后更新   {updatedDate} {updatedTime}
```

## Notes

- Token expires at 2066-05-27, no renewal needed for years
- Handles null thresholds for operators like "不为空" (NOT_NULL)
- Recursively processes nested condition structures
- Supports both base and additional criteria

## Threshold Truncation

Long threshold values (e.g., lists of 100+ user IDs) are automatically truncated to improve readability:

```
Before:
  用户ID(user_id)      等于      243884946,210206570,210205650,140222156,251590946,...[60+ more values]

After:
  用户ID(user_id)      等于      243884946,210206570,210205650,140222156,251590946,251615552,...

Maximum threshold display: 60 characters
```

This ensures that terminal output remains readable while preserving the first part of the value, which is usually the most important information.
