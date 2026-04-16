"""Launch backend (Daphne) and frontend (Vite) dev servers together.

Usage:
    python run.py           # both servers
    python run.py --backend # backend only
    python run.py --frontend # frontend only
"""
import os
import sys
<<<<<<< HEAD
import subprocess
import argparse
import threading
=======
import signal
import subprocess
import argparse
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

<<<<<<< HEAD
IS_WINDOWS = sys.platform == "win32"


def _watch(proc, name, on_exit):
    """Wait for a process to finish and report its exit."""
    code = proc.wait()
    if code != 0:
        print(f"\n[run] {name} exited with code {code}")
    else:
        print(f"\n[run] {name} stopped")
    on_exit()


def _kill(proc, name):
    """Forcefully kill a process (works on Windows where terminate() hangs)."""
    try:
        if IS_WINDOWS:
            # taskkill /F /T kills the process tree — avoids Daphne's
            # "killed N pending application instances" hang
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    except OSError:
        pass


def _ensure_backend_database() -> bool:
    """Ensure SQLite file/schema exists by running Django migrations."""
    print("[run] Ensuring local database is ready (migrations)...")
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print(f"[run] Database setup failed (exit code {result.returncode})")
        return False
    return True

=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

def run():
    parser = argparse.ArgumentParser(description="Run the monitoring dashboard")
    parser.add_argument("--backend", action="store_true", help="Backend only")
    parser.add_argument("--frontend", action="store_true", help="Frontend only")
    args = parser.parse_args()

    both = not args.backend and not args.frontend
<<<<<<< HEAD
    procs = {}  # name -> Popen
    shutdown = threading.Event()

    def trigger_shutdown():
        shutdown.set()

    if both or args.backend:
        if not _ensure_backend_database():
            return
        print("[run] Starting backend — Daphne on :7860")
        procs["Backend"] = subprocess.Popen(
            [sys.executable, "-m", "daphne", "-b", "0.0.0.0", "-p", "7860",
             "sentinel.asgi:application"],
            cwd=BACKEND_DIR,
        )

    if both or args.frontend:
        npm = "npm.cmd" if IS_WINDOWS else "npm"
        print("[run] Starting frontend — Vite on :5173")
        procs["Frontend"] = subprocess.Popen(
            [npm, "run", "dev"],
            cwd=FRONTEND_DIR,
        )

    if not procs:
        print("[run] Nothing to start")
        return

    # Start watcher threads — if either process dies, trigger shutdown
    for name, proc in procs.items():
        t = threading.Thread(target=_watch, args=(proc, name, trigger_shutdown), daemon=True)
        t.start()

    if both:
        print("[run] Dashboard ready:")
        print("      Frontend  → http://localhost:5173")
        print("      Backend   → http://localhost:7860")
        print("      Press Ctrl+C to stop both.\n")

    try:
        # Block until Ctrl+C or a process exits
        while not shutdown.is_set():
            shutdown.wait(timeout=0.5)
    except KeyboardInterrupt:
        pass

    print("\n[run] Shutting down...")
    for name, proc in procs.items():
        if proc.poll() is None:  # still running
            _kill(proc, name)
    print("[run] Done.")
=======
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
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649


if __name__ == "__main__":
    run()
