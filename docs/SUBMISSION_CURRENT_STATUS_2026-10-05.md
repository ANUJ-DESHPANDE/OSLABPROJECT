# OSLab Copilot
## Current Status Report

**Anuj Deshpande** · **24BCE0794** · **Operating Systems Lab** · **05 October 2026**

This report describes the repository as verified on 05 October 2026. Its measurements were regenerated from the checked-in demo data. Features identified as planned are not included in the current results.

## 1. Introduction

OSLab Copilot currently combines structured retrieval of Operating Systems lab instructions with source-based diagnosis of selected C program failures. It addresses a limitation of a document-only assistant: relevant instructions describe expected behaviour, but they do not establish what a student's program does. The prototype therefore stores instructional evidence and behaviour cases separately and presents the signals behind a diagnosis. It runs locally without an LLM or an API key.

The current implementation focuses on the fork/wait experiment. It is a working diagnostic prototype, not yet a general OS tutor or runtime debugger. The approved next direction is an interactive OS learning environment connecting lessons, deterministic simulations, prediction exercises, and program diagnosis.

## 2. Literature Review

[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/) organizes core material around virtualization, concurrency, and persistence. Its Process API material provides conceptual context for `fork`, `exec`, and `wait`. MIT's [xv6 teaching resources](https://ocw.mit.edu/courses/6-828-operating-system-engineering-fall-2012/resources/lecture-notes/) show how OS concepts can be connected to concrete implementation. The [Linux man-pages project](https://www.man7.org/linux/man-pages/man7/intro.7.html) provides API-oriented reference material. These are contextual references, not copied into the public dataset. The project's synthetic lab documents are original demo inputs; private faculty material is not included.

The technical design combines conventional information retrieval with program evidence. BM25 matches terms, while Latent Semantic Analysis (LSA) projects TF-IDF features into a dense latent space. Reciprocal rank fusion combines their ranked lists. This is classical LSA, not a neural embedding model. The diagnostic layer uses named source features and known failure cases rather than asking an LLM to infer a failure from prose alone.

## 3. Objective

**Implemented and verified now:** ingest structured demo instructions; preserve experiment and section metadata; compare lexical, LSA, and hybrid retrieval; extract selected C source signals; match controlled fork/wait failures; produce a structured, evidence-labelled diagnosis through a local UI and API.

**Planned next development:** a broader original OS concept library, an inspectable Dataset Studio, deterministic process exploration and prediction exercises, and later scheduling and other OS models. A safe Linux execution environment is required before student code can be run or runtime evidence can be claimed.

## 4. Dataset Collection

### A. Knowledge and instructional dataset

The public raw inputs are three synthetic Markdown files in `data/demo/`: `fork_wait.md`, `exec.md`, and `pipe.md`. Each contains one experiment with seven named sections: Aim, Theory, Procedure, Program, Expected Output, Troubleshooting, and Viva. The verified build produces **21 records**, seven per experiment. This is demonstration data, not a collected university textbook corpus. The files `data/private/` and `data/university/` are gitignored locations for any locally held material; the current build loads only `data/demo/`.

Each processed record stores an ID, experiment ID and name, topic, section type, source filename, section position, language, SHA-256 content hash, and text. The tracked snapshot is `results/demo_knowledge.json`; the working output is `data/processed/knowledge.json`. The record hash supports content comparison, but the current pipeline has no separate dataset-version manifest. The repository commit and the input files provide the reproducible version context.

### B. Behaviour and failure dataset

The raw program inputs are five reviewed POSIX C files in `data/programs/fork_wait/`: one **reference representation** and four controlled variants. Two variants omit the parent's wait; two put a wait call in the child branch. Their labels are `correct` (one case), `missing_wait` (two), and `wait_in_child` (two). Each generated record stores its source code and path, mutation description, label, static features, expected event sequence, explanation, and evidence status. The tracked snapshot is `results/demo_behaviour.json`.

“Reference” denotes the intended correct source structure, **not a verified Linux run**. On this Windows machine the five cases have `static_only` evidence, `compile_result` marked `not_run_posix_environment_unavailable`, null runtime output and raw trace, and empty normalized events. Expected events are teaching expectations; source features are inferences from code; no runtime events were observed. A Linux-only collector exists for fixed, reviewed repository examples, but it was not run here. Arbitrary student code is never executed by the local app.

## 5. Dataset Processing

### Instructional pipeline

The implemented path is: **Markdown source → heading/section detection → text extraction → logical-section records → metadata and SHA-256 hash → duplicate filtering → retrieval representations → benchmark**. The parser recognizes `# Experiment ID: Name` and known `##` sections. It keeps a logical section intact unless it exceeds 350 words, when it splits within that section. It removes surrounding blank lines and joins words in each chunk. Duplicate detection uses experiment ID, section type, and content hash. It does not currently ingest arbitrary PDFs or scanned pages, and no manual concept mapping has been implemented.

The retrieval index is built in memory from record text, section name, and topic. A query may be filtered to the current experiment; mode-dependent section preference affects hybrid ranking. The benchmark contains 12 labelled queries, each with a known relevant record. Rerunning `python -m oslab evaluate` reproduced these results:

| Method | Recall@3 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|
| BM25 | 0.917 | 0.701 | 0.777 |
| LSA dense | 0.833 | 0.722 | 0.791 |
| Hybrid | 1.000 | 0.847 | 0.886 |

Exact values and per-query ranks are in `results/retrieval_metrics.json`. The benchmark is small, synthetic, and experiment-filtered; these numbers do not establish performance on university documents or open-ended OS questions.

### Behaviour pipeline

The implemented path is: **reviewed source program → named controlled variant → static feature extraction → expected behaviour field → evidence record → feature-based failure matching → structured diagnosis**. The extractor checks for `fork`, `wait`/`waitpid`, whether a wait occurs in a simple child branch, and selected exec, pipe, close, and semaphore calls. The matcher exposes matched and different signals for each known case. The Debug result separately labels source-inferred events and user-supplied output. The regex-based extractor is limited to the demonstration C patterns; it is not a complete C control-flow parser.

The diagnostic benchmark holds out each of four failure cases and matches it against the remaining records. It reproduced **4/4 Top-1 and 4/4 Top-3** on two closely related failure families. The result is a small static-feature smoke test with near-related variants, **not “100% diagnostic accuracy” on unseen student programs**. Case predictions are in `results/diagnostic_metrics.json`. No behaviour-only or runtime-trace ablation is reported because no Linux traces were collected.

## 6. Model Architecture Design

The local Python service has a knowledge parser and retriever, a behaviour record builder and feature extractor, a case matcher, a rule-based diagnostic layer, evaluation commands, and a browser UI. BM25 supplies lexical ranking. TF-IDF bigrams followed by truncated SVD supply LSA dense vectors. Hybrid ranking uses reciprocal rank fusion with a small mode preference. The diagnostic rules compare the fork/wait expectation with source signals, attach matched failure cases and retrieved sections, and create a structured result before deterministic explanation text. The UI exposes both the student-facing result and a technical JSON view with scores and features.

The app binds to localhost and never compiles or runs pasted code. An optional trusted-example collector is restricted to checked-in programs on Linux with GCC; it is not a sandbox for student submissions. There is no LLM integration, neural embedding model, deterministic simulator, concept map, or prediction engine in the current release.

The audit reran `python -m unittest discover -s tests -v`: **8 tests passed**. `python -m oslab build` regenerated 21 instructional records and 5 behaviour records. Retrieval and diagnostic evaluation matched the tracked artifacts without a diff. A local HTTP check returned 200 for the app page, and a Debug API request returned the `missing_wait` label. The repository was clean on `main` before this report was added.

## 7. Conclusion

The present contribution is a reproducible two-dataset prototype: structure-aware instructional processing, measured retrieval, and an inspectable static diagnosis of controlled fork/wait mistakes. Its strongest current evidence is the visible path from raw demo files to processed records and from reviewed C variants to named diagnostic signals. Its main limits are the small synthetic corpus, closely related failure cases, regex-based source analysis, and absence of verified Linux execution traces.

The next development should make dataset provenance and processing inspectable in the product, then connect the existing fork/wait diagnosis to a tested process-state explorer and prediction activity. Broader OS coverage and runtime tracing should be added only with verified source rights, correctness tests, and an appropriate execution boundary.
