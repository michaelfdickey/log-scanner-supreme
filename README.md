# 🔍 Log Scanner Supreme

An AI-powered log file analyzer with a web-based interface. Upload log files, and get intelligent analysis with context-aware issue tracking across the entire file.

**Powered by GitHub Copilot API** 🤖

## Features

- **📁 Easy Upload**: Drag-and-drop or browse for log files (.log, .txt, .json, .xml, .csv, .out, .err)
- **🧠 Smart Chunking**: Automatically breaks large log files into manageable chunks for analysis
- **⚠️ Issue Detection**: Identifies errors, warnings, failures, and anomalies
- **🔗 Context Awareness**: Maintains a running summary across chunks to understand how issues evolve
- **📊 Comprehensive Reports**: Provides executive summaries, root cause analysis, and actionable recommendations
- **⏱️ Real-time Progress**: Stream updates show analysis progress as each chunk is processed

## Prerequisites

- Python 3.8+
- GitHub account with Copilot access
- GitHub Personal Access Token (PAT) with Copilot permissions

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

4. **Configure your GitHub PAT**
   
   Option A: Use the Settings UI (recommended)
   - Start the app and click the ⚙️ Settings button
   - Enter your GitHub PAT and click Save
   
   Option B: Use environment file
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your GitHub PAT:
   ```
   GITHUB_PAT=ghp_your-token-here
   ```

## Getting a GitHub Personal Access Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token (classic or fine-grained)
3. Ensure your GitHub account has Copilot access
4. Copy the token (starts with `ghp_` or `github_pat_`)

## Usage

1. **Start the server**
   ```bash
   python launcher.py   # Recommended: handles venv and cleanup
   # or
   python app.py
   ```

   Specify a different port if you want to run the server on a port other than the default 5000 using `-p <port>`:
      ```bash
      python launcher.py -p 5050
      ```


2. **Open your browser**
   Navigate to [http://localhost:5000](http://localhost:5000) or your specified port, e.g., [http://localhost:5050](http://localhost:5050) if you used `-p 5050`.

3. **Configure** (if not already done)
   - Click the ⚙️ Settings button
   - Enter your GitHub PAT
   - Click "Test Connection" to verify
   - Save settings

4. **Upload a log file**
   - Drag and drop a log file onto the upload area, or
   - Click "Browse Files" to select a file

5. **Analyze**
   Click "Analyze Log" to start the AI-powered analysis

## Configuration Options

Configure via Settings UI or edit `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_PAT` | (required) | Your GitHub Personal Access Token |
| `COPILOT_MODEL` | `gpt-4o-mini` | The model to use for analysis |
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
- Your GitHub PAT is stored locally in the `.env` file
- Data is sent to the GitHub Copilot API for analysis

## Troubleshooting

**"GitHub PAT not configured"**
- Click the ⚙️ Settings button and enter your GitHub PAT
- Make sure your GitHub account has Copilot access
- Test the connection using the "Test Connection" button

**"Unauthorized" error**
- Your PAT may have expired - generate a new one
- Ensure your GitHub account has active Copilot subscription

**Large file takes too long**
- Try reducing `CHUNK_SIZE` in Settings for faster (but less detailed) analysis
- Consider splitting very large logs into smaller files

**Analysis seems incomplete**
- Increase `CHUNK_SIZE` for more context per chunk
- Try a more capable model like `gpt-4o`

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Local Hoster

Configured for supporting the `Local Hoster` app:
https://github.com/michaelfdickey/local-hoster