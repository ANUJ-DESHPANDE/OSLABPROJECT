from .behaviour import static_features, match_cases


def diagnose(source, output, experiment, retriever, cases, question=""):
    features = static_features(source or "")
    output = output or ""
    signals = []
    if features["fork_present"]:
        signals.append("fork() found in source")
    if features["wait_present"]:
        signals.append("wait/waitpid call found in source")
    else:
        signals.append("no wait/waitpid call found in source")
    if features["wait_in_child_branch"]:
        signals.append("wait call is inside the child branch")
    if output:
        signals.append("student supplied output; execution was not performed by this service")

    if experiment == "FW01" and features["fork_present"] and not features["wait_present"]:
        label, issue, next_check, strength = "missing_wait", "Missing parent-child synchronization", "Inspect the parent branch for wait() or waitpid().", "strong_static"
    elif experiment == "FW01" and features["wait_in_child_branch"]:
        label, issue, next_check, strength = "wait_in_child", "Wait is called in the child branch", "Move waitpid to the parent branch and check its return value.", "strong_static"
    elif experiment == "FW01" and features["parent_wait_present"]:
        label, issue, next_check, strength = "correct", "No known fork/wait pattern detected", "Check return values and verify actual output in a Linux sandbox.", "limited_static"
    else:
        label, issue, next_check, strength = "unknown", "Insufficient evidence for a specific diagnosis", "Provide source code and compiler or runtime output.", "insufficient"

    retrieved = retriever.search(question or issue, experiment=experiment, mode="Debug", k=4)
    matches = match_cases(features, cases)
    observed = []
    if features["fork_present"]:
        observed.append("PROCESS_CREATE (inferred from source; not traced)")
    if features["parent_wait_present"]:
        observed.append("PARENT_WAIT (inferred from source; not traced)")
    if features["wait_in_child_branch"]:
        observed.append("CHILD_WAIT (inferred from source; not traced)")
    if output:
        observed.append("USER_OUTPUT: " + output[:300])
    return {"likely_issue": issue, "failure_label": label, "evidence_strength": strength,
            "supporting_signals": signals, "expected_behaviour": ["PROCESS_CREATE", "PARENT_WAIT", "CHILD_EXIT", "PARENT_RESUME"] if experiment == "FW01" else [],
            "observed_behaviour": observed, "matched_failure_cases": matches,
            "retrieved_sources": retrieved, "next_check": next_check,
            "features": features, "execution_status": "not_executed_static_analysis_only",
            "explanation": f"{issue}. {next_check} The conclusion is based on source signals and retrieved course material; no runtime trace was captured."}
