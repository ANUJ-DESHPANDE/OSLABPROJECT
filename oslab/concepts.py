"""Load the small concept map used by the optional learning views."""

import json
from pathlib import Path


def load_concepts():
    """Read concept records and reject missing or duplicate prerequisite links."""
    # JSON is data, so the relation check lives here rather than as JSON comments.
    concepts = [item for path in sorted(Path("data/concepts").glob("*.json"))
                for item in json.loads(path.read_text(encoding="utf-8"))]
    ids = {item["id"] for item in concepts}
    if len(ids) != len(concepts):
        raise ValueError("Duplicate concept ID")
    for item in concepts:
        if not set(item["prerequisites"]).issubset(ids):
            raise ValueError(f"Unknown prerequisite for {item['id']}")
    return concepts


def concept_for_failure(label):
    """Send a known fork/wait failure label to the relevant teaching concept."""
    # The demo failure set is small; unknown labels fall back to fork.
    return "wait" if label in {"missing_wait", "wait_in_child"} else "fork"
