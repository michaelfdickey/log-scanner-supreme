#!/usr/bin/env python3
"""Test script for debugging the log analyzer"""

from log_analyzer import LogAnalyzer
import json

# Load settings
with open('copilot-api/settings.json') as f:
    settings = json.load(f)

test_log = '''2024-01-15 08:00:01 INFO  Application starting up...
2024-01-15 08:00:02 ERROR Database connection timeout
2024-01-15 08:00:03 WARN  Retrying connection'''

analyzer = LogAnalyzer(
    api_key=settings['github_pat'],
    model=settings['model'],
    chunk_size=settings['chunk_size']
)

print('Testing analysis...')
for update in analyzer.analyze_streaming(test_log):
    t = update.get('type')
    print(f'{t}: ', end='')
    if t == 'chunk_result':
        data = update.get('data', {})
        print(data.get('chunk_summary', 'no summary'))
    elif t == 'final_summary':
        data = update.get('data', {})
        print(data.get('executive_summary', 'no summary'))
    elif t == 'error':
        print(update)
    else:
        print(update.get('message', update.get('data', '')))

print('\nDone!')
