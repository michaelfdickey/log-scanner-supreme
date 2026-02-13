"""
Log Analyzer Module - Core logic for analyzing log files

This module handles:
- Breaking log files into manageable chunks
- Detecting errors, warnings, and issues
- Maintaining context across chunks
- Generating summaries and recommendations
"""

import re
import json
from typing import Generator
from copilot_client import CopilotClient
import tiktoken


def extract_json(text: str) -> dict:
    """
    Extract JSON from text that might contain markdown code fences or other wrapping.
    """
    if not text or not text.strip():
        raise ValueError("Empty response received")
    
    text = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code fence
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                   # Raw JSON object
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                json_str = match.group(1) if match.lastindex else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue
    
    # Last resort: find first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract JSON from response: {text[:200]}...")


class LogAnalyzer:
    """Analyzes log files by chunking and processing with AI."""
    
    # Common log patterns for pre-filtering
    ERROR_PATTERNS = [
        r'\b(error|err|exception|fail|failed|failure|fatal|critical|crash|crashed)\b',
        r'\b(timeout|timed out|connection refused|connection reset)\b',
        r'\b(denied|unauthorized|forbidden|permission)\b',
        r'\b(null|undefined|NaN|nil)\s*(pointer|reference|exception)?\b',
        r'\b(stack\s*trace|traceback|segfault|segmentation fault)\b',
        r'\b(oom|out of memory|memory leak|heap|overflow)\b',
        r'\b(deadlock|race condition|thread)\b',
        r'\[(ERROR|ERR|FATAL|CRITICAL|SEVERE)\]',
        r'HTTP[/ ](4\d\d|5\d\d)',
        r'exit\s*(code|status)?\s*[1-9]\d*',
    ]
    
    WARNING_PATTERNS = [
        r'\b(warn|warning|deprecated|caution)\b',
        r'\[(WARN|WARNING)\]',
        r'\b(retry|retrying|attempt)\b',
        r'\b(slow|latency|delay|lag)\b',
    ]
    
    INFO_PATTERNS = [
        r'\b(info|notice|debug)\b',
        r'\[(INFO|DEBUG|NOTICE)\]',
    ]
    
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini', chunk_size: int = 3000):
        """
        Initialize the LogAnalyzer.
        
        Args:
            api_key: GitHub Personal Access Token with Copilot access
            model: Model to use for analysis
            chunk_size: Target size of each chunk in tokens
        """
        self.client = CopilotClient(api_key=api_key)
        self.model = model
        self.chunk_size = chunk_size
        # Use cl100k_base encoding which is compatible with GPT-4 and newer models
        self.encoding = tiktoken.get_encoding('cl100k_base')
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self.encoding.encode(text))
    
    def _preprocess_log(self, content: str) -> dict:
        """
        Pre-process log to identify potential issues before AI analysis.
        
        Returns a dict with categorized line numbers and patterns found.
        """
        lines = content.split('\n')
        findings = {
            'errors': [],
            'warnings': [],
            'info': [],
            'patterns_found': set()
        }
        
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            for pattern in self.ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings['errors'].append({'line': i, 'content': line[:200]})
                    findings['patterns_found'].add('errors')
                    break
            else:
                for pattern in self.WARNING_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings['warnings'].append({'line': i, 'content': line[:200]})
                        findings['patterns_found'].add('warnings')
                        break
        
        findings['patterns_found'] = list(findings['patterns_found'])
        return findings
    
    def _chunk_log(self, content: str) -> list:
        """
        Split log content into chunks that fit within the context window.
        
        Attempts to split at natural boundaries (blank lines, timestamps).
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_start_line = 1
        
        # Reserve tokens for system prompt and response
        max_chunk_tokens = self.chunk_size
        
        for i, line in enumerate(lines):
            line_tokens = self.count_tokens(line + '\n')
            
            if current_tokens + line_tokens > max_chunk_tokens and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'start_line': chunk_start_line,
                    'end_line': chunk_start_line + len(current_chunk) - 1,
                    'tokens': current_tokens
                })
                current_chunk = []
                current_tokens = 0
                chunk_start_line = i + 1
            
            current_chunk.append(line)
            current_tokens += line_tokens
        
        # Add remaining content
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'start_line': chunk_start_line,
                'end_line': chunk_start_line + len(current_chunk) - 1,
                'tokens': current_tokens
            })
        
        return chunks
    
    def _extract_raw_excerpt(self, chunk_content: str, max_lines: int = 50) -> str:
        """
        Extract key lines from a chunk for raw context.
        Prioritizes error/warning lines and their surrounding context.
        """
        lines = chunk_content.split('\n')
        
        # Find lines containing errors/warnings
        important_line_indices = set()
        for i, line in enumerate(lines):
            for pattern in self.ERROR_PATTERNS + self.WARNING_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Add this line and 2 lines of context before/after
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        important_line_indices.add(j)
                    break
        
        if important_line_indices:
            # Sort and get the important lines with their line numbers
            sorted_indices = sorted(important_line_indices)
            excerpt_lines = []
            prev_idx = -2
            for idx in sorted_indices:
                if idx > prev_idx + 1:
                    excerpt_lines.append('...')  # Gap marker
                excerpt_lines.append(f"L{idx + 1}: {lines[idx][:300]}")
                prev_idx = idx
            return '\n'.join(excerpt_lines[:max_lines])
        else:
            # No errors found, return first and last portions
            excerpt = []
            if len(lines) <= max_lines:
                for i, line in enumerate(lines):
                    excerpt.append(f"L{i+1}: {line[:300]}")
            else:
                # First 20 lines
                for i in range(min(20, len(lines))):
                    excerpt.append(f"L{i+1}: {lines[i][:300]}")
                excerpt.append(f'... ({len(lines) - 40} lines omitted) ...')
                # Last 20 lines
                for i in range(max(20, len(lines)-20), len(lines)):
                    excerpt.append(f"L{i+1}: {lines[i][:300]}")
            return '\n'.join(excerpt)
    
    def _analyze_chunk(self, chunk: dict, chunk_num: int, total_chunks: int, 
                       running_summary: str, previous_issues: list) -> dict:
        """
        Analyze a single chunk of log content.
        
        Args:
            chunk: The chunk data including content and line numbers
            chunk_num: Current chunk number (1-indexed)
            total_chunks: Total number of chunks
            running_summary: Summary of all previous chunks
            previous_issues: List of issues found in previous chunks
        """
        
        context_prompt = ""
        if running_summary:
            context_prompt = f"""
## Context from Previous Chunks (1-{chunk_num - 1}):

### Running Summary:
{running_summary}

### Previously Identified Issues:
{json.dumps(previous_issues, indent=2) if previous_issues else 'None yet'}

---
"""
        
        # Build focus area instruction if issue description is provided
        focus_instruction = ""
        if hasattr(self, 'issue_description') and self.issue_description:
            focus_instruction = f"""

## PRIMARY FOCUS
The user is specifically investigating: "{self.issue_description}"
Pay special attention to anything related to this issue.

HOWEVER, you must ALSO identify and report any other serious errors, critical failures, security issues, or significant warnings you find, even if unrelated to the primary focus. Do not ignore important problems just because they don't match the user's description."""
        
        system_prompt = f"""You are an expert log analyzer. Your task is to analyze log file chunks and identify issues, errors, warnings, and anomalies.{focus_instruction}

IMPORTANT: Return ONLY a valid JSON object, no markdown code fences or extra text.

Return a JSON object with this structure:
{{
    "chunk_summary": "Brief summary of what's happening in this chunk",
    "issues": [
        {{
            "severity": "error|warning|info",
            "type": "The type of issue",
            "description": "Detailed description of the issue",
            "line_numbers": [],
            "possible_causes": [],
            "context": ""
        }}
    ],
    "patterns_detected": [],
    "notable_events": [],
    "running_issues_update": ""
}}

Be thorough but concise. Focus on actionable insights."""

        user_prompt = f"""{context_prompt}
## Current Chunk Analysis Request

**Chunk {chunk_num} of {total_chunks}** (Lines {chunk['start_line']} - {chunk['end_line']})

Please analyze the following log content:

```
{chunk['content']}
```

Analyze this chunk and return your findings as JSON. Consider how any issues might relate to previously identified problems. Look for:
1. Explicit errors and exceptions
2. Warnings and deprecation notices
3. Performance issues (timeouts, slow operations)
4. Security concerns (authentication failures, permission issues)
5. Resource problems (memory, disk, connections)
6. Any patterns that might indicate systemic issues

Return ONLY the JSON object, no markdown code fences."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result = extract_json(response.choices[0].message.content)
            result['chunk_num'] = chunk_num
            result['lines'] = f"{chunk['start_line']}-{chunk['end_line']}"
            return result
            
        except Exception as e:
            return {
                'chunk_num': chunk_num,
                'lines': f"{chunk['start_line']}-{chunk['end_line']}",
                'error': str(e),
                'chunk_summary': 'Analysis failed for this chunk',
                'issues': [],
                'patterns_detected': [],
                'notable_events': []
            }
    
    def _generate_final_summary(self, chunk_results: list, all_issues: list) -> dict:
        """Generate a comprehensive final summary and recommendations."""
        
        # Compile all chunk summaries
        chunk_summaries = "\n".join([
            f"**Chunk {r['chunk_num']} (Lines {r['lines']}):** {r.get('chunk_summary', 'No summary')}"
            for r in chunk_results
        ])
        
        # Compile all patterns
        all_patterns = []
        for r in chunk_results:
            all_patterns.extend(r.get('patterns_detected', []))
        
        # Truncate issues list if too long to prevent token overflow
        # Prioritize errors over warnings over info
        truncated_issues = all_issues
        if len(all_issues) > 50:
            errors = [i for i in all_issues if i.get('severity') == 'error']
            warnings = [i for i in all_issues if i.get('severity') == 'warning']
            infos = [i for i in all_issues if i.get('severity') == 'info']
            
            # Keep up to 30 errors, 15 warnings, 5 info
            truncated_issues = errors[:30] + warnings[:15] + infos[:5]
            truncated_note = f"\n\n(Note: Showing {len(truncated_issues)} of {len(all_issues)} total issues. Prioritized by severity.)"
        else:
            truncated_note = ""
        
        system_prompt = """You are an expert log analyst providing a final comprehensive report.

Return a JSON object with this structure:
{
    "executive_summary": "A brief 2-3 sentence overview of the log file's health",
    "overall_health": "healthy|degraded|critical",
    "key_findings": [
        {
            "title": "Finding title",
            "severity": "critical|high|medium|low",
            "description": "Detailed description",
            "affected_components": ["List of affected systems/components"],
            "evidence": "Summary of evidence from the logs"
        }
    ],
    "issue_timeline": "Description of how issues progressed through the log",
    "root_cause_analysis": [
        {
            "issue": "The issue",
            "likely_root_cause": "Most probable root cause",
            "confidence": "high|medium|low",
            "reasoning": "Why this is likely the cause"
        }
    ],
    "recommendations": [
        {
            "priority": "immediate|short-term|long-term",
            "action": "Specific recommended action",
            "rationale": "Why this action is recommended"
        }
    ],
    "statistics": {
        "total_errors": 0,
        "total_warnings": 0,
        "most_frequent_issue": "Description of most common issue"
    }
}

Return ONLY the JSON object, no markdown code fences."""

        user_prompt = f"""Based on the complete analysis of this log file, provide a comprehensive final report.

## Chunk-by-Chunk Summaries:
{chunk_summaries}

## All Identified Issues ({len(all_issues)} total):{truncated_note}
{json.dumps(truncated_issues, indent=2)}

## Detected Patterns Across All Chunks:
{json.dumps(list(set(all_patterns))[:20], indent=2)}

Please synthesize all this information into a final comprehensive report with actionable recommendations. Return ONLY the JSON object."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            return extract_json(response.choices[0].message.content)
            
        except Exception as e:
            # Generate a basic fallback summary from collected data
            error_count = len([i for i in all_issues if i.get('severity') == 'error'])
            warning_count = len([i for i in all_issues if i.get('severity') == 'warning'])
            
            # Determine health based on counts
            if error_count > 10:
                health = 'critical'
            elif error_count > 0:
                health = 'degraded'
            else:
                health = 'healthy' if warning_count < 5 else 'degraded'
            
            return {
                'executive_summary': f'Analysis complete. Found {error_count} errors and {warning_count} warnings across {len(chunk_results)} chunks. (Detailed summary generation failed: {str(e)[:100]})',
                'overall_health': health,
                'key_findings': [
                    {
                        'title': issue.get('type', 'Issue'),
                        'severity': 'high' if issue.get('severity') == 'error' else 'medium',
                        'description': issue.get('description', 'No description'),
                        'affected_components': [],
                        'evidence': f"Found in chunk analysis"
                    }
                    for issue in all_issues[:5] if issue.get('severity') == 'error'
                ],
                'recommendations': [
                    {
                        'priority': 'immediate',
                        'action': 'Review the error details in the chunk analysis above',
                        'rationale': 'Manual review recommended as automated summary generation encountered an issue'
                    }
                ],
                'statistics': {
                    'total_errors': error_count,
                    'total_warnings': warning_count,
                    'most_frequent_issue': 'See chunk analysis for details'
                }
            }
    
    def analyze(self, content: str) -> dict:
        """
        Perform complete analysis of a log file.
        
        Args:
            content: The full log file content
            
        Returns:
            Complete analysis results including all chunk analyses and final summary
        """
        # Pre-process to get quick stats
        preprocessing = self._preprocess_log(content)
        
        # Split into chunks
        chunks = self._chunk_log(content)
        
        # Analyze each chunk
        chunk_results = []
        all_issues = []
        running_summary = ""
        
        for i, chunk in enumerate(chunks, 1):
            result = self._analyze_chunk(
                chunk, i, len(chunks), 
                running_summary, all_issues
            )
            chunk_results.append(result)
            
            # Update running context
            if result.get('issues'):
                all_issues.extend(result['issues'])
            
            # Build running summary
            running_summary += f"\nChunk {i}: {result.get('chunk_summary', 'No summary')}"
            if result.get('running_issues_update'):
                running_summary += f" | Issues: {result['running_issues_update']}"
        
        # Generate final summary
        final_summary = self._generate_final_summary(chunk_results, all_issues)
        
        return {
            'preprocessing': {
                'error_count': len(preprocessing['errors']),
                'warning_count': len(preprocessing['warnings']),
                'sample_errors': preprocessing['errors'][:10],
                'sample_warnings': preprocessing['warnings'][:10]
            },
            'chunks_analyzed': len(chunks),
            'chunk_results': chunk_results,
            'all_issues': all_issues,
            'final_summary': final_summary
        }
    
    def analyze_streaming(self, content: str, issue_description: str = '', selected_chunks: list = None) -> Generator[dict, None, None]:
        """
        Perform analysis with streaming updates.
        
        Args:
            content: The log file content to analyze
            issue_description: Optional description of the issue to focus on
            selected_chunks: Optional list of 1-indexed chunk numbers to analyze.
                           If None, all chunks are analyzed.
        
        Yields updates as each chunk is processed.
        """
        self.issue_description = issue_description
        # Pre-process
        yield {'type': 'status', 'message': 'Pre-processing log file...'}
        preprocessing = self._preprocess_log(content)
        
        yield {
            'type': 'preprocessing',
            'data': {
                'error_count': len(preprocessing['errors']),
                'warning_count': len(preprocessing['warnings']),
                'sample_errors': preprocessing['errors'][:10],
                'sample_warnings': preprocessing['warnings'][:10]
            }
        }
        
        # Chunk the content
        yield {'type': 'status', 'message': 'Splitting log into analyzable chunks...'}
        chunks = self._chunk_log(content)
        
        # Determine which chunks to analyze
        if selected_chunks:
            # Filter to only selected chunk indices (1-indexed)
            selected_set = set(selected_chunks)
            chunks_to_analyze = [(i+1, chunk) for i, chunk in enumerate(chunks) if (i+1) in selected_set]
        else:
            chunks_to_analyze = [(i+1, chunk) for i, chunk in enumerate(chunks)]
        
        total_to_analyze = len(chunks_to_analyze)
        
        yield {
            'type': 'chunking',
            'data': {
                'total_chunks': len(chunks),
                'analyzed_chunks': total_to_analyze,
                'selected_chunks': selected_chunks,
                'chunks_info': [
                    {'num': chunk_num, 'lines': f"{c['start_line']}-{c['end_line']}", 'tokens': c['tokens']}
                    for chunk_num, c in chunks_to_analyze
                ]
            }
        }
        
        # Analyze selected chunks
        chunk_results = []
        all_issues = []
        running_summary = ""
        
        for idx, (chunk_num, chunk) in enumerate(chunks_to_analyze, 1):
            yield {
                'type': 'status',
                'message': f'Analyzing chunk {chunk_num} ({idx} of {total_to_analyze}) (lines {chunk["start_line"]}-{chunk["end_line"]})...'
            }
            
            result = self._analyze_chunk(
                chunk, chunk_num, len(chunks),
                running_summary, all_issues
            )
            
            # Add raw excerpt for chat context
            result['raw_excerpt'] = self._extract_raw_excerpt(chunk['content'])
            
            chunk_results.append(result)
            
            # Update context
            if result.get('issues'):
                all_issues.extend(result['issues'])
            
            running_summary += f"\nChunk {chunk_num}: {result.get('chunk_summary', 'No summary')}"
            if result.get('running_issues_update'):
                running_summary += f" | Issues: {result['running_issues_update']}"
            
            yield {
                'type': 'chunk_result',
                'data': result
            }
        
        # Generate final summary with error handling
        yield {'type': 'status', 'message': 'Generating final summary and recommendations...'}
        
        try:
            final_summary = self._generate_final_summary(chunk_results, all_issues)
        except Exception as e:
            final_summary = {
                'executive_summary': f'Final summary generation failed: {str(e)}',
                'overall_health': 'unknown',
                'key_findings': [],
                'recommendations': [],
                'error': str(e)
            }
        
        yield {
            'type': 'final_summary',
            'data': final_summary
        }
        
        # Complete
        yield {
            'type': 'complete',
            'data': {
                'chunks_analyzed': total_to_analyze,
                'total_issues': len(all_issues)
            }
        }
