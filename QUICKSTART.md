# Quick Start Guide

## 5分钟快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 配置环境

```bash
cp .env.example .env
```

`.env` 文件已预配置好API凭证，无需修改。

---

## 命令速查

### 翻译单条规则

```bash
python main.py translate <规则ID>

# 示例
python main.py translate 373
```

输出示例：
```
规则名称    房间丨万州撞大胡丨丨丨辅助丨莫
规则ID      373
数据源      用户房间登录风控数据源

基础条件①
└─ [且]
   ├─ 游戏ID(game_id)   等于   265
   ├─ 房间ID(room_id)   等于   13555
   └─ 客户端IPv4(client_ipv4)   不为空

生效时间③
  00:00:00 - 23:59:59

创建人    莫晓波(moxb2705)
创建时间   2024-11-21 10:55:17
最后更新   2025-06-12 22:00:22
```

### 查看规则列表

```bash
# 查看第1页（默认每页20条，仅显示启用规则）
python main.py list

# 自定义分页
python main.py list -p 2 -s 50
```

### 批量导出（纯文本）

```bash
# 导出所有启用规则（自动生成文件名）
python main.py batch --all

# 导出前 N 条
python main.py batch -n 10

# 导出到指定文件
python main.py batch -n 5 -o my_rules.txt
```

### 导出交互式 HTML 报告 ⭐

```bash
# 导出全部启用规则为单文件 HTML（默认: rules_report.html）
python main.py html

# 指定输出路径
python main.py html -o /path/to/output.html
```

生成的 HTML 报告功能：

| 功能 | 说明 |
|------|------|
| 🔍 搜索过滤 | 右上角实时按规则名过滤 |
| 📂 展开/折叠卡片 | 点击卡片展开条件树 |
| ⚡ 展开全部 / 折叠全部 | 顶部按钮一键操作 |
| 📋 Header 元信息 | 无需展开即可看到创建人、时间 |
| 📝 阈值折叠 | 长阈值自动截断，可手动展开 |

---

## 项目结构

```
.
├── api_client.py      # API客户端
├── config.py          # 配置管理
├── translator.py      # 翻译引擎（与或树 ASCII 渲染）
├── html_exporter.py   # 交互式 HTML 报告生成器
├── main.py            # CLI入口
├── requirements.txt   # Python依赖
├── .env               # 环境配置（本地，不提交）
├── .env.example       # 环境配置模板
└── .github/
    └── copilot-instructions.md  # AI助手指引
```

---

## 常见问题

### Q: 如何修改API凭证？
**A:** 编辑 `.env` 文件：
```
API_BASE_URL=...
TEAMID=...
NCS_USER_TOKEN=...
```

### Q: 如何只导出少量规则确认效果？
**A:** 先用 `batch -n 3` 或生成3条规则的 HTML 预览：
```bash
python main.py batch -n 3
python main.py html -o rules_preview.html
```

### Q: 如何解决API连接错误？
**A:** 检查：
1. `.env` 中 `NCS_USER_TOKEN` 是否正确
2. 网络连接是否正常
3. API服务是否在线

---

详见 [README.md](README.md) 了解完整架构与设计说明。
