# OS Lab Companion

A local Operating Systems study tool built around the university course archive. Ask a theory question, review C or shell lab code, or run a CPU scheduling simulation. The data pipeline and analysis are part of this project; the local language model explains selected evidence and creates a question-specific visual walkthrough.

## Run locally

From this folder in PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m oslab import-course "$env:USERPROFILE\Downloads\OS.zip"
python -m oslab serve --port 8001
```

Open <http://127.0.0.1:8001>. Keep this PowerShell window open. The archive only needs importing once unless its contents change. The course ZIP, extracted index, and model file stay in gitignored `data/private/`.

An optional **OS Concepts textbook resources** collection is indexed separately with `python -m oslab import-reference <local-reference-zip>`. On this laptop it contains a supplied 8th-edition PDF and Wiley's 10th-edition publisher companion slides. The Ask OS source selector defaults to course notes and can include or isolate these resources. Each hit names its edition and source type. The full prescribed 10th-edition textbook is not indexed; no textbook files are committed to GitHub.

The app can show ranked source passages and static code findings without a model. To enable generated explanations and visual steps on this laptop, open a **second PowerShell window** in this folder and run `powershell -ExecutionPolicy Bypass -File .\start_model.ps1`; leave it open. This uses the downloaded local GGUF and llama.cpp runtime in `data/private/`. On a new machine, install [Ollama](https://ollama.com/download), run `ollama pull qwen3:4b-instruct`, and ensure its local server is running on port 11434. A llama.cpp server with a compatible GGUF model on port 8080 works too. Model status is shown in **Ask OS**. The model receives only selected passages and any code pasted into the local browser; no hosted API key is needed.

## A simple demo

1. **Ask OS:** enter `Why does a page fault happen?` Show the short explanation, step-by-step visual, and the source filename plus slide/page under it. Switch between hybrid, BM25, and LSA ranking if asked about retrieval.
2. **Review lab code:** paste a small C program that uses `pipe()` or `fork()` and ask what might go wrong. Show the source-based clues, related course excerpts, and code-specific visual. The app does not execute student code; findings are hypotheses to check.
3. **Scheduling lab:** choose a built-in workload and run FCFS, nonpreemptive SJF, SRTF, nonpreemptive Priority, Round Robin, a two-level fixed Multilevel Queue, or a two-level Multilevel Feedback Queue. Step through events and show the timeline and timing metrics.
4. **How the data works:** show imported document and passage counts, expand the source inventory to show per-file passage counts and SHA-256 fingerprints, and inspect skipped files and the separate public lab datasets.

The current private archive produced **33 searchable documents and 553 passages** from PDFs, PPTX slides, and DOCX files. Search also includes **21 original project lab notes**, labeled separately in results. The importer skipped 21 archive entries, mostly unsupported older PowerPoint files and images. These are counts, not a relevance score.
The separate textbook-resource import produced **3,445 passages from 22 files**: one supplied 8th-edition PDF and 21 publisher slide decks for the 10th edition. These counts are also extraction results, not measured answer quality.

## What happens behind the screen

```mermaid
flowchart LR
  ZIP[Course ZIP] --> EX[Extract PDF pages, slides, documents]
  EX --> CH[Normalize and chunk text]
  CH --> IDX[Local passage index with source locations]
  Q[Student question] --> RET[BM25 + LSA + rank fusion]
  IDX --> RET
  RET --> SRC[Cited course excerpts]
  SRC --> LLM[Optional local model]
  LLM --> OUT[Explanation + specific visual steps]
  CODE[Student code] --> STATIC[Static source checks]
  STATIC --> RET
  STATIC --> OUT
```

The importer preserves source filename, page/slide and passage text for each hit; source-file SHA-256 is shown in the inventory audit. It guards archive size and paths, skips unsupported files, and records why each file was skipped. Search combines lexical BM25 with LSA, a low-rank representation of local TF-IDF text, using reciprocal-rank fusion. **LSA here is statistical similarity, not a neural embedding model.** The source cards remain visible even if no model is running.

The model is **not fine-tuned on these files**. A normal model session may answer a general OS question similarly, but it does not automatically know which local faculty slide or supplied textbook page this project retrieved. The reproducible distinction is the local document import, ranked source passages, visible source locations, static code clues, and calculated scheduling events. Citation IDs are checked for validity, although a generated sentence still needs human scrutiny.

The code reviewer recognizes selected process, pipe, thread, mutex, exec, and shell clues and reports source line numbers. It builds a relevant search across course passages and labeled project notes from the code and the student's question, then asks the local model to explain likely issues with citations. Static checks inspect up to 20,000 characters; the model sees the first 6,000, and the UI flags either limit. This is not a compiler, a runtime trace, or proof that a particular bug occurred. For fork/wait questions, a more detailed deterministic process walkthrough is linked contextually; it is one topic in the wider OS course, not the app's main subject.

The scheduler is deliberately **single CPU and CPU-only**. Priority value 1 is highest. In Multilevel Queue, foreground jobs use Round Robin and can interrupt background FCFS jobs; queue membership never changes. In Multilevel Feedback Queue, all jobs start high, use one Round Robin quantum, then move to low FCFS; a new high job can interrupt a low job. These are explicit teaching policies, not an attempt to reproduce a real operating system's scheduler. Multiprocessor scheduling, deadlocks, and the rest of the syllabus are available as course-search topics rather than numeric simulations.

Visual steps are generated for retrieved theory questions, with a source number for each step. For the supported pipe/EOF loop pattern, a checked static walkthrough uses exact code lines and source notes because the local model sometimes invented descriptor operations. Other code reviews use the local model when its source and visual checks pass. These visuals explain a mechanism; they do not claim to replay the user's actual program. The deterministic scheduling lab computes results independently of the model.

## Evidence and limits

The private course archive has not been given a labeled relevance benchmark. The public synthetic dataset has separate labeled retrieval and diagnostic checks, described in [evaluation](docs/evaluation.md), but those numbers must not be presented as accuracy on the university archive. Scanned images and legacy `.ppt`/`.doc` are not extracted. The model can still make mistakes; inspect the cited passages before relying on an answer.

Run tests with `python -m unittest discover -s tests -q`. Technical details are in [architecture](docs/architecture.md), [dataset](docs/dataset.md), and [evaluation](docs/evaluation.md).

For a reviewer opening random files, [the code tour](docs/CODE_TOUR.md) maps each visible feature to its implementation and states what its output means.

## License

MIT for project code and original demo content; see [LICENSE](LICENSE). University material and model weights retain their own terms and are not committed.
