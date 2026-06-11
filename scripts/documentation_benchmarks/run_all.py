"""Run every documentation benchmark and write the combined summary."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import run_benchmark, write_summary
from specs import SPECS


def main(keys=None):
    selected = keys or list(SPECS)
    results = []
    for key in selected:
        results.append(run_benchmark(SPECS[key]))
    write_summary(results)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
