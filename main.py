#!/usr/bin/env python3
"""
Rule Engine Explainer - Main entry point
Translates rule engine API data into human-readable format
"""

import sys
from datetime import datetime

from ruleengine.api_client import APIClient
from ruleengine.html_exporter import HtmlExporter
from ruleengine.translator import RuleTranslator


def translate_rule(rule_id: int) -> None:
    """Fetch and translate a single rule"""
    client = APIClient()
    
    print(f"Fetching rule {rule_id}...")
    response = client.get_rule_detail(rule_id)
    
    if response.get('code') != 0:
        print(f"Error: {response.get('message', 'Unknown error')}")
        sys.exit(1)
    
    rule_data = response.get('data', {})
    translated = RuleTranslator.translate(rule_data)
    
    print("\n" + "="*60)
    print(translated)
    print("="*60)

def list_rules(page_num: int = 1, page_size: int = 20) -> None:
    """List enabled rules with pagination"""
    client = APIClient()
    
    print(f"Fetching rules (page {page_num}, size {page_size})...")
    response = client.get_rule_list(page_num, page_size, enabled_only=True)
    
    if response.get('code') != 0:
        print(f"Error: {response.get('message', 'Unknown error')}")
        sys.exit(1)
    
    data = response.get('data', {})
    page_param = data.get('pageParam', {})
    results = data.get('results', [])
    total = page_param.get('totalCount', 0)
    
    print(f"\nTotal enabled rules: {total}")
    print(f"Page {page_num} ({len(results)} rules shown):\n")
    
    for rule in results:
        rule_id = rule.get('id')
        rule_name = rule.get('ruleName', 'N/A')
        print(f"  ✓ [{rule_id}] {rule_name}")

def batch_translate(output_file: str = None, limit: int = 5, all_rules: bool = False) -> None:
    """Fetch and translate multiple rules, save to file
    
    Args:
        output_file: Output file path (optional, auto-generated if None)
        limit: Number of rules to translate (default: 5)
        all_rules: If True, translate all enabled rules (ignore limit)
    """
    client = APIClient()
    
    # Collect all enabled rules through pagination
    all_enabled_rules = []
    page_num = 1
    page_size = 100  # Fetch 100 at a time for efficiency
    
    print(f"Fetching all enabled rules...")
    
    while True:
        response = client.get_rule_list(page_num, page_size, enabled_only=True)
        
        if response.get('code') != 0:
            print(f"Error: {response.get('message', 'Unknown error')}")
            sys.exit(1)
        
        results = response.get('data', {}).get('results', [])
        
        if not results:
            break
        
        all_enabled_rules.extend(results)
        
        print(f"  Fetched page {page_num}: {len(results)} enabled rules")
        
        # Check if there are more pages
        page_param = response.get('data', {}).get('pageParam', {})
        total = page_param.get('totalCount', 0)
        if len(all_enabled_rules) >= total:
            break
        
        page_num += 1
    
    # Limit the number of rules if not fetching all
    if not all_rules and limit > 0:
        all_enabled_rules = all_enabled_rules[:limit]
    
    if not all_enabled_rules:
        print("No enabled rules found")
        sys.exit(1)
    
    print(f"Found {len(all_enabled_rules)} enabled rules to translate")
    
    # Prepare output file
    if output_file is None:
        if all_rules:
            output_file = f"all_rules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            output_file = f"rules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write(f"规则引擎数据转译 - 批量导出报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"规则总数: {len(all_enabled_rules)}\n")
        f.write("="*70 + "\n\n")
        
        for idx, rule_summary in enumerate(all_enabled_rules, 1):
            rule_id = rule_summary.get('id')
            rule_name = rule_summary.get('ruleName')
            
            if idx % 10 == 0:
                print(f"  [{idx}/{len(all_enabled_rules)}] Translating rule {rule_id}: {rule_name}...")
            
            # Fetch full rule detail
            detail_response = client.get_rule_detail(rule_id)
            
            if detail_response.get('code') != 0:
                print(f"    ✗ Error fetching rule {rule_id}")
                continue
            
            rule_data = detail_response.get('data', {})
            translated = RuleTranslator.translate(rule_data)
            
            # Write to file
            f.write(f"【第 {idx} 条规则】\n")
            f.write("-"*70 + "\n")
            f.write(translated)
            f.write("\n\n")
    
    print(f"\n✓ 转译完成！已导出到文件: {output_file}")
    print(f"  共转译 {len(all_enabled_rules)} 条规则")


def export_html(output_file: str = "rules_report.html", limit: int = 0) -> None:
    """Fetch enabled rules and export as a single self-contained HTML file.

    Args:
        output_file: Output HTML file path.
        limit: Maximum number of rules to include. 0 means all rules.
    """
    client = APIClient()

    # Collect enabled rule summaries through pagination
    all_rule_summaries = []
    page_num = 1
    page_size = 100

    print("Fetching all enabled rules...")

    while True:
        response = client.get_rule_list(page_num, page_size, enabled_only=True)

        if response.get("code") != 0:
            print(f"Error: {response.get('message', 'Unknown error')}")
            sys.exit(1)

        results = response.get("data", {}).get("results", [])
        if not results:
            break

        all_rule_summaries.extend(results)
        print(f"  Fetched page {page_num}: {len(results)} rules")

        page_param = response.get("data", {}).get("pageParam", {})
        total = page_param.get("totalCount", 0)
        if len(all_rule_summaries) >= total:
            break

        # Stop early if we already have enough for the limit
        if limit > 0 and len(all_rule_summaries) >= limit:
            break

        page_num += 1

    if not all_rule_summaries:
        print("No enabled rules found")
        sys.exit(1)

    # Apply limit
    if limit > 0:
        all_rule_summaries = all_rule_summaries[:limit]

    print(f"Found {len(all_rule_summaries)} enabled rules. Fetching details...")

    rules_data = []
    for idx, summary in enumerate(all_rule_summaries, 1):
        rule_id = summary.get("id")
        rule_name = summary.get("ruleName", "")

        if idx % 10 == 0:
            print(f"  [{idx}/{len(all_rule_summaries)}] Fetching rule {rule_id}: {rule_name}...")

        detail_response = client.get_rule_detail(rule_id)
        if detail_response.get("code") != 0:
            print(f"    ✗ Error fetching rule {rule_id}, skipping")
            continue

        rules_data.append(detail_response["data"])

    print(f"Generating HTML for {len(rules_data)} rules...")
    html_content = HtmlExporter.generate(rules_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = len(html_content.encode("utf-8")) / 1024
    print(f"\n✓ HTML 导出完成！已保存到: {output_file}")
    print(f"  共 {len(rules_data)} 条规则，文件大小: {size_kb:.1f} KB")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Rule Engine Explainer')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate a single rule')
    translate_parser.add_argument('rule_id', type=int, help='Rule ID to translate')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List enabled rules')
    list_parser.add_argument('-p', '--page', type=int, default=1, help='Page number (default: 1)')
    list_parser.add_argument('-s', '--size', type=int, default=20, help='Page size (default: 20)')
    
    # Batch translate command
    batch_parser = subparsers.add_parser('batch', help='Batch translate rules and export to file')
    batch_parser.add_argument('-n', '--number', type=int, default=5, help='Number of rules to translate (default: 5)')
    batch_parser.add_argument('-o', '--output', help='Output file path (optional, auto-generated if not specified)')
    batch_parser.add_argument('--all', action='store_true', help='Translate ALL enabled rules (ignore --number)')

    # HTML export command
    html_parser = subparsers.add_parser('html', help='Export enabled rules as a single HTML file')
    html_parser.add_argument('-o', '--output', default='rules_report.html', help='Output HTML file (default: rules_report.html)')
    html_parser.add_argument('-n', '--limit', type=int, default=0, help='Max number of rules to export (default: 0 = all rules)')
    
    args = parser.parse_args()
    
    if args.command == 'translate':
        translate_rule(args.rule_id)
    elif args.command == 'list':
        list_rules(args.page, args.size)
    elif args.command == 'batch':
        batch_translate(args.output, args.number, args.all)
    elif args.command == 'html':
        export_html(args.output, args.limit)
    else:
        parser.print_help()
