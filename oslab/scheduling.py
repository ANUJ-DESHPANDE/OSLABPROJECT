"""Deterministic CPU-only FCFS, nonpreemptive SJF, and Round Robin model."""
import re
from copy import deepcopy

DEFAULT_PROCESSES = [
    {"id": "P1", "arrival": 0, "burst": 5},
    {"id": "P2", "arrival": 1, "burst": 3},
    {"id": "P3", "arrival": 2, "burst": 1},
]


def validate(processes, algorithm, quantum):
    if algorithm not in {"FCFS", "SJF", "RR"}:
        raise ValueError("Algorithm must be FCFS, SJF or RR")
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


def simulate(processes=None, algorithm="FCFS", quantum=2):
    processes = deepcopy(DEFAULT_PROCESSES if processes is None else processes)
    validate(processes, algorithm, quantum)
    order = {item["id"]: index for index, item in enumerate(processes)}
    by_id = {item["id"]: {**item, "remaining": item["burst"], "status": "NEW",
                            "first_start": None, "completion": None} for item in processes}
    ready, running, time, used, gantt, frames = [], None, 0, 0, [], []

    def emit(event, title, actor=None):
        frames.append({"step": len(frames), "time": time, "event": event, "actor": actor,
                       "title": title, "concept_id": "round_robin" if algorithm == "RR" else "scheduling",
                       "state": {"ready": list(ready), "running": running,
                                 "processes": deepcopy(by_id), "gantt": deepcopy(gantt)}})

    emit("START", "Workload loaded")
    while any(item["status"] != "COMPLETE" for item in by_id.values()):
        for item in processes:
            process = by_id[item["id"]]
            if process["status"] == "NEW" and process["arrival"] == time:
                process["status"] = "READY"
                ready.append(item["id"])
                emit("ARRIVAL", f"{item['id']} joins the ready queue", item["id"])
        if running is None and ready:
            if algorithm == "SJF":
                ready.sort(key=lambda pid: (by_id[pid]["burst"], by_id[pid]["arrival"], order[pid]))
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
        elif algorithm == "RR" and used == quantum:
            by_id[pid]["status"] = "READY"
            ready.append(pid)
            running = None
            emit("PREEMPT", f"{pid}'s quantum expires", pid)
        if time > 200:
            raise RuntimeError("Simulation exceeded expected bound")
    metrics = {pid: {"waiting": item["completion"] - item["arrival"] - item["burst"],
                     "turnaround": item["completion"] - item["arrival"],
                     "response": item["first_start"] - item["arrival"],
                     "completion": item["completion"]} for pid, item in by_id.items()}
    return {"model": "deterministic_cpu_only_scheduling_model", "algorithm": algorithm,
            "quantum": quantum if algorithm == "RR" else None, "processes": processes,
            "frames": frames, "gantt": gantt, "metrics": metrics,
            "tie_break": "Input order after arrival for FCFS/RR; burst, arrival, input order for SJF. RR preemption enters the queue before arrivals at the next integer time."}
