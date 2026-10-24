"""Deterministic teaching models for seven single-CPU scheduling policies.

This is a teaching simulation. Its frames are calculated states, never actual
kernel observations, and there is no I/O or context-switch overhead.
"""
import re
from copy import deepcopy

DEFAULT_PROCESSES = [
    {"id": "P1", "arrival": 0, "burst": 5},
    {"id": "P2", "arrival": 1, "burst": 3},
    {"id": "P3", "arrival": 2, "burst": 1},
]

ALGORITHMS = {"FCFS", "SJF", "SRTF", "PRIORITY", "RR", "MLQ", "MLFQ"}


def validate(processes, algorithm, quantum):
    """Reject inputs outside the small workload we can explain and display."""
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown scheduling algorithm")
    if not isinstance(processes, list) or not 1 <= len(processes) <= 8:
        raise ValueError("Provide 1 to 8 processes")
    if type(quantum) is not int or not 1 <= quantum <= 10:
        raise ValueError("Quantum must be an integer from 1 to 10")
    ids = set()
    for item in processes:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,7}", item["id"]):
            raise ValueError("Each process needs a short alphanumeric ID")
        if item["id"] in ids:
            raise ValueError("Process IDs must be unique")
        ids.add(item["id"])
        if type(item.get("arrival")) is not int or not 0 <= item["arrival"] <= 20:
            raise ValueError("Arrival must be an integer from 0 to 20")
        if type(item.get("burst")) is not int or not 1 <= item["burst"] <= 20:
            raise ValueError("Burst must be an integer from 1 to 20")
        if type(item.get("priority", 1)) is not int or not 1 <= item.get("priority", 1) <= 10:
            raise ValueError("Priority must be an integer from 1 (highest) to 10")
        if type(item.get("queue", 0)) is not int or item.get("queue", 0) not in {0, 1}:
            raise ValueError("Queue must be 0 (foreground) or 1 (background)")


def simulate(processes=None, algorithm="FCFS", quantum=2):
    """Advance one CPU time unit at a time and record every visible event."""
    processes = deepcopy(DEFAULT_PROCESSES if processes is None else processes)
    validate(processes, algorithm, quantum)
    order = {item["id"]: index for index, item in enumerate(processes)}
    by_id = {item["id"]: {**item, "priority": item.get("priority", 1),
                            "queue": item.get("queue", 0), "level": 0,
                            "remaining": item["burst"], "status": "NEW",
                            "first_start": None, "completion": None} for item in processes}
    ready, running, time, used, gantt, frames = [], None, 0, 0, [], []

    def emit(event, title, actor=None):
        # A snapshot lets the browser replay the schedule without recalculating it.
        frames.append({"step": len(frames), "time": time, "event": event, "actor": actor,
                       "title": title, "concept_id": "round_robin" if algorithm == "RR" else "scheduling",
                       "state": {"ready": list(ready), "running": running,
                                 "processes": deepcopy(by_id), "gantt": deepcopy(gantt)}})

    emit("START", "Workload loaded")
    while any(item["status"] != "COMPLETE" for item in by_id.values()):
        # New arrivals enter the ready queue at the current integer time.
        for item in processes:
            process = by_id[item["id"]]
            if process["status"] == "NEW" and process["arrival"] == time:
                process["status"] = "READY"
                ready.append(item["id"])
                emit("ARRIVAL", f"{item['id']} joins the ready queue", item["id"])
        # SRTF can replace a running job when a strictly shorter one arrives.
        # Both two-queue models interrupt background work for foreground work.
        preempt = (algorithm == "SRTF" and running is not None and
                   any(by_id[pid]["remaining"] < by_id[running]["remaining"] for pid in ready))
        background_interrupted = (algorithm in {"MLQ", "MLFQ"} and running is not None and
            (by_id[running]["queue"] if algorithm == "MLQ" else by_id[running]["level"]) == 1 and
            any((by_id[pid]["queue"] if algorithm == "MLQ" else by_id[pid]["level"]) == 0 for pid in ready))
        if preempt or background_interrupted:
            previous = running
            by_id[previous]["status"] = "READY"
            # An interrupted background job resumes before later background jobs.
            (ready.insert(0, previous) if background_interrupted else ready.append(previous))
            running = None
            emit("PREEMPT", f"{previous} yields to a higher-ranked ready job", previous)
        if running is None and ready:
            if algorithm == "SJF":
                # SJF only chooses at dispatch; it does not interrupt a running job.
                ready.sort(key=lambda pid: (by_id[pid]["burst"], by_id[pid]["arrival"], order[pid]))
            elif algorithm == "SRTF":
                ready.sort(key=lambda pid: (by_id[pid]["remaining"], by_id[pid]["arrival"], order[pid]))
            elif algorithm == "PRIORITY":
                ready.sort(key=lambda pid: (by_id[pid]["priority"], by_id[pid]["arrival"], order[pid]))
            elif algorithm == "MLQ":
                ready.sort(key=lambda pid: by_id[pid]["queue"])
            elif algorithm == "MLFQ":
                ready.sort(key=lambda pid: by_id[pid]["level"])
            running = ready.pop(0)
            by_id[running]["status"] = "RUNNING"
            if by_id[running]["first_start"] is None:
                by_id[running]["first_start"] = time
            used = 0
            emit("DISPATCH", f"{running} gets the CPU", running)
        if running is None:
            gantt.append({"time": time, "process": "IDLE"})
            time += 1
            emit("IDLE", "No process is ready")
            continue
        pid = running
        by_id[pid]["remaining"] -= 1
        gantt.append({"time": time, "process": pid})
        time += 1
        used += 1
        emit("CPU_TICK", f"{pid} runs for one time unit", pid)
        if by_id[pid]["remaining"] == 0:
            by_id[pid]["status"] = "COMPLETE"
            by_id[pid]["completion"] = time
            running = None
            emit("COMPLETE", f"{pid} completes", pid)
        elif (algorithm == "RR" or
              algorithm == "MLQ" and by_id[pid]["queue"] == 0 or
              algorithm == "MLFQ" and by_id[pid]["level"] == 0) and used == quantum:
            # Time slice expired: put this process at the back of the queue.
            if algorithm == "MLFQ":
                by_id[pid]["level"] = 1  # Used a full high-queue quantum: demote.
            by_id[pid]["status"] = "READY"
            ready.append(pid)
            running = None
            emit("DEMOTE" if algorithm == "MLFQ" else "PREEMPT",
                 f"{pid}'s foreground quantum expires", pid)
        if time > 200:
            raise RuntimeError("Simulation exceeded expected bound")
    # Turnaround is total elapsed time; waiting subtracts CPU work from it.
    # Response ends at first dispatch, so RR can have later waiting as well.
    metrics = {pid: {"waiting": item["completion"] - item["arrival"] - item["burst"],
                     "turnaround": item["completion"] - item["arrival"],
                     "response": item["first_start"] - item["arrival"],
                     "completion": item["completion"]} for pid, item in by_id.items()}
    return {"model": "deterministic_cpu_only_scheduling_model", "algorithm": algorithm,
            "quantum": quantum if algorithm in {"RR", "MLQ", "MLFQ"} else None, "processes": processes,
            "frames": frames, "gantt": gantt, "metrics": metrics,
            "tie_break": "FCFS and RR use arrival/input order; SJF uses shortest burst; SRTF uses shortest remaining time; Priority is nonpreemptive (1 highest); MLQ uses foreground RR then background FCFS; MLFQ starts high, demotes after one quantum, and runs low FCFS. CPU-only; ties keep arrival/input order."}
