# OSLab Copilot: implementation progress

**05 October 2026 · final review of this implementation pass**

## Starting point

The existing published repository had three synthetic OS lab documents, 21 structured records, five static fork/wait cases, BM25/LSA/hybrid retrieval, a 12-query retrieval benchmark, a four-case failure matching benchmark, a local one-form UI, and eight passing tests. Linux runtime execution and tracing had not been performed. The original retrieval and diagnostic results were rerun before product changes and matched the tracked artifacts. The preserved [submission report](SUBMISSION_CURRENT_STATUS_2026-10-05.md) and [facts JSON](SUBMISSION_FACTS_2026-10-05.json) describe that baseline.

## Added in this pass

- **Dataset Studio:** a tracked `results/dataset_audit.json` with raw public source text, heading line positions, source and record hashes, section-to-record links, source differences for failure variants, expected/inferred/observed evidence categories, health checks and a source-derived dataset fingerprint. The UI provides a step-by-step inspection path rather than hiding the processing behind a search box.
- **Processing evaluation:** 21 independently labelled heading positions over the three synthetic Markdown inputs. Precision and recall for those headings, experiment ID accuracy and metadata completeness all measured 1.000. The narrow input format is stated beside the result.
- **Knowledge ingestion improvement:** paragraph layout and fenced code are preserved where possible; oversized plain-text blocks are split. Existing demo records and retrieval results stayed unchanged.
- **Concept library:** six original concept records covering processes, fork, wait, exec, CPU scheduling and Round Robin. Records include prerequisites, claims, misconception IDs, links to lab records where present and official external references.
- **Process Explorer:** explicit state transitions and replayable frames for fork/wait. Parent-first and child-first selections show two valid no-wait orders; both wait schedules keep parent completion after child exit. The UI displays code, parent and child state, event timeline and comparison.
- **Prediction practice:** an answer about the next fork/wait event is checked by the same process model used in the explorer, with a specific misconception signal for selected wrong answers.
- **Scheduling Lab:** deterministic CPU-only FCFS, nonpreemptive SJF and Round Robin. Learners can edit arrival and burst values, step through arrival/dispatch/tick/preemption/completion events, and reveal a Gantt timeline plus calculated waiting, turnaround and response times.
- **Debug-to-learning bridge:** a fork/wait diagnosis links to the relevant visual scenario. The original structured diagnostic result and technical scores remain available.
- **Multi-view UI and documentation:** overview, Learn, Process Explorer, Scheduling Lab, Predict & Practice, Debug and Dataset Studio. Screenshots: [overview](images/overview.png), [process explorer](images/process-explorer.png), [scheduling lab](images/scheduling-lab.png), [dataset studio](images/dataset-studio.png).

## Verification

`python -m unittest discover -s tests -v` passed **21 tests** after the final ingestion change. `python -m oslab build` regenerated 21 instructional records and five behaviour cases. `python -m oslab evaluate` regenerated the processing, retrieval and diagnostic artifacts. The pre-existing retrieval and diagnostic JSON did not change. Local HTTP checks and a headless Chrome smoke run covered the home page, process stepping, run comparison, scheduling, Dataset Studio, static diagnosis and its link back to the explorer; no JavaScript page errors were observed.

| Retrieval method | Recall@3 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| BM25 | 0.917 | 0.701 | 0.777 |
| LSA dense | 0.833 | 0.722 | 0.791 |
| Hybrid | 1.000 | 0.847 | 0.886 |

The diagnostic smoke benchmark remained **4/4 Top-1 and 4/4 Top-3** across closely related static variants. This is not a general diagnostic accuracy estimate. Runtime trace count remains **zero** in the committed behaviour data.

## Architecture changes and reason

The instructional and behaviour datasets remain separate. Original concept records now connect them to teaching modules. The Process Explorer and its practice endpoint share one reducer and frame sequence, so the diagram and answer key come from the same state. Scheduling uses a separate deterministic CPU state model with the same event/frame presentation contract. A universal OS reducer was avoided because the current resource models are too different to justify one large abstraction. Model events remain labelled as simulation, distinct from source inference and observed runtime evidence. No LLM is asked to compute state or grade answers.

## Incomplete modules and next steps

The concept library is still small and scheduling concepts lack mapped lab retrieval records. The Dataset Studio covers strict Markdown and checked-in demo code, not PDF/OCR or arbitrary uploads. The process model intentionally omits signals, multiple children and kernel scheduling detail; the scheduling model omits I/O, context-switch cost, priorities and SRTF. Synchronization, memory and file-system explorers are not yet implemented. Static C analysis remains regex-based. A restricted Linux environment and broader, less correlated behaviour cases are required before runtime diagnosis claims can grow. The optional trusted Linux collector was not run on this Windows machine; pasted student code remains unexecuted.

## GitHub status

The work was committed on `main` in these milestones:

- `17419e0` Add verified current-status submission report
- `a0a9c4d` Add dataset studio and deterministic OS learning modules
- `ff03765` Document learning architecture, datasets, and evaluation
- `b4f693a` Preserve code layout during knowledge ingestion

These commits were pushed to [ANUJ-DESHPANDE/OSLABPROJECT](https://github.com/ANUJ-DESHPANDE/OSLABPROJECT). The final progress report is a separate documentation commit. The public tree was reviewed for private files and credential patterns before push; only original synthetic demo content and linked external references are included.
