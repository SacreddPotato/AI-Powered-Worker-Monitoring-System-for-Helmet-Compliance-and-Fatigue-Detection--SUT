"""Launch backend (Daphne) and frontend (Vite) dev servers together.

Usage:
    python run.py           # both servers
    python run.py --backend # backend only
    python run.py --frontend # frontend only
"""
import os
import sys
import signal
import subprocess
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")


def run():
    parser = argparse.ArgumentParser(description="Run the monitoring dashboard")
    parser.add_argument("--backend", action="store_true", help="Backend only")
    parser.add_argument("--frontend", action="store_true", help="Frontend only")
    args = parser.parse_args()

    both = not args.backend and not args.frontend
    procs = []

    try:
        if both or args.backend:
            print("[run] Starting backend — Daphne on :7860")
            procs.append(subprocess.Popen(
                [sys.executable, "-m", "daphne", "-b", "0.0.0.0", "-p", "7860",
                 "sentinel.asgi:application"],
                cwd=BACKEND_DIR,
            ))

        if both or args.frontend:
            npm = "npm.cmd" if sys.platform == "win32" else "npm"
            print("[run] Starting frontend — Vite on :5173")
            procs.append(subprocess.Popen(
                [npm, "run", "dev"],
                cwd=FRONTEND_DIR,
            ))

        if both:
            print("[run] Dashboard ready:")
            print("      Frontend  → http://localhost:5173")
            print("      Backend   → http://localhost:7860")
            print("      Press Ctrl+C to stop both.\n")

        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\n[run] Shutting down...")
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    run()
