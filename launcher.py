#!/usr/bin/env python3
"""
Log Scanner Supreme - Launcher Script
Compatible with Local Hoster desktop app.

This script:
1. Parses -p (frontend port) and -b (backend port) flags
2. Kills any existing instance of the app running on the target port
3. Activates the virtual environment
4. Launches the application

Usage:
    python launcher.py -p 5001 -b 8001
"""

import os
import sys
import subprocess
import signal
import platform
import time
import argparse

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, 'venv')
APP_FILE = os.path.join(SCRIPT_DIR, 'app.py')
DEFAULT_PORT = 5000


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


def kill_existing_process(port):
    """Kill any process running on the target port."""
    print(f"🔍 Checking for existing processes on port {port}...")
    
    system = platform.system()
    
    try:
        if system == 'Darwin' or system == 'Linux':
            # Use lsof to find process on port
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
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
                
                # Wait briefly for processes to terminate
                time.sleep(1)
                
                # Force kill any that are still alive
                result2 = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result2.stdout.strip():
                    for pid in result2.stdout.strip().split('\n'):
                        if pid:
                            print(f"⚠️  Force killing stubborn process (PID: {pid})...")
                            try:
                                os.kill(int(pid), signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                    time.sleep(0.5)
                
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
                if f':{port}' in line and 'LISTENING' in line:
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


def launch_app(port):
    """Launch the Flask application on the given port."""
    python = get_python_executable()
    
    print(f"\n🚀 Launching Log Scanner Supreme on port {port}...")
    print(f"   URL: http://localhost:{port}")
    print(f"   Press Ctrl+C to stop\n")
    print("=" * 50)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    # Launch the app
    try:
        process = subprocess.run(
            [python, APP_FILE, '--port', str(port)],
            cwd=SCRIPT_DIR,
            env=env
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)


def parse_args():
    """Parse command-line arguments for Local Hoster compatibility."""
    parser = argparse.ArgumentParser(description='Log Scanner Supreme Launcher')
    parser.add_argument('-p', '--frontend-port', type=int, default=DEFAULT_PORT,
                        help=f'Frontend port (default: {DEFAULT_PORT})')
    parser.add_argument('-b', '--backend-port', type=int, default=None,
                        help='Backend port (accepted for compatibility; unified server uses frontend port)')
    return parser.parse_args()


def main():
    args = parse_args()
    app_port = args.frontend_port

    if args.backend_port and args.backend_port != app_port:
        print(f"ℹ️  Note: Log Scanner Supreme is a unified server. Running on port {app_port} (frontend port).")
        print(f"   The -b flag ({args.backend_port}) is accepted for compatibility but this app serves both UI and API on one port.")

    print("\n" + "=" * 50)
    print("  Log Scanner Supreme - Launcher")
    print("=" * 50 + "\n")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Kill any existing instance
    kill_existing_process(app_port)
    
    # Check dependencies
    check_dependencies()
    
    # Launch the app
    launch_app(app_port)


if __name__ == '__main__':
    main()
