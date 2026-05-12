"""
Run this file from the PROJECT ROOT to start the backend server.
Usage:  python run_backend.py
"""
import os
import sys

# Add the backend directory to Python's module search path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

if __name__ == "__main__":
    import subprocess
    uvicorn_exe = os.path.join(backend_dir, "venv", "Scripts", "uvicorn.exe")
    
    # Fix for Windows Store Python Venv Reload Bug
    # Using the uvicorn executable directly preserves the venv context for subprocesses
    if os.path.exists(uvicorn_exe):
        print(f"Starting server using Uvicorn executable at: {uvicorn_exe}")
        sys.exit(subprocess.call([uvicorn_exe, "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]))
    else:
        import uvicorn
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
