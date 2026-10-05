# Experiment EX01: Program Replacement with exec
## Aim
Replace a child process image with another program.
## Theory
A successful exec call does not return. The process ID stays the same while its program image changes.
## Procedure
Call fork. In the child, call execlp with a valid executable and arguments. Handle the error path only if exec returns. The parent waits.
## Program
The child calls execlp("echo", "echo", "hello", (char *)NULL); perror follows only on failure.
## Expected Output
The replacement program prints hello. A successful exec does not execute statements following the call.
## Troubleshooting
If code after exec runs, check the executable path and arguments; exec may have failed. Always inspect perror and the return path.
## Viva
Does exec create a new process? What happens to the process ID after exec?
