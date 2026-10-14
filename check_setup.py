"""Run this once before the workshop: python check_setup.py

It checks your Python version, the installed packages, Git, and that you can
download SkillCorner Open Data.
"""
import importlib
import os
import shutil
import subprocess
import sys

ok = True


def report(name, passed, detail=""):
    global ok
    ok &= passed
    print(f"[{'OK' if passed else 'FAIL'}] {name}{': ' + detail if detail else ''}")


report("Python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0])

for pkg in ["kloppy", "pandas", "numpy", "matplotlib", "mplsoccer", "PIL"]:
    try:
        mod = importlib.import_module(pkg)
        report(pkg, True, getattr(mod, "__version__", ""))
    except ImportError as exc:
        report(pkg, False, f"{exc}. Run: pip install -r requirements.txt")

git = shutil.which("git")
if git:
    name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
    report("git installed", True, subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip())
    report("git user.name set", bool(name), name or 'run: git config --global user.name "Your Name"')
else:
    report("git installed", False, "see README for install instructions")

if ok:
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src import load

        data_dir = os.environ.get("WORKSHOP_DATA_DIR")
        print("Downloading 300 frames of tracking and the event file (needs internet)...")
        ds = load.load_tracking(data_dir=data_dir, limit=300)
        ev = load.load_events(data_dir=data_dir)
        report("SkillCorner tracking", len(ds) > 0, f"{len(ds)} frames, teams: {[t.name for t in ds.metadata.teams]}")
        report("SkillCorner events", len(ev) > 0, f"{len(ev)} events")
    except Exception as exc:  # noqa: BLE001 - show any failure to the student
        report("SkillCorner data", False, repr(exc))

print("\nAll set, see you at the workshop!" if ok else "\nSomething is missing. Fix the FAIL lines above or ask in the Triton Ball chat.")
sys.exit(0 if ok else 1)
