"""Reproduce every result in the project, in order.
Run from the repo root:  python run_all.py
Set SKIP_DOWNLOAD=1 to reuse the committed data/clean/ snapshot."""
import os
import subprocess
import sys

DOWNLOADS = ["code/01_download_data_strategyA.py",
             "code/03_download_data_strategyC.py"]
ANALYSIS = ["code/02_backtest_strategyA.py",
            "code/04_backtest_strategyC.py",
            "code/05_risk_analysis.py",
            "code/06_build_web.py",
            "code/07_build_slides.py",
            ]

steps = ANALYSIS if os.environ.get("SKIP_DOWNLOAD") == "1" else DOWNLOADS + ANALYSIS
for script in steps:
    print(f"\n{'=' * 70}\nRunning {script}\n{'=' * 70}")
    subprocess.run([sys.executable, script], check=True)
print("\nAll steps finished.")
