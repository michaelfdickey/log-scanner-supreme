# Agentic Loop Process

## Overview
An AI-driven iterative log exploration system where the model actively investigates the log file using tools (search, read, grep) rather than passively receiving pre-selected content. The AI decides what to look at, follows threads, and builds understanding incrementally — similar to how a human engineer would debug a log file.

## Why This Is Better Than Fast Summary / Thorough Analysis

| Aspect | Fast Summary | Thorough Analysis | Agentic Loop |
|--------|-------------|-------------------|--------------|
| What AI sees | Regex-filtered extract | Everything (chunked) | Whatever it asks for |
| API calls | 1 | N+1 (N = chunks) | Variable (typically 5-15) |
| Can follow threads | No | Partially (running context) | Yes |
| Finds unexpected issues | Only if regex catches them | Yes, but drowns in noise | Yes, focused investigation |
| Cost efficiency | Low cost | High cost | Medium cost |
| Speed | Fast | Slow | Medium |

## Architecture

### Core Concept: Tool-Augmented Conversation Loop

The AI model is given a set of **tools** that operate on the uploaded log file server-side. The system runs a loop:

```
1. AI receives: file metadata + preprocessing summary + tool definitions
2. AI decides what to do → calls a tool (e.g., grep for "ERROR")
3. System executes the tool → returns results to AI
4. AI analyzes results → decides next action (another tool call, or final answer)
5. Repeat until AI declares analysis complete
```

### Tools to Provide to the AI

These are Python functions executed server-side. The AI never runs arbitrary code — it calls named tools with parameters.

#### 1. `search_log(pattern, case_sensitive=False, max_results=100)`
- Runs a regex search across the entire log file
- Returns matching lines with line numbers
- Equivalent to `grep -n -i <pattern> logfile`
- Used for: finding error patterns, searching for specific strings, counting occurrences

#### 2. `read_lines(start_line, end_line)`
- Reads a specific range of lines from the log file
- Max range: 500 lines per call
- Used for: reading context around errors, examining specific sections

#### 3. `get_line_count()`
- Returns total number of lines in the file
- Used for: understanding file size, planning reads

#### 4. `get_timestamp_range()`
- Extracts first and last timestamps found in the log
- Returns the time span covered
- Used for: understanding the log's time window

#### 5. `count_pattern(pattern, case_sensitive=False)`
- Counts occurrences of a pattern without returning all matches
- Used for: quick frequency analysis ("how many 404s?", "how many timeout errors?")

#### 6. `get_unique_values(pattern, group=0, max_results=50)`
- Extracts unique matching values from the log
- Used for: finding unique error codes, IP addresses, user IDs, component names

#### 7. `get_surrounding_context(line_number, context_lines=10)`
- Returns lines around a specific line number
- Used for: examining what happened before/after a specific event

### API Integration Strategy

#### Option A: Manual Tool Loop (Recommended for Copilot API)

The GitHub Copilot `/chat/completions` endpoint supports `tool_calls` for many models. The flow:

```python
# Pseudocode for the agentic loop

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_log",
            "description": "Search the log file using a regex pattern. Returns matching lines with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "case_sensitive": {"type": "boolean", "default": False},
                    "max_results": {"type": "integer", "default": 100}
                },
                "required": ["pattern"]
            }
        }
    },
    # ... other tools ...
]

messages = [
    {"role": "system", "content": AGENTIC_SYSTEM_PROMPT},
    {"role": "user", "content": f"Analyze this log file: {file_metadata}"}
]

MAX_ITERATIONS = 20

for iteration in range(MAX_ITERATIONS):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    choice = response.choices[0]

    # If the model wants to call tools
    if choice.finish_reason == "tool_calls":
        # Append the assistant message (with tool_calls)
        messages.append(choice.message)

        # Execute each tool call
        for tool_call in choice.message.tool_calls:
            result = execute_tool(tool_call.function.name, tool_call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        # Stream progress update to frontend
        yield {"type": "tool_call", "data": {"tool": tool_call.function.name, "iteration": iteration}}

    # If the model is done (no more tool calls)
    elif choice.finish_reason == "stop":
        final_analysis = choice.message.content
        break
```

#### Option B: Simulated Tool Use (Fallback)

If the model doesn't support `tool_calls`, simulate it:

1. Include tool descriptions in the system prompt
2. Instruct the AI to output structured JSON: `{"action": "search_log", "params": {"pattern": "ERROR"}}`
3. Parse the AI's response, execute the action, feed results back
4. Repeat until AI outputs `{"action": "complete", "analysis": {...}}`

This is less reliable but works with any chat model.

### System Prompt for Agentic Analysis

```
You are an expert log analyst with access to tools for investigating a log file. 
Your goal is to find the most critical issues, understand their root causes, and 
provide actionable recommendations.

APPROACH:
1. Start by understanding the file: check line count, read the first 50 lines to 
   understand the log format
2. Search for critical patterns: errors, exceptions, failures, crashes
3. For each significant finding, read the surrounding context to understand what 
   led to it
4. Look for patterns: repeated errors, escalating issues, correlated events
5. Search for specific indicators based on what you've found
6. Synthesize your findings into a comprehensive report

IMPORTANT GUIDELINES:
- Be methodical but efficient. Don't read the entire file line by line.
- Use search_log to find patterns, then read_lines for context.
- Use count_pattern to understand frequency before diving deep.
- Focus on the most impactful issues first.
- Look for root causes, not just symptoms.
- If the user provided an issue description, prioritize investigating that.
- When done, provide your final analysis as a structured report.

You have a maximum of 20 tool calls. Use them wisely.
```

### Server-Side Tool Execution

Each tool is a Python method on the `LogAnalyzer` class that operates on the file stored in `uploads/`:

```python
class AgenticLogAnalyzer:
    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'r', errors='replace') as f:
            self.lines = f.readlines()
        self.total_lines = len(self.lines)

    def search_log(self, pattern: str, case_sensitive: bool = False, max_results: int = 100) -> dict:
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = []
        for i, line in enumerate(self.lines, 1):
            if re.search(pattern, line, flags):
                matches.append({"line": i, "content": line.rstrip()[:500]})
                if len(matches) >= max_results:
                    break
        return {"matches": matches, "total_found": len(matches), "truncated": len(matches) >= max_results}

    def read_lines(self, start_line: int, end_line: int) -> dict:
        start = max(1, start_line) - 1
        end = min(self.total_lines, end_line)
        if end - start > 500:
            end = start + 500
        content = []
        for i in range(start, end):
            content.append({"line": i + 1, "content": self.lines[i].rstrip()[:500]})
        return {"lines": content, "requested_range": [start_line, end_line]}

    def count_pattern(self, pattern: str, case_sensitive: bool = False) -> dict:
        flags = 0 if case_sensitive else re.IGNORECASE
        count = sum(1 for line in self.lines if re.search(pattern, line, flags))
        return {"pattern": pattern, "count": count, "total_lines": self.total_lines}

    # ... other tools follow same pattern ...
```

### Frontend Integration

#### Streaming Updates

The agentic loop should stream updates to the frontend via SSE (Server-Sent Events), same pattern as thorough analysis:

```
Event stream:
  {"type": "status", "message": "Starting agentic analysis..."}
  {"type": "tool_call", "data": {"tool": "get_line_count", "iteration": 1}}
  {"type": "tool_result", "data": {"tool": "get_line_count", "summary": "File has 15,234 lines"}}
  {"type": "tool_call", "data": {"tool": "search_log", "iteration": 2, "params": {"pattern": "ERROR|FATAL"}}}
  {"type": "tool_result", "data": {"tool": "search_log", "summary": "Found 47 matches"}}
  {"type": "thinking", "data": {"message": "Found 47 errors. Investigating the most frequent types..."}}
  ... more tool calls ...
  {"type": "final_summary", "data": { ... structured analysis JSON ... }}
  {"type": "complete", "data": {"iterations": 12, "tools_used": 12}}
```

#### UI Display

Show a real-time investigation log:
- Each tool call displayed as a step: "🔍 Searching for ERROR|FATAL... → 47 matches found"
- AI's reasoning shown between steps (if the model provides it)
- Final report rendered same as fast summary / thorough analysis output
- Chat section opens for follow-up questions with full investigation context

### Endpoint Design

```
POST /api/agentic-analyze
Content-Type: application/json
Response: text/event-stream (SSE)

Request body:
{
    "filepath": "uuid_filename.txt",
    "issue_description": "optional user-provided focus area",
    "max_iterations": 20
}
```

### Key Implementation Decisions

1. **Max iterations**: Default 20, configurable. Prevents runaway loops and cost explosion.
2. **Token budget tracking**: Track cumulative tokens used across all iterations. Warn/stop if exceeding a threshold.
3. **Tool result truncation**: If a `search_log` returns 100+ matches, summarize rather than sending all lines back to the model. This prevents context window overflow.
4. **File lifecycle**: The uploaded file must NOT be deleted until the agentic loop completes (unlike current behavior where `analyze-stream` deletes the file after processing).
5. **Model selection**: Not all models support `tool_calls`. Check the `supports_tool_calls` field from `available_models.json` and only enable the agentic button for compatible models. Fall back to Option B (simulated) for others.
6. **Concurrent safety**: The `AgenticLogAnalyzer` reads the file into memory once. All tool calls operate on the in-memory copy. No file locking needed.

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `agentic_analyzer.py` | Create | `AgenticLogAnalyzer` class with tool methods + loop orchestration |
| `app.py` | Modify | Add `/api/agentic-analyze` SSE endpoint |
| `static/app.js` | Modify | Add `runAgenticAnalysis()` method, wire up button, render investigation steps |
| `templates/index.html` | Modify | Add investigation log UI section |
| `static/style.css` | Modify | Styles for investigation step display |

### Error Handling

- If a tool call fails (bad regex, etc.), return the error to the model as a tool result so it can adapt
- If the model enters a loop (calling the same tool with same params), detect and break after 3 repetitions
- If the model stops responding or returns malformed tool calls, generate a partial report from findings so far
- Network/API timeouts: retry once, then fail gracefully with partial results

### Security Considerations

- Tool parameters must be validated server-side (max line ranges, regex complexity limits)
- The AI must not be able to access files outside the uploads directory
- Regex patterns should have a timeout to prevent ReDoS attacks
- File content returned to the AI is truncated per-line (500 chars) to prevent context overflow
