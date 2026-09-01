import subprocess
import sys

def run_git():
    print("1. Running git add . ...", flush=True)
    subprocess.run(["git", "add", "."], check=True)

    print("2. Running git commit...", flush=True)
    res = subprocess.run(
        ["git", "commit", "-m", "Add landing page and authenticated dashboard, wired to the real backend API"],
        capture_output=True,
        text=True
    )
    print("Commit output:", res.stdout or res.stderr, flush=True)

    print("3. Running git push origin main...", flush=True)
    push_res = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True
    )
    print("Push output:", push_res.stdout or push_res.stderr, flush=True)

if __name__ == "__main__":
    try:
        run_git()
    except Exception as e:
        print("Git error:", e, flush=True)
