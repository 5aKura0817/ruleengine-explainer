from datetime import datetime
from typing import Dict, Any, List, Optional

class StrategyParser:
    """Parse nested strategy tree and convert to readable conditions.

    Node types:
      nodeType=1  : AND node — children all required (且)
      nodeType=2  : OR node  — any child sufficient (或)
      nodeType=-1 : Leaf node — actual condition data

    Rendered as an ASCII tree using ├─ / └─ / │ characters.
    Every compound node (AND or OR) is labelled [且] or [或] regardless of depth.
    """

    NODE_AND = 1
    NODE_OR = 2
    NODE_LEAF = -1

    @staticmethod
    def parse_strategy(strategy_list: List[Dict[str, Any]]) -> str:
        """Parse a strategy list (base or additional) into an ASCII tree string."""
        if not strategy_list:
            return ""
        base = "  "
        lines = []
        for i, node in enumerate(strategy_list):
            is_last = (i == len(strategy_list) - 1)
            conn = "└─" if is_last else "├─"
            cont = "   " if is_last else "│  "
            lines.extend(StrategyParser._render_child(node, base + conn, base + cont))
        return "\n".join(lines)

    @staticmethod
    def parse_base_conditions(base_strategies: List[Dict[str, Any]]) -> str:
        return StrategyParser.parse_strategy(base_strategies)

    @staticmethod
    def parse_additional_conditions(additional_strategies: List[Dict[str, Any]]) -> str:
        return StrategyParser.parse_strategy(additional_strategies)

    @staticmethod
    def _render_child(node: Dict[str, Any], prefix: str, continuation: str) -> List[str]:
        """Recursively render one node.

        prefix      — characters to prepend to this node's own line (ends with ├─ or └─)
        continuation — characters to prepend to lines produced by this node's children
        """
        node_type = node.get('nodeType', StrategyParser.NODE_LEAF)
        children = node.get('children') or []

        # Leaf node
        if node_type == StrategyParser.NODE_LEAF or not children:
            data = node.get('data') or {}
            if data.get('fieldName'):
                return [prefix + " " + StrategyParser._format_condition(data)]
            return []

        # Compound node (AND or OR)
        label = "[且]" if node_type == StrategyParser.NODE_AND else "[或]"
        lines = [prefix + label]
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            child_conn = continuation + ("└─" if is_last else "├─")
            child_cont = continuation + ("   " if is_last else "│  ")
            lines.extend(StrategyParser._render_child(child, child_conn, child_cont))
        return lines

    @staticmethod
    def _format_condition(data: Dict[str, Any]) -> str:
        """Format a single condition as readable text"""
        field_name = data.get('fieldName', 'Unknown Field')
        field_code = data.get('fieldCode', '')
        operator_name = data.get('operatorName', '')
        threshold = data.get('threshold')

        condition = f"{field_name}({field_code})      {operator_name}"

        if threshold is not None:
            threshold_str = str(threshold)
            # Translate boolean values to Chinese
            if threshold_str.lower() == 'true':
                threshold_str = '是'
            elif threshold_str.lower() == 'false':
                threshold_str = '否'
            # Truncate long thresholds for readability
            max_length = 60
            if len(threshold_str) > max_length:
                threshold_str = threshold_str[:max_length] + "..."
            condition += f"      {threshold_str}"

        return condition


class RuleTranslator:
    """Translate rule API response to readable rule configuration format"""
    
    @staticmethod
    def translate(rule_data: Dict[str, Any]) -> str:
        """
        Translate rule data from API into human-readable format
        
        Args:
            rule_data: The 'data' field from rule detail API response
        
        Returns:
            Formatted rule configuration text
        """
        output = []
        
        # Rule Name
        rule_name = rule_data.get('ruleName', '')
        output.append(f"规则名称    {rule_name}")
        
        # Rule ID
        rule_id = rule_data.get('id', '')
        output.append(f"规则ID      {rule_id}")
        
        # Source Name
        source_name = rule_data.get('sourceName', '')
        output.append(f"数据源      {source_name}")
        
        output.append("")  # Empty line
        
        # Base Conditions
        strategies = rule_data.get('strategies', {})
        base_strategies = strategies.get('base', [])
        
        if base_strategies:
            output.append("基础条件①")
            output.append(StrategyParser.parse_base_conditions(base_strategies))
            output.append("")  # Empty line

        # Additional Conditions
        additional_strategies = strategies.get('additional', [])
        if additional_strategies:
            output.append("附加条件②")
            output.append(StrategyParser.parse_additional_conditions(additional_strategies))
            output.append("")  # Empty line
        
        # Effective Time
        start_time = rule_data.get('startTime', 0)
        end_time = rule_data.get('endTime', 86399)
        start_time_str = RuleTranslator._format_seconds_to_time(start_time)
        end_time_str = RuleTranslator._format_seconds_to_time(end_time)
        
        output.append("生效时间③")
        output.append(f"  {start_time_str} - {end_time_str}")
        output.append("")  # Empty line
        
        # Rule Description
        comment = rule_data.get('comment', '')
        output.append("规则说明")
        output.append(f"  {comment}")
        output.append("")  # Empty line
        
        # Metadata
        create_by = rule_data.get('createBy', {})
        creator_fullname = create_by.get('fullname', 'Unknown')
        creator_username = create_by.get('username', '')
        
        output.append(f"创建人    {creator_fullname}({creator_username})")
        
        create_time = rule_data.get('createTime', 0)
        create_time_str = RuleTranslator._format_timestamp(create_time)
        output.append(f"创建时间   {create_time_str}")
        
        update_time = rule_data.get('updateTime', 0)
        update_time_str = RuleTranslator._format_timestamp(update_time)
        output.append(f"最后更新   {update_time_str}")
        
        return "\n".join(output)
    
    @staticmethod
    def _format_timestamp(timestamp_ms: int) -> str:
        """Convert millisecond timestamp to formatted date-time string"""
        if timestamp_ms == 0:
            return ""
        try:
            dt = datetime.fromtimestamp(timestamp_ms / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, OSError):
            return ""
    
    @staticmethod
    def _format_seconds_to_time(seconds: int) -> str:
        """Convert seconds from midnight to HH:MM:SS format"""
        try:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        except:
            return "00:00:00"
