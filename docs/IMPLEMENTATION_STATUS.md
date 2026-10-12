# Implementation status

This describes the current local study companion. The [05 October submission report](SUBMISSION_CURRENT_STATUS_2026-10-05.md) is a preserved snapshot of the earlier lab diagnostic prototype.

## Working now

- Private course ZIP import for PDF pages, PPTX slides, and DOCX text, with archive safety checks, normalized chunks, source hashes, page/slide locations, and recorded skip reasons. The current local archive produced 33 documents and 553 passages; private files are gitignored.
- Local retrieval over those passages and 21 separately labeled original project lab notes: BM25, statistical LSA, and reciprocal-rank hybrid. Search shows original excerpts even when no model is running.
- Optional free local model server through Ollama or llama.cpp. It receives retrieved excerpts and generates a cited short answer and source-linked, question-specific visual steps. Citation numbers and step source IDs are checked before displaying generated output.
- C/shell lab-code review with conservative static OS API clues and source line numbers, related local retrieval, a checked walkthrough for the pipe/EOF-loop pattern, and optional model suggestions for other cases. Pasted student code is never compiled or executed.
- Deterministic FCFS, nonpreemptive SJF, and Round Robin scheduling with ready queue, event stepping, Gantt timeline, and calculated timings.
- Dataset view with course import counts, per-file passage counts and SHA-256 fingerprints, skipped-entry reasons, and the separately audited synthetic instructional and behavior corpora. The original fork/wait process model remains available contextually for relevant questions.
- Python unit tests and a browser smoke check for the main views.

## Boundaries

- The private course archive has no labeled relevance benchmark. The existing public retrieval and diagnostic benchmark scores cover only small synthetic examples and cannot be claimed as accuracy for university material.
- The code reviewer uses source patterns, not full C control flow or a runtime trace. It can miss issues and can flag intentional code.
- Generated explanations and visuals can be wrong even with citations; users can inspect the retrieved text. The visual steps are explanatory models, not a replay of a student's code.
- Scanned images and legacy Office formats are not extracted. CPU scheduling assumes integer CPU bursts without I/O, priority, or context-switch cost.

## Next engineering work

Add an independently labeled private-corpus relevance set, stronger document extraction and OCR, deeper source analysis, and separate tested simulators for memory and synchronization. Do not turn a model-generated illustration into a claimed kernel trace.
