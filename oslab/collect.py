"""Collect real evidence for checked-in trusted examples on Linux only."""
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from .behaviour import build_cases, normalize_trace
from .knowledge import save_json


def collect_trusted():
    if platform.system() != "Linux" or not shutil.which("gcc"):
        raise RuntimeError("Trusted execution collection requires Linux and gcc; no code was run")
    cases = build_cases()
    with tempfile.TemporaryDirectory(prefix="oslab-trusted-") as temporary:
        directory = Path(temporary)
        for case in cases:
            binary = directory / case["id"]
            compile_run = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", case["source_path"], "-o", str(binary)],
                                         capture_output=True, text=True, timeout=10)
            case["compile_result"] = {"returncode": compile_run.returncode}
            case["compiler_output"] = compile_run.stderr
            if compile_run.returncode != 0:
                continue
            # These are fixed, reviewed repository examples. Student supplied code never reaches this path.
            if shutil.which("strace"):
                trace = directory / (case["id"] + ".trace")
                command = ["strace", "-f", "-e", "trace=process,pipe,read,write,close", "-o", str(trace), str(binary)]
            else:
                trace = None
                command = [str(binary)]
            try:
                run = subprocess.run(command, capture_output=True, text=True, timeout=5, cwd=directory)
                case["runtime_output"] = {"stdout": run.stdout, "stderr": run.stderr, "returncode": run.returncode}
                if trace:
                    case["raw_trace"] = trace.read_text(encoding="utf-8", errors="replace")
                    case["normalized_events"] = normalize_trace(case["raw_trace"])
                case["evidence_level"] = "trusted_linux_trace" if trace else "trusted_linux_runtime"
            except subprocess.TimeoutExpired:
                case["runtime_output"] = {"timeout_seconds": 5}
                case["evidence_level"] = "trusted_linux_timeout"
    save_json("data/processed/behaviour.json", cases)
    return cases
