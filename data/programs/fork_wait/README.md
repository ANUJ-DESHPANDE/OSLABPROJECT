# Five controlled fork/wait C examples

These are **fixed test cases**, not submissions from students and not code run by the web app. They have little inline prose because the benchmark compares their source text and differences directly.

| File | Deliberate behavior to inspect |
|---|---|
| `baseline.c` | Parent calls `waitpid()` before printing its completion message. |
| `missing_wait_a.c` | Parent omits the wait and may finish before the child. |
| `missing_wait_b.c` | The same missing-wait issue written with a `switch`. |
| `wait_in_child_a.c` | `wait()` is placed in the child; it does not make the parent wait. |
| `wait_in_child_b.c` | Similar child-side `waitpid()` variant. |

`oslab/behaviour.py` reads these files and records **static source features**. In the committed Windows demo, compiler output, runtime output and syscall traces remain empty because these examples were not run under Linux for the published dataset.
