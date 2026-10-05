"""A small explicit teaching model, not a real process scheduler or trace."""
from copy import deepcopy

EVENTS = {
    "FORK": ("fork() returns in two processes", "fork", 5),
    "PARENT_WAIT": ("Parent calls waitpid and blocks", "wait", 8),
    "PARENT_WAIT_IMMEDIATE": ("Parent calls waitpid after the child has exited; it returns immediately", "wait", 8),
    "CHILD_RUN": ("Child is selected to run", "process", 7),
    "CHILD_WORK": ("Child prints its completion message", "fork", 7),
    "CHILD_EXIT": ("Child exits; a waiting parent becomes ready", "wait", 7),
    "PARENT_RESUME": ("waitpid returns and reaps the child", "wait", 8),
    "PARENT_OUTPUT": ("Parent prints its completion message", "wait", 9),
    "PARENT_EXIT": ("Parent exits", "process", 10),
}

CODE = [
    "#include <stdio.h>",
    "#include <sys/wait.h>",
    "#include <unistd.h>",
    "int main(void) {",
    "    const int use_wait = 1;",
    "    pid_t child = fork();",
    "    if (child < 0) { perror(\"fork\"); return 1; }",
    "    if (child == 0) { puts(\"child finished\"); return 0; }",
    "    if (use_wait) waitpid(child, NULL, 0);",
    "    puts(\"parent complete\");",
    "    return 0;",
    "}",
]


def event_plan(use_wait=True, schedule="parent_first"):
    if schedule not in {"parent_first", "child_first"}:
        raise ValueError("Unknown schedule")
    if use_wait:
        if schedule == "parent_first":
            return ["FORK", "PARENT_WAIT", "CHILD_RUN", "CHILD_WORK", "CHILD_EXIT", "PARENT_RESUME", "PARENT_OUTPUT", "PARENT_EXIT"]
        return ["FORK", "CHILD_RUN", "CHILD_WORK", "CHILD_EXIT", "PARENT_WAIT_IMMEDIATE", "PARENT_OUTPUT", "PARENT_EXIT"]
    if schedule == "parent_first":
        return ["FORK", "PARENT_OUTPUT", "PARENT_EXIT", "CHILD_RUN", "CHILD_WORK", "CHILD_EXIT"]
    return ["FORK", "CHILD_RUN", "CHILD_WORK", "CHILD_EXIT", "PARENT_OUTPUT", "PARENT_EXIT"]


def initial_state():
    return {"parent": "RUNNING", "child": "NOT_CREATED", "child_reaped": False,
            "output": [], "active": "parent"}


def apply_event(state, event):
    state = deepcopy(state)
    if event == "FORK":
        assert state["child"] == "NOT_CREATED"
        state["child"] = "READY"
    elif event == "PARENT_WAIT":
        assert state["parent"] == "RUNNING" and state["child"] == "READY"
        state["parent"], state["active"] = "BLOCKED", None
    elif event == "PARENT_WAIT_IMMEDIATE":
        assert state["parent"] == "READY" and state["child"] == "EXITED"
        state["parent"], state["active"], state["child_reaped"] = "RUNNING", "parent", True
    elif event == "CHILD_RUN":
        assert state["child"] == "READY"
        if state["parent"] == "RUNNING":
            state["parent"] = "READY"
        state["child"], state["active"] = "RUNNING", "child"
    elif event == "CHILD_WORK":
        assert state["child"] == "RUNNING"
        state["output"].append("child finished")
    elif event == "CHILD_EXIT":
        assert state["child"] == "RUNNING"
        state["child"] = "EXITED"
        if state["parent"] == "BLOCKED":
            state["parent"] = "READY"
        state["active"] = None
    elif event == "PARENT_RESUME":
        assert state["parent"] == "READY" and state["child"] == "EXITED"
        state["parent"], state["active"], state["child_reaped"] = "RUNNING", "parent", True
    elif event == "PARENT_OUTPUT":
        assert state["parent"] in {"RUNNING", "READY"}
        state["parent"], state["active"] = "RUNNING", "parent"
        state["output"].append("parent complete")
    elif event == "PARENT_EXIT":
        assert state["parent"] == "RUNNING"
        state["parent"], state["active"] = "EXITED", None
    else:
        raise ValueError(f"Unknown event: {event}")
    assert sum(state[name] == "RUNNING" for name in ("parent", "child")) <= 1
    return state


def scenario(use_wait=True, schedule="parent_first"):
    state = initial_state()
    frames = [{"step": 0, "event": "START", "title": "Parent begins", "concept_id": "process",
               "code_line": None, "state": deepcopy(state)}]
    for step, event in enumerate(event_plan(use_wait, schedule), 1):
        state = apply_event(state, event)
        title, concept_id, code_line = EVENTS[event]
        frames.append({"step": step, "event": event, "title": title, "concept_id": concept_id,
                       "code_line": code_line, "state": deepcopy(state)})
    return {"model": "deterministic_teaching_model_not_runtime_trace", "use_wait": use_wait,
            "schedule": schedule, "code": [line.replace("use_wait = 1", f"use_wait = {int(use_wait)}") for line in CODE], "frames": frames,
            "teaching_point": "With wait, parent completion follows child exit. Without wait, both output orders are valid in this simplified model."}


def grade_prediction(use_wait, schedule, step, answer):
    frames = scenario(use_wait, schedule)["frames"]
    if not isinstance(step, int) or step < 0 or step >= len(frames) - 1:
        raise ValueError("Invalid step")
    expected = frames[step + 1]["event"]
    correct = answer == expected
    misconception = None
    if not correct and expected == "PARENT_WAIT" and answer == "CHILD_RUN":
        misconception = "fork_runs_child_first"
    elif not correct and not use_wait and answer == "PARENT_WAIT":
        misconception = "wait_forces_global_order"
    return {"correct": correct, "expected_event": expected, "chosen_event": answer,
            "misconception_id": misconception, "next_state": frames[step + 1]["state"] if correct else None,
            "explanation": EVENTS[expected][0] + ". This is a teaching scenario, not an observed trace."}
