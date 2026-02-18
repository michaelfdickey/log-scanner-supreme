# Thorough Analysis Process

## Overview
Multi-pass chunk-by-chunk AI analysis that processes the entire log file sequentially, maintaining running context across chunks.

How Claude Opus 4.6 in the VS Code chat is different
When you paste a log file into Copilot chat, models like Opus 4.6 have tool use — they can run terminal commands (grep, sed, awk) against the actual file on your machine. So the workflow is:

AI reads a sample of the file to understand the format
AI writes grep/sed commands to search for specific patterns
AI reads the command output (focused, relevant lines)
AI iterates — maybe running more targeted searches based on what it found
AI synthesizes findings
This is fundamentally more powerful because the model is actively exploring the file rather than passively receiving pre-selected content. It can follow threads, correlate timestamps, search for specific error codes, etc.

The ideal approach would be an agentic loop where the AI gets tools to query the log:

A search_log(pattern) tool that runs grep on the server-side file
A read_lines(start, end) tool that reads specific line ranges
The AI starts with file stats + the preprocessing summary, then iteratively investigates


## Current Implementation

### Flow
1. User uploads log file → saved to `uploads/` on server
2. User clicks **🔬 Thorough Analysis**
3. Backend previews chunks (split by token count, default 3k tokens each)
4. Chunk grid UI displayed — user can analyze individual chunks or all at once
5. For each chunk:
   - Chunk content + running summary of previous chunks + previously found issues sent to AI
   - AI returns: chunk_summary, issues[], patterns_detected[], notable_events[]
   - Running context updated with new findings
6. After all chunks processed, a final synthesis call generates:
   - Executive summary, overall health rating
   - Key findings with severity
   - Root cause analysis with confidence levels
   - Prioritized recommendations
   - Statistics
7. Chat section opens with full analysis context available

### Strengths
- AI sees every line of the log file
- Cross-chunk context maintained (later chunks informed by earlier findings)
- Users can selectively analyze specific chunks
- Comprehensive findings

### Weaknesses
- Slow for large files (N chunks = N+1 API calls)
- Expensive in token usage
- Running summary grows and may hit context limits on very large files
- AI passively receives content — cannot follow investigative threads
- Chunk boundaries may split related log entries

### Key Files
- `log_analyzer.py` → `LogAnalyzer.analyze_streaming()`, `_analyze_chunk()`, `_generate_final_summary()`
- `app.py` → `/analyze-stream` endpoint (SSE streaming), `/api/preview-chunks`, `/api/analyze-chunk`
- `static/app.js` → `previewChunks()`, `startAnalysisAll()`, `analyzeSingleChunk()`, `handleStreamUpdate()`
