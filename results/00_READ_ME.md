# What these result files mean

These `.json` files are **generated data**, read by the application and tests. Standard JSON has no comment syntax, so adding `//` or `#` inside them would break the program. This guide sits beside them for anyone opening a random result in VS Code.

| File | Plain-English meaning |
|---|---|
| `demo_behaviour.json` | Five small, reviewed C examples about `fork()` and `wait()`: one reference program and four deliberately changed variants. This is a teaching/regression dataset, not five observed student runs. |
| `demo_knowledge.json` | Twenty-one sections extracted from three original Markdown lab notes. Each record keeps its experiment, section, source and text. |
| `dataset_audit.json` | Shows the raw demo sources, heading positions, section links, hashes, differences between C variants and data-quality warnings. It describes the **public demo data**; the private course import has its own local index and inventory. |
| `processing_metrics.json` | Checks section extraction against 21 labelled headings in the three controlled Markdown files. |
| `retrieval_metrics.json` | Compares BM25, LSA and hybrid retrieval on 12 labelled questions over demo notes. Recall@3 is search relevance on this small set, not answer accuracy on the private course files. |
| `diagnostic_metrics.json` | Compares four closely related static failure variants. The matches are regression checks, not a general debugging success rate. |

## Reading `demo_behaviour.json`

- `baseline: true` marks the reference C program; `failure_label` names the intended variant.
- `source_path` points to the original C file; `source_code` is copied into the record so the audit is inspectable.
- `features` are clues inferred from source text, such as whether `fork()` and `wait()` appear. They are not observations from a real process.
- `expected_behaviour` is a teaching expectation.
- `compile_result: not_run_posix_environment_unavailable`, `runtime_output: null`, `raw_trace: null`, and `normalized_events: []` explicitly mean **no Linux run or trace was collected** for this committed demo snapshot.
- `evidence_level: static_only` tells the reader how strong the record's evidence is.

The source of these records is [`oslab/behaviour.py`](../oslab/behaviour.py). Regenerate with `python -m oslab build`; evaluate with `python -m oslab evaluate`.
