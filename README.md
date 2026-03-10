# Rule Engine Explainer

将规则引擎 API 返回的复杂 JSON 数据转译为易读的规则配置文本 / HTML 格式。

## Installation

```bash
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，填入 NCS_USER_TOKEN
```

## Configuration

在 `.env` 中配置以下环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NCS_USER_TOKEN` | API 鉴权 JWT Token（必填） | — |
| `TEAM_ID` | 团队 ID | `93` |
| `BASE_URL` | API 基础地址 | `https://data.ct108.net/ncs-ruleengine-api` |

`.env.example` 提供了模板，复制后填入 Token 即可。

## Usage

### 翻译单条规则

```bash
python main.py translate <ruleId>
```

### 列出规则

```bash
# 默认第 1 页，每页 20 条（仅显示已启用规则）
python main.py list

# 自定义分页
python main.py list -p 2 -s 50
```

### 导出规则

```bash
# 导出全部规则（默认同时生成 HTML 和纯文本到 ./output/overview.{html,txt}）
python main.py export

# 仅导出纯文本
python main.py export --type plaintext

# 仅导出 HTML
python main.py export --type html

# 指定输出路径前缀
python main.py export -o ./output/custom

# 只导出前 N 条
python main.py export -n 10
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件路径前缀（不含扩展名） | `./output/overview` |
| `-n, --number` | 最多导出条数（0 = 全部） | `0` |
| `--type` | 导出格式：`all` / `html` / `plaintext` | `all` |

### HTML 报告功能

- 🔍 实时搜索过滤规则名
- 📂 卡片独立展开 / 折叠条件树
- ⚡ 一键展开全部 / 折叠全部
- 📋 卡片标题行直接显示创建人、时间
- 📝 阈值超过 60 字符自动截断，可点击展开完整值
