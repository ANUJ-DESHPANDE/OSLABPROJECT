import re
from pathlib import Path
from .knowledge import save_json

EVENTS = {"clone": "PROCESS_CREATE", "fork": "PROCESS_CREATE", "vfork": "PROCESS_CREATE",
          "wait4": "PARENT_WAIT", "waitpid": "PARENT_WAIT", "execve": "CHILD_EXEC",
          "pipe": "PIPE_CREATE", "pipe2": "PIPE_CREATE", "read": "READ",
          "write": "WRITE", "close": "CLOSE", "exit_group": "PROCESS_EXIT"}


def normalize_trace(raw):
    """Extract syscall classes; discard PID, fd, addresses, timestamps and return noise."""
    result = []
    for line in raw.splitlines():
        match = re.search(r"\b([a-z][a-z0-9_]*)\(", line)
        if match and match.group(1) in EVENTS:
            event = EVENTS[match.group(1)]
            if not result or result[-1] != event:
                result.append(event)
    return result


def static_features(source):
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    clean = re.sub(r'"(?:\\.|[^"\\])*"', '""', clean)
    wait = bool(re.search(r"\bwait(?:pid)?\s*\(", clean))
    child_branch = re.search(r"if\s*\(\s*\w+\s*==\s*0\s*\)\s*\{(?P<body>[^{}]*)\}", clean)
    child_wait = bool(child_branch and re.search(r"\bwait(?:pid)?\s*\(", child_branch.group("body")))
    return {"fork_present": bool(re.search(r"\bfork\s*\(", clean)),
            "wait_present": wait, "wait_in_child_branch": child_wait,
            "parent_wait_present": wait and not child_wait,
            "exec_present": bool(re.search(r"\bexec\w*\s*\(", clean)),
            "pipe_present": bool(re.search(r"\bpipe\s*\(", clean)),
            "close_call_count": len(re.findall(r"\bclose\s*\(", clean)),
            "semaphore_present": bool(re.search(r"\bsem_(?:wait|post)\s*\(", clean))}


CASES = {
    "baseline": ("correct", "Reference program: parent waits for child", True),
    "missing_wait_a": ("missing_wait", "Removed waitpid from parent", False),
    "missing_wait_b": ("missing_wait", "Parent returns in switch default without waiting", False),
    "wait_in_child_a": ("wait_in_child", "Moved wait into child branch", False),
    "wait_in_child_b": ("wait_in_child", "Moved waitpid into child branch", False),
}


def build_cases():
    result = []
    for name, (label, mutation, baseline) in CASES.items():
        path = Path("data/programs/fork_wait") / (name + ".c")
        source = path.read_text(encoding="utf-8")
        features = static_features(source)
        result.append({"id": name, "experiment_id": "FW01", "failure_label": label,
                       "baseline": baseline, "mutation_description": mutation,
                       "source_path": str(path).replace("\\", "/"), "source_code": source,
                       "compile_result": "not_run_posix_environment_unavailable",
                       "compiler_output": None, "runtime_output": None, "raw_trace": None,
                       "normalized_events": [], "features": features,
                       "expected_behaviour": ["PROCESS_CREATE", "PARENT_WAIT", "CHILD_EXIT", "PARENT_RESUME"],
                       "explanation": {"correct": "Parent calls waitpid before completion.",
                                       "missing_wait": "Parent has no wait; completion order is not synchronized.",
                                       "wait_in_child": "A wait in the child cannot synchronize the parent."}[label],
                       "evidence_level": "static_only"})
    return result


def save_cases(path="data/processed/behaviour.json"):
    cases = build_cases()
    save_json(path, cases)
    return cases


def match_cases(features, cases, exclude_id=None, top_k=3):
    keys = ("fork_present", "wait_present", "wait_in_child_branch", "parent_wait_present")
    scored = []
    for case in cases:
        if case["id"] == exclude_id:
            continue
        matched = [key for key in keys if features[key] == case["features"][key]]
        mismatched = [key for key in keys if key not in matched]
        scored.append({"id": case["id"], "failure_label": case["failure_label"],
                       "matched_signals": matched, "different_signals": mismatched,
                       "score": len(matched) / len(keys)})
    return sorted(scored, key=lambda x: (-x["score"], x["id"]))[:top_k]
