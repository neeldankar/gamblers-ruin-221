"""Run one command and record its peak memory (used by run_all.py; not an experiment).
    python experiments/peak_wrapper.py OUT.json command [args...]

getrusage(RUSAGE_CHILDREN) covers the children this process has waited for. This wrapper has exactly one child
(the experiment), so the number is that experiment's own peak, including any worker processes it waited for
(e09_four). Writes {"exit_code": ..., "peak_mb": ...} to OUT.json and exits with the command's exit code.
"""
import json
import resource
import subprocess
import sys


def main():
    out, command = sys.argv[1], sys.argv[2:]
    exit_code = subprocess.run(command).returncode  # stdout and stderr go straight to the console
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_mb = rss / 2**20 if sys.platform == "darwin" else rss / 2**10  # bytes on macOS, kilobytes on Linux
    with open(out, "w") as fh:
        json.dump({"exit_code": exit_code, "peak_mb": peak_mb}, fh)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
