"""
Log Scanner Supreme - A web-based log file analyzer
"""

import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from log_analyzer import LogAnalyzer

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'log', 'txt', 'json', 'xml', 'csv', 'out', 'err'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


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
        # Initialize analyzer
        api_key = os.getenv('OPENAI_API_KEY')
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        chunk_size = int(os.getenv('CHUNK_SIZE', '3000'))
        
        if not api_key or api_key == 'your-openai-api-key-here':
            return jsonify({
                'error': 'OpenAI API key not configured. Please add your API key to the .env file.'
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
            # Initialize analyzer
            api_key = os.getenv('OPENAI_API_KEY')
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            chunk_size = int(os.getenv('CHUNK_SIZE', '3000'))
            
            if not api_key or api_key == 'your-openai-api-key-here':
                yield f"data: {json.dumps({'error': 'OpenAI API key not configured'})}\n\n"
                return
            
            analyzer = LogAnalyzer(api_key=api_key, model=model, chunk_size=chunk_size)
            
            # Read file content
            with open(filepath, 'r', errors='replace') as f:
                content = f.read()
            
            # Stream analysis results
            for update in analyzer.analyze_streaming(content):
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


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Log Scanner Supreme")
    print("="*60)
    print("\n  Starting server at: http://localhost:5000")
    print("\n  Make sure you have set your OPENAI_API_KEY in .env file")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
