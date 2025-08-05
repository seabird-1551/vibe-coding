#!/usr/bin/env python3
"""
Startup script for AI-Powered Data Quality Checker
Runs both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import streamlit
        import pandas
        import openai
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_backend():
    """Start FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.backend.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ]
    return subprocess.Popen(backend_cmd)

def start_frontend():
    """Start Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run",
        "app/frontend/streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    return subprocess.Popen(frontend_cmd)

def main():
    """Main startup function"""
    print("🤖 AI-Powered Data Quality Checker")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Creating from template...")
        if os.path.exists('env.example'):
            import shutil
            shutil.copy('env.example', '.env')
            print("✅ Created .env file from template")
            print("📝 Please edit .env file and add your OpenAI API key")
        else:
            print("❌ No env.example file found")
    
    # Create necessary directories
    Path("uploads").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        processes.append(backend_process)
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        # Start frontend
        frontend_process = start_frontend()
        processes.append(frontend_process)
        
        print("\n" + "=" * 50)
        print("🎉 Application is starting up!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:8501")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for processes
        while True:
            time.sleep(1)
            # Check if any process has died
            for process in processes:
                if process.poll() is not None:
                    print(f"❌ Process {process.pid} has stopped unexpectedly")
                    return
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 