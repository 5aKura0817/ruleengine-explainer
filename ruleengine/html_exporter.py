from datetime import datetime
from typing import Any, Dict, List


def _format_threshold(threshold) -> str:
    """Translate boolean threshold values (no truncation — HTML handles display)."""
    if threshold is None:
        return ""
    s = str(threshold)
    if s.lower() == "true":
        return "是"
    if s.lower() == "false":
        return "否"
    return s


def _format_timestamp(ts_ms: int) -> str:
    if not ts_ms:
        return ""
    try:
        return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _format_time_range(start_s: int, end_s: int) -> str:
    def fmt(s):
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{fmt(start_s)} – {fmt(end_s)}"


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class HtmlExporter:
    """Generate a self-contained single HTML file for all translated rules."""

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate(rules_data: List[Dict[str, Any]]) -> str:
        """Return a full HTML page string for the given list of rule detail dicts."""
        cards_html = "\n".join(
            HtmlExporter._render_card(rule) for rule in rules_data
        )
        unique_sources = sorted(set(
            rule.get("sourceName", "").strip()
            for rule in rules_data
            if rule.get("sourceName", "").strip()
        ))
        return HtmlExporter._page_template(len(rules_data), cards_html, unique_sources)

    # ------------------------------------------------------------------ #
    #  Card rendering                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _render_card(rule: Dict[str, Any]) -> str:
        rule_id = rule.get("id", "")
        rule_name = _html_escape(rule.get("ruleName", ""))
        source_name = _html_escape(rule.get("sourceName", ""))

        create_by = rule.get("createBy") or {}
        creator = _html_escape(
            f"{create_by.get('fullname', '')}({create_by.get('username', '')})"
        )
        create_time = _format_timestamp(rule.get("createTime", 0))
        update_time = _format_timestamp(rule.get("updateTime", 0))

        header = (
            f'<div class="card-header" onclick="toggleCard(this)">'
            f'<span class="toggle-icon">▶</span>'
            f'<div class="header-main">'
            f'<div class="header-top">'
            f'<span class="rule-id">#{rule_id}</span>'
            f'<span class="rule-name">{rule_name}</span>'
            f'<span class="rule-source">{source_name}</span>'
            f'</div>'
            f'<div class="header-meta">'
            f'<span>{creator}</span>'
            f'<span>创建 {create_time}</span>'
            f'<span>更新 {update_time}</span>'
            f'</div>'
            f'</div>'
            f"</div>"
        )

        body_parts = []

        strategies = rule.get("strategies", {})

        base = strategies.get("base", [])
        if base:
            body_parts.append(HtmlExporter._render_strategy_section("基础条件①", base))

        additional = strategies.get("additional", [])
        if additional:
            body_parts.append(
                HtmlExporter._render_strategy_section("附加条件②", additional)
            )

        # Effective time
        start_time = rule.get("startTime", 0)
        end_time = rule.get("endTime", 86399)
        time_range = _format_time_range(start_time, end_time)
        body_parts.append(
            f'<div class="meta-row">'
            f'<span class="meta-label">生效时间③</span>'
            f'<span class="meta-value">{_html_escape(time_range)}</span>'
            f"</div>"
        )

        # Comment
        comment = (rule.get("comment") or "").strip()
        if comment:
            body_parts.append(
                f'<div class="meta-row">'
                f'<span class="meta-label">规则说明</span>'
                f'<span class="meta-value comment">{_html_escape(comment)}</span>'
                f"</div>"
            )

        body_html = "\n".join(body_parts)

        # data-search and data-sourcename attributes for JS filtering
        search_text = f"{rule_id} {rule.get('ruleName', '')} {source_name}".lower()
        raw_source = rule.get("sourceName", "").strip()

        return (
            f'<div class="card" data-search="{_html_escape(search_text)}" data-sourcename="{_html_escape(raw_source)}">'
            f"{header}"
            f'<div class="card-body">{body_html}</div>'
            f"</div>"
        )

    # ------------------------------------------------------------------ #
    #  Condition tree rendering                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _render_strategy_section(label: str, strategies: List[Dict[str, Any]]) -> str:
        nodes_html = "".join(
            HtmlExporter._render_tree_node(node) for node in strategies
        )
        return (
            f'<div class="strategy-section">'
            f'<div class="strategy-label">{label}</div>'
            f'<div class="tree-root">{nodes_html}</div>'
            f"</div>"
        )

    @staticmethod
    def _render_tree_node(node: Dict[str, Any]) -> str:
        node_type = node.get("nodeType", -1)
        children = node.get("children") or []

        # Leaf node
        if node_type == -1 or not children:
            data = node.get("data") or {}
            if not data.get("fieldName"):
                return ""
            return HtmlExporter._render_leaf(data)

        # Compound node
        label = "且" if node_type == 1 else "或"
        badge_class = "badge-and" if node_type == 1 else "badge-or"

        children_html = "".join(
            HtmlExporter._render_tree_node(child) for child in children
        )

        return (
            f'<div class="tree-node">'
            f'<span class="badge {badge_class}">{label}</span>'
            f'<div class="tree-children">{children_html}</div>'
            f"</div>"
        )

    @staticmethod
    def _render_leaf(data: Dict[str, Any]) -> str:
        field_name = _html_escape(data.get("fieldName", ""))
        field_code = _html_escape(data.get("fieldCode", ""))
        operator_name = _html_escape(data.get("operatorName", ""))
        raw = _format_threshold(data.get("threshold"))

        THRESHOLD_MAX = 60
        if len(raw) > THRESHOLD_MAX:
            short = _html_escape(raw[:THRESHOLD_MAX])
            full = _html_escape(raw)
            # Wrapper keeps condition row intact; full text shown as a block below
            return (
                f'<div class="threshold-wrapper">'
                f'<div class="leaf-condition">'
                f'<span class="field-name">{field_name}</span>'
                f'<span class="field-code">({field_code})</span>'
                f'<span class="operator">{operator_name}</span>'
                f'<span class="threshold">{short}…</span>'
                f'<button class="threshold-toggle" onclick="toggleThreshold(this)">展开</button>'
                f'</div>'
                f'<div class="threshold-full-block">{full}</div>'
                f'</div>'
            )

        return (
            f'<div class="leaf-condition">'
            f'<span class="field-name">{field_name}</span>'
            f'<span class="field-code">({field_code})</span>'
            f'<span class="operator">{operator_name}</span>'
            f'<span class="threshold">{_html_escape(raw)}</span>'
            f"</div>"
        )

    # ------------------------------------------------------------------ #
    #  Page template, CSS, JS                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _page_template(total: int, cards_html: str, unique_sources: List[str] = None) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        css = HtmlExporter._css()
        js = HtmlExporter._js()
        source_options = '<option value="">全部数据源</option>\n'
        if unique_sources:
            source_options += "\n".join(
                f'      <option value="{_html_escape(s)}">{_html_escape(s)}</option>'
                for s in unique_sources
            )
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>规则引擎转译一览</title>
<style>
{css}
</style>
</head>
<body>
<div class="page-header">
  <div class="page-title">规则引擎转译一览</div>
  <div class="header-right">
    <input type="text" id="search" class="search-box" placeholder="搜索规则名称 / ID…" oninput="applyFilters()">
    <select id="sourceFilter" class="source-filter" onchange="applyFilters()">
      {source_options}
    </select>
    <button class="action-btn" onclick="expandAll()">展开全部</button>
    <button class="action-btn" onclick="collapseAll()">折叠全部</button>
    <span class="total-count" id="count-label">{total} 条规则</span>
  </div>
</div>
<div class="page-meta">生成时间：{now}</div>
<div class="cards-container" id="cards">
{cards_html}
</div>
<script>
{js}
</script>
</body>
</html>"""

    @staticmethod
    def _css() -> str:
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  font-size: 14px;
  background: #f5f6fa;
  color: #333;
}

/* ── Header ── */
.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #1e2a3a;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,.3);
}
.page-title { font-size: 18px; font-weight: 600; letter-spacing: .5px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.search-box {
  width: 280px;
  padding: 7px 12px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: #2d3e52;
  color: #fff;
}
.search-box::placeholder { color: #8a9bb0; }
.search-box:focus { background: #374f67; }
.source-filter {
  padding: 7px 10px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: #2d3e52;
  color: #fff;
  cursor: pointer;
  max-width: 220px;
}
.source-filter option { background: #1e2a3a; color: #fff; }
.source-filter:focus { background: #374f67; }
.total-count { font-size: 13px; color: #8a9bb0; white-space: nowrap; }

.page-meta {
  padding: 6px 24px;
  font-size: 12px;
  color: #888;
  background: #eef0f5;
  border-bottom: 1px solid #dde1ea;
}

/* ── Cards container ── */
.cards-container {
  max-width: 1100px;
  margin: 20px auto;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ── Card ── */
.card {
  background: #fff;
  border: 1px solid #dde1ea;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
  transition: box-shadow .15s;
}
.card:hover { box-shadow: 0 3px 10px rgba(0,0,0,.1); }

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
  background: #fafbfc;
  border-bottom: 1px solid transparent;
  transition: background .1s;
}
.card-header:hover { background: #f0f2f7; }
.card.open .card-header { border-bottom-color: #dde1ea; }

.header-main { flex: 1; min-width: 0; }
.header-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-meta {
  display: flex;
  gap: 16px;
  margin-top: 3px;
  font-size: 11px;
  color: #999;
}

.toggle-icon {
  font-size: 11px;
  color: #888;
  transition: transform .2s;
  flex-shrink: 0;
}
.card.open .toggle-icon { transform: rotate(90deg); }

.rule-id {
  font-size: 12px;
  font-weight: 600;
  color: #5a7fa8;
  font-family: monospace;
  flex-shrink: 0;
}
.rule-name {
  font-weight: 600;
  color: #222;
  flex: 1;
}
.rule-source {
  font-size: 12px;
  color: #888;
  flex-shrink: 0;
}

.card-body {
  display: none;
  padding: 16px;
}
.card.open .card-body { display: block; }

/* ── Strategy section ── */
.strategy-section {
  margin-bottom: 14px;
}
.strategy-label {
  font-size: 12px;
  font-weight: 700;
  color: #5a7fa8;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: .4px;
}

/* ── Tree ── */
.tree-root { padding-left: 4px; }

.tree-node {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 4px 0;
}

.tree-children {
  padding-left: 24px;
  border-left: 2px solid #e0e6f0;
  margin-left: 12px;
  margin-top: 4px;
}

.badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .5px;
  width: fit-content;
}
.badge-and {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}
.badge-or {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

/* ── Leaf condition ── */
.leaf-condition {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 13px;
  margin: 2px 0;
}
.leaf-condition:hover { background: #f5f7fb; }
.field-name { color: #444; font-weight: 500; }
.field-code { color: #aaa; font-size: 11px; font-family: monospace; }
.operator { color: #5a7fa8; font-weight: 600; padding: 0 4px; }
.threshold {
  color: #1e293b;
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
}

/* ── Meta ── */
.meta-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
  margin-bottom: 6px;
  align-items: baseline;
}
.meta-label { color: #5a7fa8; font-weight: 600; flex-shrink: 0; }
.meta-value { color: #555; }
.meta-value.comment { color: #777; font-style: italic; }

.hidden { display: none !important; }

/* ── Action buttons (expand/collapse all) ── */
.action-btn {
  padding: 5px 12px;
  border: 1px solid #4a6a8a;
  border-radius: 5px;
  background: transparent;
  color: #c8d8e8;
  font-size: 12px;
  cursor: pointer;
  transition: background .1s, color .1s;
  white-space: nowrap;
}
.action-btn:hover {
  background: #2d3e52;
  color: #fff;
}

/* ── Threshold collapse ── */
.threshold-wrapper { margin: 2px 0; }
.threshold-full-block {
  display: none;
  font-family: monospace;
  font-size: 12px;
  color: #1e293b;
  word-break: break-all;
  padding: 4px 8px;
  margin: 2px 6px 4px;
  background: #f4f6fb;
  border-left: 2px solid #c8d4e8;
  border-radius: 0 3px 3px 0;
}
.threshold-toggle {
  background: none;
  border: none;
  color: #5a7fa8;
  cursor: pointer;
  font-size: 11px;
  padding: 0 3px;
  text-decoration: underline;
  font-family: inherit;
}
.threshold-toggle:hover { color: #1e40af; }
"""

    @staticmethod
    def _js() -> str:
        return """
function toggleCard(header) {
  header.parentElement.classList.toggle('open');
}

function expandAll() {
  document.querySelectorAll('.card:not(.hidden)').forEach(c => c.classList.add('open'));
}

function collapseAll() {
  document.querySelectorAll('.card:not(.hidden)').forEach(c => c.classList.remove('open'));
}

function applyFilters() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const source = document.getElementById('sourceFilter').value;
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(card => {
    const matchSearch = !q || card.dataset.search.includes(q);
    const matchSource = !source || card.dataset.sourcename === source;
    const match = matchSearch && matchSource;
    card.classList.toggle('hidden', !match);
    if (match) visible++;
  });
  const total = cards.length;
  const isFiltered = q || source;
  document.getElementById('count-label').textContent =
    isFiltered ? visible + ' / ' + total + ' 条规则' : total + ' 条规则';
}

// Keep backward-compatible alias used by search input
function filterCards(query) { applyFilters(); }

function toggleThreshold(btn) {
  // btn lives inside .leaf-condition which is inside .threshold-wrapper
  const wrapper = btn.closest('.threshold-wrapper');
  const shortThreshold = wrapper.querySelector('.threshold');
  const fullBlock = wrapper.querySelector('.threshold-full-block');
  const isExpanded = fullBlock.style.display === 'block';
  shortThreshold.style.display = isExpanded ? '' : 'none';
  btn.style.display = isExpanded ? '' : 'none';
  fullBlock.style.display = isExpanded ? 'none' : 'block';
  // Add a collapse button inside fullBlock on first expand
  if (!isExpanded && !fullBlock.querySelector('.threshold-toggle')) {
    const collapseBtn = document.createElement('button');
    collapseBtn.className = 'threshold-toggle';
    collapseBtn.textContent = '收起';
    collapseBtn.style.display = 'block';
    collapseBtn.style.marginTop = '4px';
    collapseBtn.onclick = function() { toggleThresholdCollapse(this); };
    fullBlock.appendChild(collapseBtn);
  }
}

function toggleThresholdCollapse(btn) {
  const wrapper = btn.closest('.threshold-wrapper');
  const shortThreshold = wrapper.querySelector('.threshold');
  const expandBtn = wrapper.querySelector('.leaf-condition .threshold-toggle');
  const fullBlock = wrapper.querySelector('.threshold-full-block');
  shortThreshold.style.display = '';
  expandBtn.style.display = '';
  fullBlock.style.display = 'none';
}
"""
