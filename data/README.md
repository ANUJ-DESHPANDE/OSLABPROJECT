# What is in `data/`

| Path | Purpose |
|---|---|
| `demo/*.md` | Three original, small OS lab notes. The parser in `oslab/knowledge.py` turns their headings into 21 structured teaching sections. |
| `programs/fork_wait/*.c` | Five fixed C examples: one baseline and four deliberately changed variants. Their exact source text is used in controlled comparisons, so they stay as fixtures. See [`programs/fork_wait/README.md`](programs/fork_wait/README.md). |
| `benchmarks/*.json` | Hand-labelled headings, retrieval questions and expected IDs for narrow regression checks. JSON cannot contain comments. |
| `concepts/*.json` | Original concept cards and links used by optional learning views. |
| `processed/` | Generated public demo records. Rebuild with `python -m oslab build`. |
| `private/` | Gitignored local faculty files, reference resources, indexes and model weights. Never part of GitHub. |

The public demo dataset and private course dataset are separate. Scores under `results/` evaluate only the small labelled public demo set unless explicitly stated otherwise.
