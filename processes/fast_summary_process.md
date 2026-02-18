# Fast Summary Process

## Overview
Single-pass AI analysis that sends a condensed extract of the log file in one API call.

## Current Implementation

### Flow
1. User uploads log file → saved to `uploads/` on server
2. User clicks **⚡ Fast Summary**
3. Backend reads the file and runs local regex preprocessing (`_preprocess_log`)
4. Python extracts a condensed view:
   - All lines matching ERROR_PATTERNS / WARNING_PATTERNS with ±2 lines of context
   - First 30 lines and last 30 lines of the file
   - Deduplicates overlapping ranges
5. Condensed text is truncated to ~12k tokens if needed
6. Single API call to `/chat/completions` with system prompt requesting JSON output
7. Response parsed → executive summary, key findings, recommendations displayed
8. Chat section opens for follow-up questions

### Strengths
- Fast (one API call, typically 5-15 seconds)
- Cheap (minimal token usage)
- Good for quick triage

### Weaknesses
- AI only sees what the regex pre-filter selects
- May miss issues that don't match hardcoded patterns
- No ability for AI to "follow up" on something interesting
- Context truncation may drop important details in very large files

### Key Files
- `log_analyzer.py` → `LogAnalyzer.fast_summary()`
- `app.py` → `/api/fast-summary` endpoint
- `static/app.js` → `runFastSummary()` method
