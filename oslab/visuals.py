"""Route a question to a mechanism; the local model writes the actual steps."""

import re

MECHANISMS = {
    "page_fault": ("Memory", "Page fault and address translation"),
    "deadlock": ("Synchronization", "Deadlock and resource waiting"),
    "synchronization": ("Synchronization", "Thread coordination"),
    "pipe": ("Interprocess communication", "Pipe and file descriptor flow"),
    "scheduling": ("CPU scheduling", "CPU scheduling decisions"),
    "process": ("Processes", "Process creation and waiting"),
    "files": ("Files and storage", "File and directory operations"),
    "shell": ("Shell and Linux", "Shell command execution"),
}

PATTERNS = [
    ("page_fault", r"page fault|paging|virtual memory|tlb|address translation"),
    ("deadlock", r"deadlock|dining philosopher"),
    ("synchronization", r"semaphore|mutex|lock|critical section|race condition|thread synchron"),
    ("pipe", r"\bpipes?\b|\bipc\b|interprocess communication|file descriptor.*eof"),
    ("scheduling", r"schedul|round robin|\bfcfs\b|\bsjf\b|time slice"),
    ("process", r"\bfork\b|\bwaitpid\b|process creation|parent.*child|\bexec\b"),
    ("files", r"file system|inode|directory|disk|file allocation"),
    ("shell", r"shell|\bbash\b|linux command"),
]


def choose_visual(question, sources=(), topics=()):
    """Return a topic hint, never a generic visual masquerading as an answer."""
    text = question.lower() or " ".join(topics).lower()
    if not text.strip():
        text = " ".join(topics).lower()
    candidates = (text, " ".join(source.get("title", "") for source in sources[:2]).lower())
    for candidate in candidates:
        for key, pattern in PATTERNS:
            if re.search(pattern, candidate):
                topic, title = MECHANISMS[key]
                return {"id": key, "topic": topic, "title": title}
    return None
