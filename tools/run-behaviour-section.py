"""Run named check-behaviour sections alone:  python3 tools/run-behaviour-section.py check_b313_fx check_b317_hundobox [--against FILE]"""
import importlib.util, os, sys
names = [a for a in sys.argv[1:] if a.startswith("check_")]
if "--against" in sys.argv:
    i = sys.argv.index("--against"); AG = ["--against", sys.argv[i + 1]]
else: AG = []
WT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0]] + AG
spec = importlib.util.spec_from_file_location("cb", WT + "/tools/check-behaviour.py")
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME if hasattr(cb, "CHROME") else "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    for n in names: getattr(cb, n)(br)
    br.close()
bad = list(cb.FAILURES)
print("FAILURES:", bad)
