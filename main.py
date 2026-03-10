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


def export_rules(output_path: str = "./output/overview", limit: int = 0, export_type: str = "all") -> None:
    """Export enabled rules in one or more formats.
    
    Args:
        output_path: Output file path prefix (without extension, default: ./output/overview)
        limit: Maximum number of rules to export (0 = all)
        export_type: Export format - "all", "html", or "plaintext" (default: "all")
    """
    import os

    # Process output path
    if not os.path.sep in output_path and not output_path.startswith('.'):
        output_path = os.path.join("./output", output_path)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    client = APIClient()

    # Collect all enabled rules through pagination
    all_rule_summaries = []
    page_num = 1
    page_size = 100

    print("Fetching all enabled rules...")

    while True:
        response = client.get_rule_list(page_num, page_size, enabled_only=True)

        if response.get('code') != 0:
            print(f"Error: {response.get('message', 'Unknown error')}")
            sys.exit(1)

        results = response.get('data', {}).get('results', [])
        if not results:
            break

        all_rule_summaries.extend(results)
        print(f"  Fetched page {page_num}: {len(results)} enabled rules")

        page_param = response.get('data', {}).get('pageParam', {})
        total = page_param.get('totalCount', 0)
        if len(all_rule_summaries) >= total:
            break

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

    # Fetch detailed rule data
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

    if not rules_data:
        print("No rules fetched successfully")
        sys.exit(1)

    # Export based on type
    exported_files = []

    if export_type in ("all", "plaintext"):
        # Generate plaintext report
        txt_file = output_path + ".txt"
        print(f"Generating plaintext report...")

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(f"规则引擎数据转译 - 批量导出报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"规则总数: {len(rules_data)}\n")
            f.write("="*70 + "\n\n")

            for idx, rule_data in enumerate(rules_data, 1):
                translated = RuleTranslator.translate(rule_data)
                f.write(f"【第 {idx} 条规则】\n")
                f.write("-"*70 + "\n")
                f.write(translated)
                f.write("\n\n")

        exported_files.append(txt_file)
        print(f"  ✓ 纯文本导出完成: {txt_file}")

    if export_type in ("all", "html"):
        # Generate HTML report
        html_file = output_path + ".html"
        print(f"Generating HTML report...")

        html_content = HtmlExporter.generate(rules_data)

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        size_kb = len(html_content.encode("utf-8")) / 1024
        exported_files.append(html_file)
        print(f"  ✓ HTML 导出完成: {html_file} ({size_kb:.1f} KB)")

    print(f"\n✓ 导出完成！共 {len(rules_data)} 条规则")
    if len(exported_files) > 1:
        print(f"  已生成 {len(exported_files)} 个文件:")
        for f in exported_files:
            print(f"    - {f}")

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
    
    # Export command (replaces batch and html)
    export_parser = subparsers.add_parser('export', help='Export enabled rules to file(s)')
    export_parser.add_argument('-o', '--output', default='./output/overview',
                               help='Output file path prefix without extension (default: ./output/overview)')
    export_parser.add_argument('-n', '--number', type=int, default=0,
                               help='Max number of rules to export (default: 0 = all rules)')
    export_parser.add_argument('--type', choices=['all', 'html', 'plaintext'],
                               default='all', help='Export format: all (default), html, or plaintext')
    
    args = parser.parse_args()
    
    if args.command == 'translate':
        translate_rule(args.rule_id)
    elif args.command == 'list':
        list_rules(args.page, args.size)
    elif args.command == 'export':
        export_rules(args.output, args.number, args.type)
    else:
        parser.print_help()
