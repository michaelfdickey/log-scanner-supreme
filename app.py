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
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

# Available models for Copilot API (grouped by vendor)
# Only includes models that support /chat/completions endpoint
AVAILABLE_MODELS = [
    # --- OpenAI GPT-5.x ---
    {'id': 'gpt-5.2', 'name': 'GPT-5.2 (OpenAI, Versatile)'},
    {'id': 'gpt-5.1', 'name': 'GPT-5.1 (OpenAI, Versatile)'},
    {'id': 'gpt-5', 'name': 'GPT-5 (OpenAI, Versatile)'},
    {'id': 'gpt-5-mini', 'name': 'GPT-5 Mini (OpenAI, Lightweight)'},
    # --- OpenAI GPT-4.x ---
    {'id': 'gpt-4.1', 'name': 'GPT-4.1 (OpenAI, Versatile)'},
    {'id': 'gpt-4o', 'name': 'GPT-4o (OpenAI)'},
    {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini (OpenAI, Fast)'},
    {'id': 'gpt-4', 'name': 'GPT-4 (OpenAI, Legacy)'},
    {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo (OpenAI, Budget)'},
    # --- Anthropic Claude ---
    {'id': 'claude-opus-4.6', 'name': 'Claude Opus 4.6 (Anthropic, Powerful)'},
    {'id': 'claude-opus-4.5', 'name': 'Claude Opus 4.5 (Anthropic, Powerful)'},
    {'id': 'claude-opus-41', 'name': 'Claude Opus 4.1 (Anthropic, Powerful)'},
    {'id': 'claude-sonnet-4.5', 'name': 'Claude Sonnet 4.5 (Anthropic, Versatile)'},
    {'id': 'claude-sonnet-4', 'name': 'Claude Sonnet 4 (Anthropic, Versatile)'},
    {'id': 'claude-haiku-4.5', 'name': 'Claude Haiku 4.5 (Anthropic, Fast)'},
    # --- Google Gemini ---
    {'id': 'gemini-3-pro-preview', 'name': 'Gemini 3 Pro (Google, Preview)'},
    {'id': 'gemini-3-flash-preview', 'name': 'Gemini 3 Flash (Google, Preview)'},
    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro (Google, Powerful)'},
    # --- xAI Grok ---
    {'id': 'grok-code-fast-1', 'name': 'Grok Code Fast 1 (xAI, Lightweight)'},
]

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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
        'chunk_size': int(settings.get('chunk_size', 3000)),
        'api_key_configured': bool(api_key.strip() and 
                                   api_key not in ['your-openai-api-key-here', 'your-github-pat-here'])
    }


def save_settings(api_key=None, model=None, chunk_size=None):
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
        'chunk_size': settings['chunk_size'],
        'available_models': AVAILABLE_MODELS
    })


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
    """Handle chat queries about the log analysis"""
    data = request.json
    user_query = data.get('query', '')
    chunk_context = data.get('chunk_context', '')
    full_context = data.get('full_context', '')
    shadow_context = data.get('shadow_context', '')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    settings = get_settings()
    api_key = settings['api_key']
    model = settings['model']
    
    if not api_key or not settings['api_key_configured']:
        return jsonify({'error': 'GitHub PAT not configured'}), 400
    
    try:
        from copilot_client import CopilotClient
        client = CopilotClient(api_key=api_key)
        
        # Build the system prompt with context expansion instructions
        system_prompt = """You are a helpful log analysis assistant. You have access to context from a log file analysis.
Your job is to answer questions about the log file, help troubleshoot issues found, and provide insights.

When the user asks for examples of errors, specific log entries, actual error messages, or wants to trace something across chunks:
1. First look in the "Raw Log Content" section if available - this contains actual log lines
2. If you find what they're asking for, quote the relevant lines directly
3. If you cannot find the specific information in the provided context, respond with EXACTLY this format:
   [NEED_CHUNKS:1,2,3] I need to see the raw log content from chunk(s) X to answer this question.
   
   Replace the numbers with the actual chunk numbers you need. For example:
   - [NEED_CHUNKS:3] - if you need chunk 3
   - [NEED_CHUNKS:2,3,4] - if you need chunks 2, 3, and 4
   - [NEED_CHUNKS:1] - if you need chunk 1
   
   Look at the "Chunk-by-Chunk Summary" in the Full Analysis Context to determine which chunks likely contain the information needed.
   
The system will automatically fetch the raw log content from those chunks and retry your query.

Be specific and cite relevant parts of the context when answering.
Format your responses clearly with markdown when appropriate.
When showing log lines, use code blocks for readability."""

        # Build context message
        context_message = ""
        if chunk_context:
            context_message += f"## Current Chunk Context (Summary)\n{chunk_context}\n\n"
        if shadow_context:
            context_message += f"## Raw Log Content\n{shadow_context}\n\n"
        if full_context:
            context_message += f"## Full Analysis Context\n{full_context}\n\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if context_message:
            messages.append({"role": "user", "content": f"Here is the context from the log analysis:\n\n{context_message}"})
            messages.append({"role": "assistant", "content": "I've reviewed the log analysis context. I'm ready to answer questions about the log file and help troubleshoot any issues found. I can see both summaries and raw log content when available."})
        
        messages.append({"role": "user", "content": user_query})
        
        # Call the Copilot API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2000
        )
        
        assistant_response = response.choices[0].message.content
        
        # Check if specific chunks are needed - parse [NEED_CHUNKS:1,2,3] format
        import re
        chunks_match = re.search(r'\[NEED_CHUNKS?:([0-9,\s]+)\]', assistant_response)
        needs_raw_content = chunks_match is not None
        chunks_requested = []
        
        if chunks_match:
            # Parse the chunk numbers
            chunk_str = chunks_match.group(1)
            chunks_requested = [int(c.strip()) for c in chunk_str.split(',') if c.strip().isdigit()]
            # Clean the response
            clean_response = re.sub(r'\[NEED_CHUNKS?:[0-9,\s]+\]\s*', '', assistant_response).strip()
        else:
            clean_response = assistant_response
        
        return jsonify({
            'response': clean_response,
            'needs_raw_content': needs_raw_content,
            'chunks_requested': chunks_requested
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Log Scanner Supreme")
    print("  Powered by GitHub Copilot API")
    print("="*60)
    print("\n  Starting server at: http://localhost:5000")
    print("\n  Configure your GitHub PAT in Settings (click ⚙️)")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
