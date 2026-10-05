# Evaluation

Run `python -m oslab build` and `python -m oslab evaluate` from the repository root. The commands regenerate tracked JSON under `results/`. `python -m unittest discover -s tests -v` checks parsers, feature extraction, normalization, diagnosis, dataset audit, process transitions and scheduling arithmetic.

## Processing

`data/benchmarks/processing.json` independently labels three source experiment IDs and 21 section names with line positions. On the checked demo sources, heading precision and recall, experiment ID accuracy and metadata completeness are each **1.000**. There are zero unresolved concept links and zero duplicates after filtering. This benchmark has no PDF, OCR or external document cases; its result is a correctness check for the current Markdown format.

## Retrieval

`data/benchmarks/retrieval.json` has 12 queries with one relevant record each. Results are experiment filtered. Recall@3, MRR@10 and nDCG@10 are regenerated in `results/retrieval_metrics.json`:

| Method | Recall@3 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| BM25 | 0.917 | 0.701 | 0.777 |
| LSA dense | 0.833 | 0.722 | 0.791 |
| Hybrid | 1.000 | 0.847 | 0.886 |

LSA means TF-IDF bigrams followed by truncated SVD; it is not a neural embedding model. Hybrid uses reciprocal rank fusion and a small section preference for the current mode. Individual ranks are stored so failures can be inspected. The sample is small and synthetic, and only one relevant section is labelled per query.

## Diagnosis

`results/diagnostic_metrics.json` records leave-one-failure-case-out matching over four static fork/wait variants. Top-1 and Top-3 are both 4/4. Two variants share each failure label, so this benchmark is vulnerable to near-related examples and does not estimate performance on unrelated student code. The single correct reference is excluded because there is no second correct case to match when held out. No runtime-only or trace ablation is reported; no Linux trace exists in the committed data.

## Deterministic model tests

Process tests check parent blocking and wakeup, child-first wait returning after child exit, both no-wait output orders, invalid transitions and prediction feedback. Scheduling tests use known FCFS and SJF timelines, a Round Robin case with arrivals, metric calculations and invalid input rejection. These are scenario tests, not a user learning study. Browser smoke testing was performed locally with headless Chrome across the main views and is not a required dependency of the Python test suite.

## Next evaluation improvements

Add independent source formats and labelled section spans for extraction; broader theory queries with concept-level relevance judgments; failure cases across program templates and experiments; and actual Linux traces collected under a safe boundary. Keep per-topic and per-failure error reports when sample sizes permit.
