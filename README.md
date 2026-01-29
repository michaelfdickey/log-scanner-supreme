# 🔍 Log Scanner Supreme

An AI-powered log file analyzer with a web-based interface. Upload log files, and get intelligent analysis with context-aware issue tracking across the entire file.

## Features

- **📁 Easy Upload**: Drag-and-drop or browse for log files (.log, .txt, .json, .xml, .csv, .out, .err)
- **🧠 Smart Chunking**: Automatically breaks large log files into manageable chunks for analysis
- **⚠️ Issue Detection**: Identifies errors, warnings, failures, and anomalies
- **🔗 Context Awareness**: Maintains a running summary across chunks to understand how issues evolve
- **📊 Comprehensive Reports**: Provides executive summaries, root cause analysis, and actionable recommendations
- **⏱️ Real-time Progress**: Stream updates show analysis progress as each chunk is processed

## Prerequisites

- Python 3.8+
- OpenAI API key

## Installation

1. **Clone the repository**
   ```bash
   cd log-scanner-supreme
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

## Usage

1. **Start the server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to [http://localhost:5000](http://localhost:5000)

3. **Upload a log file**
   - Drag and drop a log file onto the upload area, or
   - Click "Browse Files" to select a file

4. **Analyze**
   Click "Analyze Log" to start the AI-powered analysis

## Configuration Options

Edit the `.env` file to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | The model to use for analysis |
| `CHUNK_SIZE` | `3000` | Target chunk size in tokens |

## How It Works

1. **Pre-processing**: Quickly scans the file for error/warning patterns using regex
2. **Chunking**: Splits the log into chunks that fit within the model's context window
3. **Chunk Analysis**: Each chunk is analyzed with context from previous chunks
4. **Running Summary**: Maintains a cumulative understanding of issues as they progress
5. **Final Report**: Generates a comprehensive summary with findings and recommendations

## Analysis Output

The analyzer provides:

- **Quick Scan Results**: Preliminary count of potential errors and warnings
- **Chunk-by-Chunk Analysis**: Detailed findings for each section of the log
- **Issue Tracking**: All identified issues with severity, type, and possible causes
- **Executive Summary**: Overall health assessment (healthy/degraded/critical)
- **Root Cause Analysis**: Probable causes with confidence levels
- **Recommendations**: Prioritized actions (immediate/short-term/long-term)

## Supported Log Formats

The analyzer works with various log formats:

- Standard application logs
- System logs (syslog, journald)
- Web server logs (Apache, Nginx)
- Application server logs (Tomcat, Node.js)
- Database logs
- Custom application logs
- JSON-formatted logs

## Tips for Best Results

1. **Complete Logs**: Upload full log files rather than snippets for better context
2. **Relevant Timeframes**: Include logs from the time period when issues occurred
3. **Multiple Files**: If you have multiple related log files, analyze them separately and compare
4. **Chunk Size**: Adjust `CHUNK_SIZE` if you need more or less context per analysis

## Security Notes

- Log files are uploaded to a local `uploads/` directory
- Files are automatically deleted after analysis
- Your API key is stored locally in the `.env` file
- No data is sent anywhere except to the OpenAI API for analysis

## Troubleshooting

**"OpenAI API key not configured"**
- Make sure you've created a `.env` file with your API key
- Check that the key is valid and has available credits

**Large file takes too long**
- Try reducing `CHUNK_SIZE` in `.env` for faster (but less detailed) analysis
- Consider splitting very large logs into smaller files

**Analysis seems incomplete**
- Increase `CHUNK_SIZE` for more context per chunk
- Try a more capable model like `gpt-4o`

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.