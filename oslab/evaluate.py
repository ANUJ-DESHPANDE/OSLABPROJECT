import json
import math
from pathlib import Path
from .behaviour import build_cases, match_cases
from .knowledge import Retriever, load_demo, save_json
from .studio import audit_demo


def processing_evaluation():
    labels = json.loads(Path("data/benchmarks/processing.json").read_text(encoding="utf-8"))
    audit = audit_demo()
    sources = {item["source"]: item for item in audit["knowledge"]["sources"]}
    records = audit["knowledge"]["records"]
    expected = {(item["source"], name, line) for item in labels for name, line in item["headings"]}
    actual = {(item["source"], section["name"], section["line"])
              for item in sources.values() for section in item["sections"]}
    correct = len(expected & actual)
    experiment_correct = sum(all(record["experiment_id"] == item["experiment_id"]
                                 for record in records if record["source"] == item["source"]) for item in labels)
    fields = ("id", "experiment_id", "experiment_name", "topic", "section_type", "source", "page_section", "language", "content_hash", "text")
    present = sum(bool(record.get(field)) for record in records for field in fields)
    return {"source_count": len(labels), "labelled_section_count": len(expected),
            "section_heading_precision": correct / len(actual), "section_heading_recall": correct / len(expected),
            "experiment_id_accuracy": experiment_correct / len(labels),
            "metadata_completeness": present / (len(records) * len(fields)),
            "duplicate_count_after_filter": audit["knowledge"]["health"]["duplicate_count_after_filter"],
            "unresolved_concept_link_count": len(audit["knowledge"]["health"]["warnings"]),
            "qualification": "Three synthetic Markdown sources with 21 labelled section headings; no PDF or OCR evaluation."}


def retrieval_evaluation():
    records = load_demo()
    retriever = Retriever(records)
    queries = json.loads(Path("data/benchmarks/retrieval.json").read_text(encoding="utf-8"))
    results = {}
    for method in ("bm25", "dense", "hybrid"):
        ranks = []
        for item in queries:
            got = retriever.search(item["query"], item["experiment"], item["mode"], method, 10)
            rank = next((i for i, r in enumerate(got, 1) if r["id"] == item["relevant_id"]), None)
            ranks.append(rank)
        results[method] = {"recall_at_3": sum(r is not None and r <= 3 for r in ranks) / len(ranks),
                           "mrr_at_10": sum(1 / r for r in ranks if r) / len(ranks),
                           "ndcg_at_10": sum(1 / math.log2(r + 1) for r in ranks if r) / len(ranks),
                           "ranks": ranks}
    return {"query_count": len(queries), "methods": results,
            "model": "TF-IDF bigrams + TruncatedSVD latent semantic analysis; BM25; reciprocal rank fusion"}


def diagnostic_evaluation():
    cases = build_cases()
    rows = []
    for case in cases:
        if case["baseline"]:
            continue
        matches = match_cases(case["features"], cases, exclude_id=case["id"], top_k=3)
        rows.append({"case": case["id"], "label": case["failure_label"],
                     "top1": matches[0]["failure_label"], "top3": [m["failure_label"] for m in matches]})
    return {"case_count": len(rows), "top1_accuracy": sum(r["label"] == r["top1"] for r in rows) / len(rows),
            "top3_accuracy": sum(r["label"] in r["top3"] for r in rows) / len(rows),
            "evidence": "leave-one-failure-case-out static features only; two variants per failure label; no Linux execution or trace",
            "cases": rows}


def run():
    processing = processing_evaluation()
    retrieval = retrieval_evaluation()
    diagnostic = diagnostic_evaluation()
    save_json("results/processing_metrics.json", processing)
    save_json("results/retrieval_metrics.json", retrieval)
    save_json("results/diagnostic_metrics.json", diagnostic)
    return processing, retrieval, diagnostic
