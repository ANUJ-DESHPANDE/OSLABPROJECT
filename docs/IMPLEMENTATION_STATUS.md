# Implementation status

Status after the learning-platform iteration. The [current-status submission report](SUBMISSION_CURRENT_STATUS_2026-10-05.md) is an earlier, immutable snapshot of the lab diagnostic prototype.

## Implemented and tested

- Two public demo datasets: 21 structured instructional records and five reviewed fork/wait source cases.
- Dataset Studio audit with source text, section positions, source/record hashes, record metadata, source diffs, warnings, a dataset fingerprint and measured processing results.
- BM25, LSA and hybrid retrieval; 12-query benchmark retained without metric changes.
- Static fork/wait diagnosis with named case matches, retrieved evidence and a link to the process explanation.
- Six original concept records with prerequisites, claims, misconceptions and official external reading links.
- Deterministic fork/wait Process Explorer with parent-first and child-first schedules, a step timeline, state replay and output comparison.
- Prediction exercise graded from the same process model.
- CPU-only FCFS, SJF and Round Robin scheduling with event stepping, ready queue, progressive Gantt timeline and calculated metrics.
- Local multi-view UI, JSON endpoints, 21 passing Python tests and browser smoke checks.

## Experimental or limited

- The process explorer is a small teaching model, not a Linux process trace. It does not model signals, reparenting or all interleavings.
- Scheduling has no I/O, priority, context-switch cost or preemptive SJF.
- Static C detection uses simple regexes and can miss or misclassify complex branch structures.
- The Dataset Studio displays the public demo pipeline. It does not ingest arbitrary uploads, PDFs or private university material.
- The diagnostic benchmark has only four closely related failure variants. No broad diagnostic accuracy claim is justified.
- The trusted Linux collector is available as a separate command but was not run on this Windows machine.

## Planned

Rights-cleared and independently annotated source expansion; deeper concept coverage; safer sandboxed Linux execution for student code; more varied failure cases; stronger static C parsing; synchronization, memory and file descriptor models; and optional contextual LLM explanation constrained by retrieved and computed evidence. New models should be added only with independent correctness tests and meaningful connections to the concept and diagnostic flows.
