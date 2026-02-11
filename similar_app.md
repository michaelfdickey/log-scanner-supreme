# Log Scanner App Template

This document describes the architecture and implementation of a web-based log file analyzer powered by the GitHub Copilot API. Use this as a guide to build similar applications.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Core Components](#core-components)
5. [GitHub Copilot API Integration](#github-copilot-api-integration)
6. [Log Analysis Engine](#log-analysis-engine)
7. [Interactive Chat with Shadow Context](#interactive-chat-with-shadow-context)
8. [Frontend Implementation](#frontend-implementation)
9. [Settings Management](#settings-management)
10. [Key Prompts and Patterns](#key-prompts-and-patterns)
11. [Building a New App](#building-a-new-app)

---

## Overview

This application is a **web-based log file analyzer** that:

- Accepts log file uploads via drag-and-drop or file picker
- Breaks large logs into manageable chunks for analysis
- Uses AI (GitHub Copilot API) to identify errors, warnings, patterns, and issues
- Maintains context across chunks for progressive understanding
- Generates a final summary with recommendations
- Provides an interactive chat interface for follow-up questions
- Implements "shadow context" for automatic context expansion when needed

### Key Features

1. **Chunked Analysis**: Large files are split into token-limited chunks
2. **Streaming Updates**: Real-time progress updates during analysis
3. **Context Awareness**: Each chunk analysis considers previous findings
4. **Smart Chat**: Auto-fetches additional log content when AI needs it
5. **Issue Focus**: Optional issue description to guide analysis
6. **Dark Theme UI**: Modern, responsive web interface

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Upload UI  │  │  Results UI │  │   Chat Interface        │  │
│  │  (drag/drop)│  │  (chunks,   │  │   (query + contexts)    │  │
│  │             │  │   summary)  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Backend (app.py)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   /upload   │  │  /analyze-  │  │      /api/chat          │  │
│  │             │  │   stream    │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Log Analyzer (log_analyzer.py)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Preprocess  │  │   Chunk &   │  │   Generate Summary      │  │
│  │   (regex)   │  │   Analyze   │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Copilot Client (copilot_client.py)                │
│           GitHub Copilot API (api.githubcopilot.com)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
log-scanner-app/
├── app.py                  # Flask backend - routes and API endpoints
├── log_analyzer.py         # Core analysis logic - chunking, prompts, streaming
├── copilot_client.py       # GitHub Copilot API client wrapper
├── launcher.py             # Helper script to check deps and start app
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html          # Main HTML template (Jinja2)
│
├── static/
│   ├── app.js              # Frontend JavaScript (LogScanner class)
│   └── style.css           # CSS styling (dark theme)
│
├── copilot-api/
│   └── settings.json       # API key and settings (gitignored)
│
├── uploads/                # Temporary file storage (gitignored)
├── .env.example            # Example environment file
└── .gitignore              # Git ignore rules
```

---

## Core Components

### 1. Flask Backend (`app.py`)

**Purpose**: Handle HTTP requests, file uploads, streaming responses, and settings management.

**Key Routes**:

```python
@app.route('/')                          # Serve main page
@app.route('/upload', methods=['POST'])  # Handle file uploads
@app.route('/analyze-stream', methods=['POST'])  # Stream analysis results (SSE)
@app.route('/api/chat', methods=['POST'])        # Handle chat queries
@app.route('/api/settings', methods=['GET', 'POST'])  # Get/save settings
@app.route('/api/settings/test', methods=['POST'])    # Test API connection
```

**Streaming Pattern** (Server-Sent Events):

```python
@app.route('/analyze-stream', methods=['POST'])
def analyze_stream():
    def generate():
        analyzer = LogAnalyzer(api_key=api_key, model=model)
        for update in analyzer.analyze_streaming(content, issue_description):
            yield f"data: {json.dumps(update)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )
```

### 2. Log Analyzer (`log_analyzer.py`)

**Purpose**: Core analysis logic including preprocessing, chunking, AI analysis, and summary generation.

**Key Classes/Methods**:

```python
class LogAnalyzer:
    def __init__(self, api_key, model, chunk_size)
    def _preprocess_log(content) -> dict       # Regex-based error/warning detection
    def _chunk_log(content) -> list            # Split into token-limited chunks
    def _extract_raw_excerpt(chunk) -> str     # Extract key lines for chat context
    def _analyze_chunk(...) -> dict            # AI analysis of single chunk
    def _generate_final_summary(...) -> dict   # AI-generated final report
    def analyze_streaming(content, issue_description) -> Generator  # Main entry point
```

**Token Counting**:

```python
import tiktoken
self.encoding = tiktoken.get_encoding('cl100k_base')

def count_tokens(self, text: str) -> int:
    return len(self.encoding.encode(text))
```

### 3. Copilot Client (`copilot_client.py`)

**Purpose**: Wrapper for GitHub Copilot API that mimics OpenAI client interface.

**Key Features**:
- Drop-in replacement for OpenAI client usage
- Handles authentication with GitHub PAT
- Provides ChatCompletion-like response objects

---

## GitHub Copilot API Integration

### API Endpoint

```
https://api.githubcopilot.com/chat/completions
```

### Required Headers

```python
headers = {
    'Authorization': f'Bearer {github_pat}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Copilot-Integration-Id': 'copilot-chat'  # REQUIRED
}
```

### Request Format

```python
data = {
    'model': 'gpt-4o-mini',  # or gpt-4o, gpt-4, gpt-3.5-turbo
    'messages': [
        {"role": "system", "content": "System prompt here"},
        {"role": "user", "content": "User message here"}
    ],
    'temperature': 0.3,
    'max_tokens': 2000  # optional
}
```

### Response Parsing

```python
response = requests.post(API_ENDPOINT, headers=headers, json=data, timeout=120)
result = response.json()
content = result['choices'][0]['message']['content']
```

### Authentication

Uses GitHub Personal Access Token (PAT) with Copilot access:
- Token format: `ghp_*` or `github_pat_*`
- Store in `copilot-api/settings.json` (gitignored)

### Full Client Implementation

```python
class CopilotClient:
    API_ENDPOINT = "https://api.githubcopilot.com/chat/completions"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = self._ChatCompletions(self)
    
    class _ChatCompletions:
        def __init__(self, client):
            self.client = client
            self.completions = self
        
        def create(self, model, messages, temperature=0.7, max_tokens=None):
            headers = {
                'Authorization': f'Bearer {self.client.api_key}',
                'Content-Type': 'application/json',
                'Copilot-Integration-Id': 'copilot-chat'
            }
            
            data = {'model': model, 'messages': messages, 'temperature': temperature}
            if max_tokens:
                data['max_tokens'] = max_tokens
            
            response = requests.post(self.client.API_ENDPOINT, headers=headers, json=data, timeout=120)
            # Parse response into ChatCompletion object...
```

---

## Log Analysis Engine

### Preprocessing (Regex-based)

Quick scan to identify error/warning patterns before AI analysis:

```python
ERROR_PATTERNS = [
    r'\b(error|err|exception|fail|failed|failure|fatal|critical|crash)\b',
    r'\b(timeout|timed out|connection refused|connection reset)\b',
    r'\b(denied|unauthorized|forbidden|permission)\b',
    r'\[(ERROR|ERR|FATAL|CRITICAL|SEVERE)\]',
    r'HTTP[/ ](4\d\d|5\d\d)',
    r'exit\s*(code|status)?\s*[1-9]\d*',
]

WARNING_PATTERNS = [
    r'\b(warn|warning|deprecated|caution)\b',
    r'\[(WARN|WARNING)\]',
    r'\b(retry|retrying|attempt)\b',
]
```

### Chunking Strategy

Split log into token-limited chunks:

```python
def _chunk_log(self, content: str) -> list:
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_start_line = 1
    
    for i, line in enumerate(lines):
        line_tokens = self.count_tokens(line + '\n')
        
        if current_tokens + line_tokens > self.chunk_size and current_chunk:
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
    
    # Don't forget remaining content
    if current_chunk:
        chunks.append({...})
    
    return chunks
```

### Raw Excerpt Extraction

Extract key lines from chunks for chat context:

```python
def _extract_raw_excerpt(self, chunk_content: str, max_lines: int = 50) -> str:
    lines = chunk_content.split('\n')
    important_line_indices = set()
    
    # Find error/warning lines and add context (2 lines before/after)
    for i, line in enumerate(lines):
        for pattern in self.ERROR_PATTERNS + self.WARNING_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    important_line_indices.add(j)
                break
    
    # Format with line numbers
    excerpt_lines = []
    prev_idx = -2
    for idx in sorted(important_line_indices):
        if idx > prev_idx + 1:
            excerpt_lines.append('...')  # Gap marker
        excerpt_lines.append(f"L{idx + 1}: {lines[idx][:300]}")
        prev_idx = idx
    
    return '\n'.join(excerpt_lines[:max_lines])
```

### Context-Aware Analysis

Each chunk receives context from previous chunks:

```python
context_prompt = f"""
## Context from Previous Chunks (1-{chunk_num - 1}):

### Running Summary:
{running_summary}

### Previously Identified Issues:
{json.dumps(previous_issues, indent=2)}
---
"""
```

### Issue Description Focus

Optional user-provided focus for analysis:

```python
if self.issue_description:
    focus_instruction = f"""
## PRIMARY FOCUS
The user is specifically investigating: "{self.issue_description}"
Pay special attention to anything related to this issue.

HOWEVER, you must ALSO identify and report any other serious errors, 
critical failures, security issues, or significant warnings you find, 
even if unrelated to the primary focus.
"""
```

---

## Interactive Chat with Shadow Context

### The Problem

User asks: "Show me the actual error message"
AI only has summaries, not raw log lines.

### The Solution: Shadow Context

1. **Initial Context**: Chunk summaries + full analysis summary
2. **Shadow Context**: Hidden, expandable raw log content
3. **Auto-Expansion**: AI requests specific chunks when needed

### Implementation Flow

```
User asks question
       │
       ▼
┌─────────────────────────────────────┐
│ Send: query + chunk_context +       │
│       full_context + shadow_context │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ AI Response                         │
│ Contains [NEED_CHUNKS:2,3]?         │
└─────────────────────────────────────┘
       │
       ├── No ──► Show response to user
       │
       ▼ Yes
┌─────────────────────────────────────┐
│ Frontend parses chunk numbers       │
│ Adds raw excerpts to shadow_context │
│ Retries the query automatically     │
└─────────────────────────────────────┘
       │
       ▼
Show enhanced response to user
```

### AI Prompt for Context Expansion

```python
system_prompt = """You are a helpful log analysis assistant.

When the user asks for examples of errors, specific log entries, or actual error messages:
1. First look in the "Raw Log Content" section if available
2. If you find what they're asking for, quote the relevant lines directly
3. If you cannot find the specific information, respond with EXACTLY this format:
   [NEED_CHUNKS:1,2,3] I need to see the raw log content from chunk(s) X to answer this.
   
   Replace the numbers with the actual chunk numbers you need.
   Look at the "Chunk-by-Chunk Summary" to determine which chunks likely contain the information.
   
The system will automatically fetch the raw log content and retry your query.
"""
```

### Frontend Implementation

```javascript
async sendChatMessage(retryWithRawContent = false, chunksToFetch = null) {
    // If retrying, add requested chunks to shadow context
    if (retryWithRawContent && chunksToFetch) {
        chunksToFetch.forEach(chunkNum => {
            const rawExcerpt = this.getRawExcerptForChunk(chunkNum);
            if (rawExcerpt && !this.shadowContext.includes(rawExcerpt)) {
                this.shadowContext += '\n\n' + rawExcerpt;
            }
        });
    }
    
    const response = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
            query: query,
            chunk_context: this.chunkContextArea.value,
            full_context: this.fullContextArea.value,
            shadow_context: this.shadowContext
        })
    });
    
    const data = await response.json();
    
    // Auto-retry if chunks needed
    if (data.needs_raw_content && !retryWithRawContent) {
        await this.sendChatMessage(true, data.chunks_requested);
        return;
    }
    
    this.addChatMessage(data.response, 'assistant');
}
```

### Backend Parsing

```python
# Parse [NEED_CHUNKS:1,2,3] format
chunks_match = re.search(r'\[NEED_CHUNKS?:([0-9,\s]+)\]', assistant_response)
needs_raw_content = chunks_match is not None
chunks_requested = []

if chunks_match:
    chunk_str = chunks_match.group(1)
    chunks_requested = [int(c.strip()) for c in chunk_str.split(',') if c.strip().isdigit()]
    clean_response = re.sub(r'\[NEED_CHUNKS?:[0-9,\s]+\]\s*', '', assistant_response).strip()

return jsonify({
    'response': clean_response,
    'needs_raw_content': needs_raw_content,
    'chunks_requested': chunks_requested
})
```

---

## Frontend Implementation

### Main JavaScript Class

```javascript
class LogScanner {
    constructor() {
        this.uploadedFile = null;
        this.filePath = null;
        this.chunkResults = [];      // Store all chunk analysis results
        this.allIssues = [];         // Aggregate all issues
        this.currentChunk = 0;       // Currently viewed chunk
        this.finalSummary = null;    // Final summary data
        this.shadowContext = '';     // Accumulated raw log context for chat
        this.settings = {};
        
        this.init();
    }
    
    init() {
        // Get DOM elements
        // Setup event listeners
        // Initialize chat elements
        // Load settings
    }
}
```

### Streaming Event Handling

```javascript
async startAnalysis() {
    const response = await fetch('/analyze-stream', {
        method: 'POST',
        body: JSON.stringify({ 
            filepath: this.filePath,
            issue_description: this.issueDescription.value
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE events
        const lines = buffer.split('\n');
        buffer = lines.pop();  // Keep incomplete line
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                this.handleStreamUpdate(data);
            }
        }
    }
}

handleStreamUpdate(data) {
    switch (data.type) {
        case 'status':
            this.progressStatus.textContent = data.message;
            break;
        case 'preprocessing':
            this.showPreprocessing(data.data);
            break;
        case 'chunk_result':
            this.handleChunkResult(data.data);
            break;
        case 'final_summary':
            this.finalSummary = data.data;
            this.showFinalSummary(data.data);
            break;
        case 'complete':
            this.showChatSection();
            break;
    }
}
```

### Chat Context Generation

```javascript
generateChunkContext() {
    const currentResult = this.chunkResults[this.currentChunk];
    let context = `### Chunk ${currentResult.chunk_num} (Lines ${currentResult.lines})\n\n`;
    context += `**TL;DR:** ${currentResult.chunk_summary}\n\n`;
    
    if (currentResult.issues?.length > 0) {
        context += `**Issues Found (${currentResult.issues.length}):**\n`;
        currentResult.issues.forEach((issue, idx) => {
            context += `${idx + 1}. [${issue.severity.toUpperCase()}] ${issue.type}: ${issue.description}\n`;
        });
    }
    return context;
}

generateFullContext() {
    let context = `### Overall Analysis Summary\n\n`;
    context += `**Health Status:** ${this.finalSummary.overall_health}\n`;
    context += `**Executive Summary:** ${this.finalSummary.executive_summary}\n\n`;
    
    // Key findings, issue counts, chunk summaries...
    return context;
}
```

---

## Settings Management

### Storage Location

```
copilot-api/settings.json  (gitignored)
```

### Settings Structure

```json
{
    "api_key": "ghp_xxxxxxxxxxxx",
    "model": "gpt-4o-mini",
    "chunk_size": 3000
}
```

### API Key Masking

Never send full API key to frontend:

```python
def get_settings():
    settings = load_settings()
    api_key = settings.get('api_key', '')
    
    return {
        'api_key_configured': bool(api_key),
        'api_key_masked': f"ghp_...{api_key[-4:]}" if len(api_key) > 8 else '',
        'model': settings.get('model', 'gpt-4o-mini'),
        'chunk_size': settings.get('chunk_size', 3000),
        'available_models': AVAILABLE_MODELS
    }
```

---

## Key Prompts and Patterns

### Chunk Analysis Prompt

```python
system_prompt = f"""You are an expert log analyzer. Your task is to analyze log file chunks 
and identify issues, errors, warnings, and anomalies.{focus_instruction}

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
"""
```

### Final Summary Prompt

```python
system_prompt = """You are an expert log analyst providing a final comprehensive report.

Return a JSON object with this structure:
{
    "executive_summary": "A brief 2-3 sentence overview",
    "overall_health": "healthy|degraded|critical",
    "key_findings": [...],
    "issue_timeline": "Description of how issues progressed",
    "root_cause_analysis": [...],
    "recommendations": [...],
    "statistics": {...}
}
"""
```

### JSON Extraction Helper

AI sometimes wraps JSON in markdown - extract it:

```python
def extract_json(text: str) -> dict:
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from markdown code fence
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                json_str = match.group(1) if match.lastindex else match.group(0)
                return json.loads(json_str)
            except:
                continue
    
    raise ValueError(f"Could not extract JSON from response")
```

---

## Building a New App

### Step 1: Copy Base Structure

```bash
mkdir my-new-analyzer
cp -r log-scanner-app/{app.py,copilot_client.py,launcher.py,requirements.txt} my-new-analyzer/
cp -r log-scanner-app/{templates,static,copilot-api} my-new-analyzer/
```

### Step 2: Customize the Analyzer

Create your domain-specific analyzer in `log_analyzer.py`:

1. **Update ERROR_PATTERNS and WARNING_PATTERNS** for your domain
2. **Modify the chunk analysis prompt** to focus on your use case
3. **Adjust the final summary prompt** for relevant recommendations
4. **Update preprocessing** if needed for specific log formats

### Step 3: Customize the Frontend

1. **Update HTML** - Change title, descriptions, file type hints
2. **Update CSS** - Adjust colors/branding if needed
3. **Update JS** - Modify display logic for your data structure

### Step 4: Add Domain-Specific Features

Examples:
- **Kubernetes logs**: Parse pod names, namespaces, container IDs
- **Database logs**: Track queries, connections, locks
- **Web server logs**: Parse HTTP status codes, response times, IPs
- **Application logs**: Track user sessions, transactions, performance metrics

### Step 5: Customize Chat Prompts

Update the chat system prompt to be domain-aware:

```python
system_prompt = """You are a [DOMAIN] log analysis assistant.
You understand [SPECIFIC TECHNOLOGIES] and can help troubleshoot 
[COMMON ISSUES IN THIS DOMAIN].
...
"""
```

### Essential Dependencies

```
flask>=3.0.0
requests>=2.31.0
tiktoken>=0.5.0
python-dotenv>=1.0.0
werkzeug>=3.0.0
```

### Gitignore Essentials

```
# Settings with API key
copilot-api/settings.json
.env

# Uploads
uploads/

# Python
__pycache__/
venv/
*.pyc
```

---

## Summary

This app provides a complete template for building AI-powered log analysis tools:

1. **Copilot API Integration**: Drop-in client for GitHub Copilot
2. **Chunked Analysis**: Handle large files by splitting into manageable pieces
3. **Context Continuity**: Maintain awareness across chunks
4. **Streaming UI**: Real-time progress updates
5. **Interactive Chat**: Follow-up questions with auto-context expansion
6. **Shadow Context**: Automatically fetch more data when AI needs it

To build a new specialized analyzer:
1. Clone the structure
2. Customize patterns and prompts for your domain
3. Adjust the UI to show relevant information
4. Add domain-specific parsing if needed

The core architecture (chunking, streaming, chat with shadow context) can remain largely unchanged while the prompts and patterns are customized for each use case.
