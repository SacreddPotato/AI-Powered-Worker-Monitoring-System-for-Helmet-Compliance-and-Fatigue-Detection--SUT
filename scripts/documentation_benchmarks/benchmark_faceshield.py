"""Benchmark the 'faceshield' model weights against labeled ground truth."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import run_benchmark, write_summary
from specs import SPECS

if __name__ == "__main__":
    write_summary([run_benchmark(SPECS["faceshield"])])
