"""Conservative source signals for several common OS lab APIs."""

import re


def inspect_code(code):
    """Find selected OS calls and cautious source clues without running code.

    Comments and string literals are removed first so an example mentioned in a
    comment does not masquerade as a real call. This is text inspection, not a
    C parser or proof of runtime behavior.
    """
    clean = re.sub(r"/\*.*?\*/|//[^\n]*",
                   lambda match: "\n" * match.group().count("\n"), code, flags=re.S)
    clean = re.sub(r'"(?:\\.|[^"\\])*"', '""', clean)
    positions = {name: [clean.count("\n", 0, match.start()) + 1 for match in
                         re.finditer(r"\b" + re.escape(name) + r"\s*\(", clean)] for name in
             ("fork", "wait", "waitpid", "execve", "execl", "execlp", "execv", "execvp",
              "pipe", "read", "write", "close", "pthread_create", "pthread_join",
              "pthread_detach", "pthread_mutex_lock", "pthread_mutex_unlock",
              "sem_wait", "sem_post", "open", "malloc", "free")}
    calls = {name: len(lines) for name, lines in positions.items()}
    present = [name for name, count in calls.items() if count]
    shell = bool(re.search(r"^\s*#!.*(?:bash|sh)\b", code))
    findings = []

    def add(topic, observation, next_check, relevant=()):
        # Every warning points to a check the student can perform, not a verdict.
        findings.append({"topic": topic, "observation": observation, "next_check": next_check,
                         "lines": sorted({line for name in relevant for line in positions[name]}),
                         "evidence_level": "source_signal_not_runtime_proof"})

    if calls["fork"] and not (calls["wait"] or calls["waitpid"]):
        add("processes", "fork() appears without wait()/waitpid().",
            "If the parent must finish after the child, check where it waits. Asynchronous code may intentionally omit wait.", ("fork",))
    if calls["pipe"] and not calls["close"]:
        add("pipes", "pipe() appears without any close() call.",
            "Check whether each process closes unused pipe ends; an open write end can keep a reader waiting for EOF.", ("pipe",))
        if calls["read"] and re.search(r"\bwhile\s*\([^;{}]*\bread\s*\(", clean, flags=re.S):
            add("pipes", "A read() loop appears with no close() call anywhere in this source.",
                "If the loop relies on EOF, close every unused pipe write end after fork(); otherwise the reader may wait indefinitely.",
                ("read", "fork", "wait", "waitpid"))
    if calls["pthread_create"] and not (calls["pthread_join"] or calls["pthread_detach"]):
        add("threads", "pthread_create() appears without pthread_join() or pthread_detach().",
            "Check how thread completion and resources are handled before the process exits.", ("pthread_create",))
    if calls["pthread_mutex_lock"] > calls["pthread_mutex_unlock"]:
        add("locks", "The text contains more mutex lock calls than unlock calls.",
            "Inspect each control-flow path. A text count alone cannot prove a lock leak.", ("pthread_mutex_lock",))
    if calls["sem_wait"] and not calls["sem_post"]:
        add("semaphores", "sem_wait() appears without sem_post() in this source.",
            "Check which thread or process releases the semaphore; release may deliberately occur elsewhere.", ("sem_wait",))
    if calls["open"] and not calls["close"]:
        add("files", "open() appears without close() in this source.",
            "Check who owns the descriptor and whether it is closed on success and error paths.", ("open",))
    if any(calls[name] for name in ("execve", "execl", "execlp", "execv", "execvp")):
        add("exec", "An exec-family call appears in the source.",
            "On success exec replaces the current process. Check the error path for a failed exec call.",
            ("execve", "execl", "execlp", "execv", "execvp"))
    if not present and not shell:
        add("general", "No supported OS API call was detected by the static checks.",
            "Provide the task requirement and observed output; the local model can still explain retrieved course material.")
    topics = [name for name, active in (("processes", calls["fork"] or calls["waitpid"]),
                                           ("pipes", calls["pipe"]),
                                           ("threads", calls["pthread_create"]),
                                           ("locks", calls["pthread_mutex_lock"]),
                                           ("semaphores", calls["sem_wait"] or calls["sem_post"]),
                                           ("files", calls["open"]),
                                           ("shell", shell)) if active]
    return {"language_hint": "shell" if shell else "C/C++ or unknown", "calls": present,
            "topics": topics, "findings": findings, "execution_status": "not_executed"}


def retrieval_query(question, inspection):
    """Add OS terms suggested by detected calls to search the course index."""
    terms = {
        "processes": "fork waitpid process parent child",
        "pipes": "pipe file descriptor close read write IPC EOF",
        "threads": "pthread create join thread concurrency",
        "locks": "mutex lock unlock race condition",
        "semaphores": "semaphore sem_wait sem_post synchronization",
        "files": "open close file descriptor file system",
        "shell": "shell programming Linux commands",
    }
    return " ".join([question[:250]] + [terms[topic] for topic in inspection["topics"]]).strip()


def pipe_eof_walkthrough(code, inspection, sources):
    """Explain one checked pipe/EOF pattern using pasted line numbers.

    The source proves that no close() call is written here; it does not prove
    what this student's program did at runtime.
    """
    calls = set(inspection["calls"])
    if not {"pipe", "fork", "read"} <= calls or "close" in calls:
        return None
    if not any(item["observation"].startswith("A read() loop") for item in inspection["findings"]):
        return None
    source_id = next((index for index, source in enumerate(sources, 1)
                      if "pipe" in source["text"].lower() and "eof" in source["text"].lower()
                      and "write" in source["text"].lower()), None)
    if source_id is None:
        return None
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", lambda match: "\n" * match.group().count("\n"), code, flags=re.S)
    clean = re.sub(r'"(?:\\.|[^"\\])*"', '""', clean)
    lines = clean.splitlines()

    def line_of(name):
        return next((index for index, line in enumerate(lines, 1)
                     if re.search(r"\b" + re.escape(name) + r"\s*\(", line)), 0)

    pipe_line, read_line = line_of("pipe"), line_of("read")
    write_line, wait_line = line_of("write"), line_of("wait") or line_of("waitpid")
    answer = (f"A pipe reader gets EOF only after every write end closes [{source_id}]. "
              f"This source has a read() loop at line {read_line} and no close() call; after fork(), "
              "both processes can retain a write end. The loop may therefore keep waiting for EOF. "
              + (f"The parent also waits at line {wait_line}, so it may remain blocked while the reader waits. "
                 if wait_line else "")
              + "Close unused pipe ends in each process, including the reader's inherited write end, "
                "and close the writer's end after its final write.")
    steps = [
        {"label": "Create the pipe", "detail": "pipe() creates a read end and a write end; fork() shares both descriptors with the child.",
         "source_id": source_id, "code_line": pipe_line},
        {"label": "Reader waits for EOF", "detail": "The read() loop continues until EOF. This source contains no close() call, so a write end can stay open.",
         "source_id": source_id, "code_line": read_line},
    ]
    if write_line:
        steps.append({"label": "Writer sends data", "detail": "write() sends bytes, but the source never closes the write end after the final write.",
                      "source_id": source_id, "code_line": write_line})
    if wait_line:
        steps.append({"label": "Parent waits", "detail": "wait() needs the child to exit; a child still waiting for EOF may leave the parent blocked too.",
                      "source_id": source_id, "code_line": wait_line})
    steps.append({"label": "Close unused ends", "detail": "Close the reader's inherited write end and close the writer's end after sending data, then rerun and observe.",
                  "source_id": source_id, "code_line": 0})
    return {"answer": answer, "citations_used": [source_id], "has_valid_citation": True,
            "model": "Checked source walkthrough", "origin": "static",
            "visual": {"title": "Why this reader may wait for EOF", "steps": steps,
                       "evidence_level": "source_grounded_static_hypothesis_not_runtime_trace"}}
