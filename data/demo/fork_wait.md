# Experiment FW01: Process Creation with fork and wait
## Aim
Create a child process and synchronize the parent with its completion.
## Theory
fork creates a child process. The return value is zero in the child and positive in the parent. Process scheduling is nondeterministic. wait or waitpid blocks the parent until a child terminates and reaps it.
## Procedure
Call fork, check failure, run child work in the child branch, call waitpid in the parent branch, and print completion after the wait returns.
## Program
The parent branch calls waitpid(child_pid, &status, 0). The child branch exits after its work. Check fork return values and waitpid errors.
## Expected Output
Child work finishes before the parent prints its completion message. Exact process IDs and scheduling order of earlier messages may vary.
## Troubleshooting
If the parent prints completion before the child finishes, inspect the parent branch for a missing wait or waitpid call. A wait in the child branch does not synchronize the parent.
## Viva
Why is output order without wait nondeterministic? What does waitpid return? What is a zombie process?
