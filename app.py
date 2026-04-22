"""
Log Scanner Supreme - A web-based log file analyzer
"""

import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv, set_key, dotenv_values
from log_analyzer import LogAnalyzer

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, '.env')
SETTINGS_FILE = os.path.join(BASE_DIR, 'copilot-api', 'settings.json')

# Load environment variables
load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'log', 'txt', 'json', 'xml', 'csv', 'out', 'err'}
MODELS_FILE = os.path.join(BASE_DIR, 'copilot-api', 'available_models.json')
PROMPTS_FILE = os.path.join(BASE_DIR, 'copilot-api', 'prompts.json')
LOG_TYPES_FILE = os.path.join(BASE_DIR, 'processes', 'log_types.md')

# Fallback model list used when available_models.json hasn't been generated yet
FALLBACK_MODELS = [
    {'id': 'gpt-4o', 'name': 'GPT-4o (OpenAI)'},
    {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini (OpenAI, Fast)'},
    {'id': 'claude-sonnet-4', 'name': 'Claude Sonnet 4 (Anthropic, Versatile)'},
    {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo (OpenAI, Budget)'},
]


def load_available_models():
    """Load models from the cached JSON file, falling back to defaults."""
    if os.path.exists(MODELS_FILE):
        try:
            with open(MODELS_FILE, 'r') as f:
                data = json.load(f)
            models = data.get('models', [])
            if models:
                return [
                    {
                        'id': m['id'],
                        'name': m.get('display_name', m.get('name', m['id'])),
                        'max_context_tokens': m.get('max_context_window_tokens'),
                        'max_output_tokens': m.get('max_output_tokens'),
                    }
                    for m in models
                ]
        except (json.JSONDecodeError, KeyError):
            pass
    return FALLBACK_MODELS


AVAILABLE_MODELS = load_available_models()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def ensure_settings_file():
    """Ensure settings.json file exists."""
    settings_dir = os.path.dirname(SETTINGS_FILE)
    os.makedirs(settings_dir, exist_ok=True)
    
    if not os.path.exists(SETTINGS_FILE):
        default_settings = {
            'github_pat': '',
            'model': 'gpt-4o-mini',
            'fast_model': 'gpt-4o-mini',
            'chunk_size': 3000
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=4)


def get_settings():
    """Get current settings from settings.json file."""
    ensure_settings_file()
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        settings = {}
    
    api_key = settings.get('github_pat', '')
    return {
        'api_key': api_key,
        'model': settings.get('model', 'gpt-4o-mini'),
        'fast_model': settings.get('fast_model', settings.get('model', 'gpt-4o-mini')),
        'chunk_size': int(settings.get('chunk_size', 3000)),
        'api_key_configured': bool(api_key.strip() and 
                                   api_key not in ['your-openai-api-key-here', 'your-github-pat-here'])
    }


def save_settings(api_key=None, model=None, fast_model=None, chunk_size=None):
    """Save settings to settings.json file."""
    ensure_settings_file()
    
    # Load existing settings
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        settings = {}
    
    # Update settings
    if api_key is not None:
        settings['github_pat'] = api_key
    
    if model is not None:
        settings['model'] = model
    
    if fast_model is not None:
        settings['fast_model'] = fast_model
    
    if chunk_size is not None:
        settings['chunk_size'] = chunk_size
    
    # Save settings
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/settings', methods=['GET'])
def get_settings_api():
    """Get current settings (API key is masked)."""
    settings = get_settings()
    # Mask the API key for security
    if settings['api_key']:
        masked = settings['api_key'][:8] + '...' + settings['api_key'][-4:] if len(settings['api_key']) > 12 else '****'
    else:
        masked = ''
    
    return jsonify({
        'api_key_masked': masked,
        'api_key_configured': settings['api_key_configured'],
        'model': settings['model'],
        'fast_model': settings['fast_model'],
        'chunk_size': settings['chunk_size'],
        'available_models': AVAILABLE_MODELS
    })


def load_prompts():
    """Load prompts from prompts.json file."""
    try:
        with open(PROMPTS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_log_type_prompt(log_type: str) -> str:
    """Extract the analysis prompt for a specific log type from log_types.md.
    
    Parses the markdown looking for a ## heading that matches the detected log type,
    then extracts the content from the ### Analysis prompt code block.
    """
    if not log_type:
        return ''
    
    try:
        with open(LOG_TYPES_FILE, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return ''
    
    # Normalize the log type for matching
    log_type_lower = log_type.lower().strip()
    
    # Split into sections by ## headings
    import re
    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    
    for section in sections:
        if not section.strip():
            continue
        # Get the heading (first line)
        heading = section.split('\n')[0].strip()
        heading_lower = heading.lower()
        
        # Match if the detected log type contains the heading or vice versa
        if (heading_lower in log_type_lower or 
            log_type_lower in heading_lower or
            # Also try matching key words
            all(word in log_type_lower for word in heading_lower.split() if len(word) > 3)):
            
            # Look for ### Analysis prompt section with a code block
            prompt_match = re.search(
                r'###\s*Analysis\s*prompt\s*\n+```[^\n]*\n(.*?)```',
                section, 
                re.DOTALL | re.IGNORECASE
            )
            if prompt_match:
                return prompt_match.group(1).strip()
    
    return ''


def save_prompts(prompts):
    """Save prompts to prompts.json file."""
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts, f, indent=4)


@app.route('/api/prompts/<prompt_type>', methods=['GET'])
def get_prompts_api(prompt_type):
    """Get prompts for a specific analysis type."""
    prompts = load_prompts()
    if prompt_type not in prompts:
        return jsonify({'error': f'Unknown prompt type: {prompt_type}'}), 404
    return jsonify(prompts[prompt_type])


@app.route('/api/prompts/<prompt_type>', methods=['POST'])
def save_prompts_api(prompt_type):
    """Save prompts for a specific analysis type."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    prompts = load_prompts()
    prompts[prompt_type] = data
    save_prompts(prompts)
    return jsonify({'status': 'saved', 'prompt_type': prompt_type})


@app.route('/api/settings', methods=['POST'])
def update_settings_api():
    """Update settings."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update only provided fields
        if 'api_key' in data and data['api_key']:
            save_settings(api_key=data['api_key'].strip())
        
        if 'model' in data:
            save_settings(model=data['model'])
        
        if 'fast_model' in data:
            save_settings(fast_model=data['fast_model'])
        
        if 'chunk_size' in data:
            chunk_size = int(data['chunk_size'])
            if chunk_size < 500 or chunk_size > 100000:
                return jsonify({'error': 'Chunk size must be between 500 and 100,000'}), 400
            save_settings(chunk_size=chunk_size)
        
        # Return updated settings
        settings = get_settings()
        if settings['api_key']:
            masked = settings['api_key'][:8] + '...' + settings['api_key'][-4:] if len(settings['api_key']) > 12 else '****'
        else:
            masked = ''
        
        return jsonify({
            'success': True,
            'api_key_masked': masked,
            'api_key_configured': settings['api_key_configured'],
            'model': settings['model'],
            'fast_model': settings['fast_model'],
            'chunk_size': settings['chunk_size']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/test', methods=['POST'])
def test_api_key():
    """Test if the GitHub PAT is valid for Copilot API."""
    from copilot_client import test_api_key as copilot_test
    
    data = request.get_json()
    api_key = data.get('api_key') if data else None
    
    # Use provided key or current saved key
    if not api_key:
        settings = get_settings()
        api_key = settings['api_key']
    
    if not api_key:
        return jsonify({'valid': False, 'error': 'No GitHub PAT provided'})
    
    result = copilot_test(api_key)
    return jsonify(result)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        # Read and count lines
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
            line_count = content.count('\n') + 1
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': unique_filename,
            'size': file_size,
            'lines': line_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/detect-log-type', methods=['POST'])
def detect_log_type():
    """Detect the type of log file from its content."""
    data = request.get_json()

    if not data or 'filepath' not in data:
        return jsonify({'error': 'No file path provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        settings = get_settings()
        api_key = settings['api_key']
        model = settings['fast_model']

        if not api_key or not settings['api_key_configured']:
            return jsonify({'error': 'GitHub PAT not configured. Please add your token in Settings.'}), 400

        analyzer = LogAnalyzer(api_key=api_key, model=model)

        with open(filepath, 'r', errors='replace') as f:
            content = f.read()

        result = analyzer.detect_log_type(content)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fast-summary', methods=['POST'])
def fast_summary():
    """Generate a fast AI summary of the uploaded log file."""
    data = request.get_json()

    if not data or 'filepath' not in data:
        return jsonify({'error': 'No file path provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        settings = get_settings()
        api_key = settings['api_key']
        model = settings['fast_model']
        chunk_size = settings['chunk_size']

        if not api_key or not settings['api_key_configured']:
            return jsonify({'error': 'GitHub PAT not configured. Please add your token in Settings.'}), 400

        analyzer = LogAnalyzer(api_key=api_key, model=model, chunk_size=chunk_size)

        with open(filepath, 'r', errors='replace') as f:
            content = f.read()

        issue_description = data.get('issue_description', '')
        log_type = data.get('log_type', '')
        log_type_prompt = get_log_type_prompt(log_type)
        prompts = load_prompts()
        fast_prompts = prompts.get('fast_summary', {})
        results = analyzer.fast_summary(content, issue_description=issue_description, prompt_overrides=fast_prompts, log_type=log_type, log_type_prompt=log_type_prompt)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_file():
    """Analyze the uploaded log file."""
    data = request.get_json()
    
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No file path provided'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Initialize analyzer with Copilot API
        settings = get_settings()
        api_key = settings['api_key']
        model = settings['model']
        chunk_size = settings['chunk_size']
        
        if not api_key or not settings['api_key_configured']:
            return jsonify({
                'error': 'GitHub PAT not configured. Please add your token in Settings.'
            }), 400
        
        analyzer = LogAnalyzer(api_key=api_key, model=model, chunk_size=chunk_size)
        
        # Read file content
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        
        # Analyze the log file
        results = analyzer.analyze(content)
        
        # Clean up the uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview-chunks', methods=['POST'])
def preview_chunks():
    """Preview chunks and preprocessing results without running AI analysis."""
    data = request.get_json()
    
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No file path provided'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        settings = get_settings()
        chunk_size = settings['chunk_size']
        
        analyzer = LogAnalyzer(api_key='preview', model='preview', chunk_size=chunk_size)
        
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        
        # Pre-process
        preprocessing = analyzer._preprocess_log(content)
        
        # Chunk the content
        chunks = analyzer._chunk_log(content)
        
        chunks_info = []
        for i, c in enumerate(chunks):
            chunks_info.append({
                'num': i + 1,
                'start_line': c['start_line'],
                'end_line': c['end_line'],
                'lines': f"{c['start_line']}-{c['end_line']}",
                'tokens': c['tokens'],
                'preview': c['content'][:200] + ('...' if len(c['content']) > 200 else '')
            })
        
        return jsonify({
            'preprocessing': {
                'error_count': len(preprocessing['errors']),
                'warning_count': len(preprocessing['warnings']),
                'sample_errors': preprocessing['errors'][:10],
                'sample_warnings': preprocessing['warnings'][:10]
            },
            'total_chunks': len(chunks),
            'chunks_info': chunks_info
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze-chunk', methods=['POST'])
def analyze_single_chunk():
    """Analyze a single chunk by number."""
    data = request.get_json()
    
    if not data or 'filepath' not in data or 'chunk_num' not in data:
        return jsonify({'error': 'filepath and chunk_num required'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        settings = get_settings()
        api_key = settings['api_key']
        model = settings['model']
        chunk_size = settings['chunk_size']
        
        if not api_key or not settings['api_key_configured']:
            return jsonify({'error': 'GitHub PAT not configured'}), 400
        
        analyzer = LogAnalyzer(api_key=api_key, model=model, chunk_size=chunk_size)
        
        # Set issue description if provided
        analyzer.issue_description = data.get('issue_description', '')
        
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        
        chunks = analyzer._chunk_log(content)
        chunk_num = int(data['chunk_num'])
        
        if chunk_num < 1 or chunk_num > len(chunks):
            return jsonify({'error': f'Invalid chunk number. Must be 1-{len(chunks)}'}), 400
        
        chunk = chunks[chunk_num - 1]
        
        # Get running context from previously analyzed chunks if provided
        running_summary = data.get('running_summary', '')
        previous_issues = data.get('previous_issues', [])
        
        result = analyzer._analyze_chunk(
            chunk, chunk_num, len(chunks),
            running_summary, previous_issues
        )
        
        # Add raw excerpt for chat context
        result['raw_excerpt'] = analyzer._extract_raw_excerpt(chunk['content'])
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze-stream', methods=['POST'])
def analyze_file_stream():
    """Analyze the uploaded log file with streaming updates."""
    from flask import Response, stream_with_context
    
    data = request.get_json()
    
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No file path provided'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filepath'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    def generate():
        try:
            # Initialize analyzer with Copilot API
            settings = get_settings()
            api_key = settings['api_key']
            model = settings['model']
            chunk_size = settings['chunk_size']
            
            if not api_key or not settings['api_key_configured']:
                yield f"data: {json.dumps({'error': 'GitHub PAT not configured'})}\n\n"
                return
            
            analyzer = LogAnalyzer(api_key=api_key, model=model, chunk_size=chunk_size)
            
            # Get issue description if provided
            issue_description = data.get('issue_description', '')
            
            # Get selected chunks if provided (1-indexed list)
            selected_chunks = data.get('selected_chunks', None)
            
            # Read file content
            with open(filepath, 'r', errors='replace') as f:
                content = f.read()
            
            # Stream analysis results
            for update in analyzer.analyze_streaming(content, issue_description=issue_description, selected_chunks=selected_chunks):
                yield f"data: {json.dumps(update)}\n\n"
            
            # Clean up
            try:
                os.remove(filepath)
            except:
                pass
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat queries about the log analysis with automatic log retrieval."""
    data = request.json
    user_query = data.get('query', '')
    chunk_context = data.get('chunk_context', '')
    full_context = data.get('full_context', '')
    shadow_context = data.get('shadow_context', '')
    filepath_key = data.get('filepath', '')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    settings = get_settings()
    api_key = settings['api_key']
    model = settings['model']
    
    if not api_key or not settings['api_key_configured']:
        return jsonify({'error': 'GitHub PAT not configured'}), 400
    
    # Load the log file if filepath provided (for dynamic retrieval)
    log_lines = None
    if filepath_key:
        log_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filepath_key)
        if os.path.exists(log_filepath):
            with open(log_filepath, 'r', errors='replace') as f:
                log_lines = f.readlines()
    
    try:
        from copilot_client import CopilotClient
        client = CopilotClient(api_key=api_key)
        
        system_prompt = """You are a helpful log analysis assistant. You have access to context from a log file analysis AND the ability to fetch specific lines or search the actual log file.

When answering questions:
1. First check the "Raw Log Content" and "Analysis Context" sections for relevant information
2. If you find what the user is asking for, answer directly with specific line references
3. If you need to see specific log lines that aren't in the current context, use these commands:

**To fetch specific line ranges:**
[FETCH_LINES:100-200]
This retrieves lines 100 through 200 from the log file.

**To search for a pattern in the log:**
[SEARCH_LOG:error pattern here]
This searches the entire log file for lines matching the pattern (case-insensitive) and returns matching lines with surrounding context.

You can use multiple fetch/search commands in one response. The system will automatically retrieve the requested content and re-ask your question with the additional context.

RULES:
- Use FETCH_LINES when you know approximately which lines to look at (from line numbers mentioned in the analysis)
- Use SEARCH_LOG when you need to find specific text, URLs, error messages, or patterns
- Keep line ranges reasonable (max 200 lines per fetch) to avoid overwhelming context
- When you have enough information to answer, provide a thorough answer WITHOUT any fetch/search commands
- Always cite specific line numbers when quoting log content
- Use code blocks when showing log lines

When analyzing timing or delays:
- Look for timestamps and calculate time differences
- Identify the longest gaps between consecutive entries

IMPORTANT: At the end of EVERY final answer (one without FETCH/SEARCH commands), include a section starting with exactly "---SUGGESTIONS---" followed by 2-4 brief suggested follow-up questions, one per line. No bullets or numbering."""

        # Build context message
        context_message = ""
        if chunk_context:
            context_message += f"## Current Chunk Context (Summary)\n{chunk_context}\n\n"
        if shadow_context:
            context_message += f"## Raw Log Content\n{shadow_context}\n\n"
        if full_context:
            context_message += f"## Full Analysis Context\n{full_context}\n\n"
        
        has_log_file = log_lines is not None
        if has_log_file:
            context_message += f"\n(Log file is available with {len(log_lines)} total lines. Use [FETCH_LINES:start-end] or [SEARCH_LOG:pattern] to retrieve specific content.)\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if context_message:
            messages.append({"role": "user", "content": f"Here is the context from the log analysis:\n\n{context_message}"})
            messages.append({"role": "assistant", "content": "I've reviewed the log analysis context. I'm ready to answer questions about the log file. I can fetch specific line ranges or search for patterns in the log when needed."})
        
        messages.append({"role": "user", "content": user_query})
        
        # Retrieval loop — up to 3 rounds of fetching
        import re
        max_retrieval_rounds = 3
        retrieval_log = []  # Track what was fetched for the frontend
        
        for round_num in range(max_retrieval_rounds + 1):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=3000
            )
            
            assistant_response = response.choices[0].message.content
            
            # Check for FETCH_LINES commands
            fetch_matches = re.findall(r'\[FETCH_LINES:(\d+)-(\d+)\]', assistant_response)
            # Check for SEARCH_LOG commands
            search_matches = re.findall(r'\[SEARCH_LOG:([^\]]+)\]', assistant_response)
            
            if not fetch_matches and not search_matches:
                # No more retrieval needed — this is the final answer
                break
            
            if round_num >= max_retrieval_rounds:
                # Max rounds reached, strip commands and return what we have
                assistant_response = re.sub(r'\[FETCH_LINES:\d+-\d+\]\s*', '', assistant_response)
                assistant_response = re.sub(r'\[SEARCH_LOG:[^\]]+\]\s*', '', assistant_response)
                break
            
            if not has_log_file:
                # No file available, strip commands and return
                assistant_response = re.sub(r'\[FETCH_LINES:\d+-\d+\]\s*', '', assistant_response)
                assistant_response = re.sub(r'\[SEARCH_LOG:[^\]]+\]\s*', '', assistant_response)
                break
            
            # Execute retrievals
            retrieved_content = []
            
            for start_str, end_str in fetch_matches:
                start = max(1, int(start_str))
                end = min(len(log_lines), int(end_str))
                # Cap at 200 lines per fetch
                if end - start > 200:
                    end = start + 200
                fetched = []
                for i in range(start - 1, end):
                    fetched.append(f"L{i+1}: {log_lines[i].rstrip()}")
                retrieved_content.append(f"### Lines {start}-{end}:\n```\n" + '\n'.join(fetched) + "\n```")
                retrieval_log.append(f"Fetched lines {start}-{end}")
            
            for pattern in search_matches:
                # Search the log file for the pattern
                try:
                    search_re = re.compile(re.escape(pattern), re.IGNORECASE)
                except re.error:
                    search_re = re.compile(re.escape(pattern), re.IGNORECASE)
                
                matches_found = []
                for i, line in enumerate(log_lines):
                    if search_re.search(line):
                        # Include ±3 lines of context
                        ctx_start = max(0, i - 3)
                        ctx_end = min(len(log_lines), i + 4)
                        block = []
                        for j in range(ctx_start, ctx_end):
                            marker = " >> " if j == i else "    "
                            block.append(f"{marker}L{j+1}: {log_lines[j].rstrip()}")
                        matches_found.append('\n'.join(block))
                        
                        if len(matches_found) >= 15:  # Cap at 15 matches
                            break
                
                if matches_found:
                    retrieved_content.append(
                        f"### Search results for \"{pattern}\" ({len(matches_found)} matches):\n```\n" + 
                        '\n---\n'.join(matches_found) + "\n```"
                    )
                else:
                    retrieved_content.append(f"### Search for \"{pattern}\": No matches found in the log file.")
                retrieval_log.append(f"Searched for \"{pattern}\"")
            
            # Add retrieved content to messages and loop
            retrieval_text = "\n\n".join(retrieved_content)
            
            # Add the assistant's request and the retrieved data to the conversation
            messages.append({"role": "assistant", "content": assistant_response})
            messages.append({"role": "user", "content": f"Here is the log content you requested:\n\n{retrieval_text}\n\nNow please answer the original question using this additional context. If you need more data, you can request it. Otherwise, provide your complete answer."})
        
        # Extract suggested follow-up questions
        suggestions = []
        clean_response = assistant_response
        if '---SUGGESTIONS---' in assistant_response:
            parts = assistant_response.split('---SUGGESTIONS---', 1)
            clean_response = parts[0].strip()
            suggestion_lines = parts[1].strip().split('\n')
            suggestions = [s.strip().strip('-').strip('•').strip('"').strip() for s in suggestion_lines if s.strip()]
            suggestions = suggestions[:4]
        
        # Clean any remaining fetch/search commands from the response
        clean_response = re.sub(r'\[FETCH_LINES:\d+-\d+\]\s*', '', clean_response)
        clean_response = re.sub(r'\[SEARCH_LOG:[^\]]+\]\s*', '', clean_response)
        
        return jsonify({
            'response': clean_response,
            'suggestions': suggestions,
            'retrieval_steps': retrieval_log
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Log Scanner Supreme')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on (default: 5000)')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  Log Scanner Supreme")
    print("  Powered by GitHub Copilot API")
    print("="*60)
    print(f"\n  Starting server at: http://localhost:{args.port}")
    print("\n  Configure your GitHub PAT in Settings (click ⚙️)")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=args.port)
