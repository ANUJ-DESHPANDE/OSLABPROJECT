"""Inspectable provenance and quality summary for the public demo datasets."""
import difflib
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from .behaviour import build_cases
from .concepts import load_concepts
from .knowledge import ingest, parse_markdown, save_json

DEMO_SECTIONS = {"Aim", "Theory", "Procedure", "Program", "Expected Output", "Troubleshooting", "Viva"}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def knowledge_sources():
    output = []
    for path in sorted(Path("data/demo").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        records = parse_markdown(path)
        sections = []
        for number, line in enumerate(raw.splitlines(), 1):
            match = re.match(r"## (.+)", line)
            if match:
                sections.append({"name": match.group(1), "line": number,
                                 "record_ids": [r["id"] for r in records if r["section_type"] == match.group(1)]})
        missing = sorted(DEMO_SECTIONS - {s["name"] for s in sections})
        output.append({"source": path.name, "path": str(path).replace("\\", "/"),
                       "source_sha256": digest(raw), "raw_text": raw,
                       "extraction": "UTF-8 Markdown lines; # Experiment and ## section headings",
                       "sections": sections, "record_count": len(records),
                       "warnings": [f"Missing section: {name}" for name in missing]})
    return output


def audit_demo():
    sources = knowledge_sources()
    records = ingest(Path("data/demo").glob("*.md"))
    cases = build_cases()
    concepts = load_concepts()
    record_ids = {r["id"] for r in records}
    concept_warnings = [f"{item['id']}: unknown record {record_id}"
                        for item in concepts for record_id in item["source_records"] if record_id not in record_ids]
    hashes = Counter((r["experiment_id"], r["section_type"], r["content_hash"]) for r in records)
    duplicate_count = sum(count - 1 for count in hashes.values() if count > 1)
    baseline = next(case for case in cases if case["baseline"])
    behaviour = []
    for case in cases:
        diff = "" if case["baseline"] else "\n".join(difflib.unified_diff(
            baseline["source_code"].splitlines(), case["source_code"].splitlines(),
            fromfile="baseline.c", tofile=case["id"] + ".c", lineterm=""))
        behaviour.append({"id": case["id"], "label": case["failure_label"],
                          "baseline": case["baseline"], "mutation_description": case["mutation_description"],
                          "source_path": case["source_path"], "source_sha256": digest(case["source_code"]),
                          "source_code": case["source_code"], "source_diff": diff,
                          "features": case["features"], "expected_events": case["expected_behaviour"],
                          "inferred_from_source": [key for key, value in case["features"].items() if value],
                          "observed_at_runtime": [], "runtime_status": case["compile_result"],
                          "evidence_level": case["evidence_level"]})
    version = digest("\n".join(source["source_sha256"] for source in sources) + "\n" +
                     "\n".join(case["source_sha256"] for case in behaviour) + "\n" +
                     json.dumps(concepts, sort_keys=True))[:16]
    return {"schema_version": 1, "dataset_version": version,
            "pipeline": ["raw Markdown", "heading detection", "section extraction", "logical records",
                         "metadata and content hash", "deduplication", "BM25/LSA representations"],
            "knowledge": {"sources": sources, "records": records,
                          "health": {"source_count": len(sources), "record_count": len(records),
                                     "section_counts": dict(Counter(r["section_type"] for r in records)),
                                     "missing_metadata_count": sum(any(not r.get(field) for field in
                                         ("experiment_id", "section_type", "source", "content_hash", "text")) for r in records),
                                     "duplicate_count_after_filter": duplicate_count,
                                     "warnings": [warning for source in sources for warning in source["warnings"]] + concept_warnings}},
            "concepts": concepts,
            "behaviour": {"cases": behaviour, "health": {"case_count": len(behaviour),
                          "label_counts": dict(Counter(case["label"] for case in behaviour)),
                          "observed_trace_count": 0,
                          "warnings": ["No Linux runtime traces have been collected in this demo snapshot."]}}}


def save_audit(path="results/dataset_audit.json"):
    audit = audit_demo()
    save_json(path, audit)
    return audit
