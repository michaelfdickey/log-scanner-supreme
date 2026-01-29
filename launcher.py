#!/usr/bin/env python3
"""
Log Scanner Supreme - Launcher Script

This script:
1. Kills any existing instance of the app running on port 5000
2. Activates the virtual environment
3. Launches the application
"""

import os
import sys
import subprocess
import signal
import platform

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, 'venv')
APP_FILE = os.path.join(SCRIPT_DIR, 'app.py')
PORT = 5000


def get_python_executable():
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == 'Windows':
        python_path = os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    else:
        python_path = os.path.join(VENV_DIR, 'bin', 'python')
    
    if not os.path.exists(python_path):
        print(f"❌ Virtual environment not found at {VENV_DIR}")
        print("\nPlease create it first:")
        print(f"  cd {SCRIPT_DIR}")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    return python_path


def kill_existing_process():
    """Kill any process running on the target port."""
    print(f"🔍 Checking for existing processes on port {PORT}...")
    
    system = platform.system()
    
    try:
        if system == 'Darwin' or system == 'Linux':
            # Use lsof to find process on port
            result = subprocess.run(
                ['lsof', '-ti', f':{PORT}'],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"⚠️  Killing existing process (PID: {pid})...")
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                print("✅ Existing processes terminated")
            else:
                print("✅ No existing process found on port")
                
        elif system == 'Windows':
            # Use netstat to find process on port
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if f':{PORT}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    print(f"⚠️  Killing existing process (PID: {pid})...")
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    print("✅ Existing process terminated")
                    break
            else:
                print("✅ No existing process found on port")
                
    except Exception as e:
        print(f"⚠️  Could not check for existing processes: {e}")


def check_dependencies():
    """Check if required packages are installed."""
    python = get_python_executable()
    
    print("📦 Checking dependencies...")
    
    result = subprocess.run(
        [python, '-c', 'import flask; import openai; import tiktoken; import dotenv'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("❌ Missing dependencies. Installing...")
        requirements_file = os.path.join(SCRIPT_DIR, 'requirements.txt')
        subprocess.run([python, '-m', 'pip', 'install', '-r', requirements_file])
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies satisfied")


def launch_app():
    """Launch the Flask application."""
    python = get_python_executable()
    
    print(f"\n🚀 Launching Log Scanner Supreme...")
    print(f"   URL: http://localhost:{PORT}")
    print(f"   Press Ctrl+C to stop\n")
    print("=" * 50)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    # Launch the app
    try:
        process = subprocess.run(
            [python, APP_FILE],
            cwd=SCRIPT_DIR,
            env=env
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)


def main():
    print("\n" + "=" * 50)
    print("  Log Scanner Supreme - Launcher")
    print("=" * 50 + "\n")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Kill any existing instance
    kill_existing_process()
    
    # Check dependencies
    check_dependencies()
    
    # Launch the app
    launch_app()


if __name__ == '__main__':
    main()
