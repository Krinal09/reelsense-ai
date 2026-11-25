"""One-command launcher:  python run.py   → http://localhost:8000
Installs missing dependencies, builds the UI once, loads .env if present, starts everything."""
import os, subprocess, sys, shutil, webbrowser, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def sh(cmd):
    print("›", " ".join(cmd)); subprocess.check_call(cmd, shell=(os.name == "nt"))

try:
    import fastapi, uvicorn, numpy, openpyxl, reportlab, httpx  # noqa
except ImportError:
    sh([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-local.txt"])

if os.path.exists(".env"):
    for line in open(".env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip())

if not os.path.isdir("dist"):
    if not shutil.which("npm"):
        sys.exit("Node.js is required once to build the UI: install it from https://nodejs.org and run again.")
    if not os.path.isdir("node_modules"):
        sh(["npm", "install", "--no-audit", "--no-fund"])
    sh(["npm", "run", "build"])

port = int(os.environ.get("PORT", "8000"))
threading.Timer(2.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
import uvicorn
uvicorn.run("api.index:app", host="127.0.0.1", port=port)
