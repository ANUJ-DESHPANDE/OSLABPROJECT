# Datasets and processing

## Public source inventory

The current public knowledge inputs are three original Markdown lab documents: `fork_wait.md`, `exec.md`, and `pipe.md`. Each has one experiment and seven logical sections. The behaviour inputs are five reviewed C files in `data/programs/fork_wait/`: one reference representation and two variants of each of two failure labels. The original concept library has six records across processes and scheduling. These counts describe a small demo corpus, not university textbook coverage.

Private university documents belong only in gitignored `data/private/` or `data/university/`. The build reads `data/demo/*.md` only. Linked references are not downloaded or copied into the repository.

## Knowledge pipeline

```text
UTF-8 Markdown → experiment heading → named section heading → section text
→ split only above 350 words → metadata and SHA-256 content hash
→ duplicate filter → 21 JSON records → BM25 / LSA representations
```

`oslab/knowledge.py` recognizes `# Experiment ID: Name` and known `##` section names. Record fields are `id`, `experiment_id`, `experiment_name`, `topic`, `section_type`, `source`, `page_section`, `language`, `content_hash`, and `text`. Duplicate filtering keys on experiment ID, section type and hash. Markdown extraction is currently strict: unknown section names fail rather than silently becoming arbitrary text. It does not process PDF, OCR or arbitrary lecture notes.

`results/demo_knowledge.json` is a tracked public snapshot. `data/processed/knowledge.json` is the ignored local working copy. `results/dataset_audit.json` adds source SHA-256 values, raw source text, detected section line numbers, record links, health counts and warnings. Its dataset fingerprint changes when a public source, C case or concept record changes; it is reproducible from the checked-in inputs.

## Behaviour pipeline

```text
reviewed C reference → controlled source variant → source diff
→ static features → expected event field → evidence record
→ interpretable case match → structured Debug result
```

Each case includes source, mutation description, failure label, static features, compiler/runtime/trace fields, normalized events, expected behaviour and evidence level. `results/demo_behaviour.json` is the tracked snapshot. The dataset audit adds diffs from the reference and displays expected, inferred and observed categories separately.

All committed case records currently say `static_only`: the reference is source reviewed but has not been compiled or traced on Linux in this environment. The optional `collect-trusted` command can capture actual results for fixed repository examples on Linux; its local output is not silently converted into the tracked static demo snapshot. No arbitrary student code is executed by the web app.

## Concept records

`data/concepts/*.json` holds original teaching summaries, claims, prerequisites, misconception IDs, linked instructional record IDs where applicable, references, and related simulator IDs. The loader checks unique IDs and valid prerequisites; the Dataset Studio audit flags unresolved instructional record links. Scheduling concepts currently have original summaries and reference links, but no lab retrieval records mapped to them. That is an explicit coverage gap.

## Quality controls and limitations

The labelled processing benchmark lists the expected experiment ID and heading line number for each of the 21 demo sections. Evaluation reports heading precision and recall, experiment ID accuracy, metadata completeness, duplicate count and unresolved concept links. Its perfect values apply only to three simple synthetic Markdown inputs. More meaningful extraction evaluation requires varied documents, rights-cleared inputs, and independent annotations. Behaviour evaluation requires more failure families and template-separated splits to avoid near-duplicate leakage.
