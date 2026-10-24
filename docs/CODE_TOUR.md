# Code tour for a live review

Start with `web/index.html`: it contains the four visible screens. `web/app.js` reads the forms, calls the local HTTP endpoints, and draws the results. The browser does not read private files directly.

| If the reviewer opens... | Explain it this way |
|---|---|
| `oslab/__main__.py` | The entry point. It loads the datasets, serves the website at `127.0.0.1`, validates requests, and routes each tool to its Python function. `/api/course/ask` searches before asking the local model; `/api/schedule` returns calculated states. |
| `oslab/course.py` | The importer reads supported PDF/PPTX/DOCX files from a ZIP, records skipped files and SHA-256 hashes, and saves short source-linked passages in a private local JSON index. `CourseSearch` fits BM25-like term statistics and TF-IDF/LSA vectors, then ranks passages. |
| `oslab/local_model.py` | Sends only selected excerpts to local Qwen3 4B through llama.cpp or Ollama. It asks for structured, cited answer points and visual steps, and checks IDs and shape. A valid ID is not a proof that every claim is correct. |
| `oslab/code_review.py` | Removes comments/string literals, finds selected OS calls and source line numbers, and reports cautious next checks. One pipe/EOF-loop case has a checked walkthrough. It never compiles or executes pasted code. |
| `oslab/scheduling.py` | Simulates one CPU tick at a time. Ready queue, running process and remaining bursts create event snapshots. Seven named teaching policies choose or interrupt jobs; metrics come from arrival, first start and completion times. |
| `oslab/behaviour.py` | Builds five small reviewed fork/wait cases and extracts simple source signals. These are demo regression cases, not observed student executions. |
| `oslab/knowledge.py` | Parses the three public Markdown lab notes into 21 sections and implements their small benchmark retriever. The private faculty importer is in `course.py`. |
| `oslab/diagnose.py` | Combines static fork/wait clues, similar demo cases and relevant demo notes for the older structured diagnosis endpoint. |
| `oslab/process_model.py` | Runs a small, explicit fork/wait teaching scenario. Its frames and practice answer key come from the same state transitions; they are not kernel traces. |
| `oslab/collect.py` | Optional Linux-only collector for fixed checked-in C examples. The Windows web app does not call it, and pasted student code never reaches it. |
| `oslab/concepts.py` and `oslab/visuals.py` | Load concept links and select a topic hint for a question. The local model writes the actual source-linked visual steps. |
| `oslab/studio.py` and `oslab/evaluate.py` | Expose the data audit and evaluate controlled public demo records. The 12-query retrieval scores do not measure private-course answer accuracy. |
| `results/*.json` | Generated, machine-readable demo records and metrics. JSON cannot contain comments; open [`results/00_READ_ME.md`](../results/00_READ_ME.md) for each field's meaning. |

## Reproduce the diagram on paper

Draw four boxes across the top: **files → extract/chunk → private passage index → hybrid retrieval**. Draw a **student question** arrow into retrieval. From retrieval draw **top source passages → local Qwen model → cited answer + visual steps**. Below, draw separate branches: **pasted code → static checks → related passages**, and **process workload → Python scheduler → Gantt + metrics**. Label private files and model weights as **local only**.

## Key terms

- **Passage:** a short text segment with its source filename and page/slide.
- **BM25:** keyword relevance adjusted for passage length and term rarity.
- **LSA:** statistical similarity from compressed TF-IDF text vectors; not neural embeddings.
- **Hybrid:** combine the ranks from BM25 and LSA.
- **RAG:** retrieve evidence first, then have the local model explain the selected evidence.
- **Static check:** a clue inferred from source text, not proof from a run.
- **Deterministic simulation:** the same input and policy produce the same event sequence.
