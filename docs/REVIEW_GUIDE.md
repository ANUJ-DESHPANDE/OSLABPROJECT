# In-person review guide

## Say this first (30 seconds)

“This is a local Operating Systems study companion. I imported our course archive and extracted searchable passages from PDFs, slides, and documents, keeping the original file and page or slide. Search combines keyword ranking and statistical concept similarity. A small local model turns the retrieved evidence into a plain-language explanation and a visual walkthrough for the exact question. There is also a static lab-code reviewer and a deterministic CPU scheduling simulator.”

## Show it in four moves

1. **Ask OS:** search `Why does a page fault happen?` Point at a citation and open its source excerpt. Then step through the generated visual. Say that each step is an explanatory model grounded in a displayed passage.
2. **Review lab code:** use the pipe example or paste your own C/shell code. Show a specific source clue, the related course passage, and a code-line-aware visual step if one was generated. State clearly that the code was not run.
3. **Scheduling lab:** run the sample workload, change Round Robin quantum, and compare the Gantt timeline and waiting time. These results are calculated by project code, not guessed by the model.
4. **How the data works:** show the local archive processing counts: 33 searchable documents, 553 passages, 21 skipped entries. Explain the skip reasons and provenance. Point out the 21 separately labeled original project lab notes used alongside course passages.

## The data story

`OS.zip` → safe in-memory archive reading → PDF page / PPTX slide / DOCX text extraction → Unicode cleanup and passage chunks → local JSON index with file hash and page/slide → BM25 and LSA rankings → hybrid rank fusion → top cited passages → optional local explanation and visual.

There is also a separate small, public synthetic lab dataset: structured Markdown teaching records and reviewed C variants with labeled source-based failure cases. Its existing benchmark does **not** measure the private course archive. The static checker recognizes selected OS APIs and suspicious patterns; it is broader than the original fork/wait prototype but is still not general proof of correctness.

| If asked | Short answer |
|---|---|
| “Is this RAG?” | “Yes. It retrieves relevant local course passages and supplies them to a local generator. The page/slide citations and raw excerpts remain available for checking.” |
| “Is it just an LLM wrapper?” | “The importer, index, BM25, LSA, hybrid ranking, static code checks, and scheduling simulator are our own pipeline. The model only explains selected evidence and creates a question-specific teaching view.” |
| “Are the visual steps a real execution trace?” | “No. They illustrate the likely mechanism. Scheduling has its own deterministic simulation; pasted student code is never executed.” |
| “What are the limits?” | “Legacy slides and scanned images are skipped, there is no labeled relevance score on our course archive, and the model or static analysis may miss or misstate a bug.” |
| “Why keep fork/wait?” | “It is a common OS lab topic with a deeper process walkthrough, but it appears only when the question or code needs it.” |

## Start it on this laptop

In PowerShell in the project folder:

```powershell
python -m oslab serve --port 8001
```

Open <http://127.0.0.1:8001> and leave that terminal running. Start the local model server too if the app says the model is unavailable. If port 8001 is busy, choose another port and open that URL.

On this laptop, start the local model in a second PowerShell window with `powershell -ExecutionPolicy Bypass -File .\start_model.ps1`. Leave both windows open for the demo.
