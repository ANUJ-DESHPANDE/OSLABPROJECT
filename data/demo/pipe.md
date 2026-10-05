# Experiment PI01: Parent-child communication with pipe
## Aim
Send a message from parent to child through a pipe.
## Theory
pipe creates a read end and a write end. Unused ends should be closed in each process. A reader sees EOF only after all write ends close.
## Procedure
Create the pipe before fork. The child closes the write end and reads. The parent closes the read end, writes a message, closes the write end, and waits.
## Program
Use pipe(fd), fork(), close(fd[1]) in the child, close(fd[0]) in the parent, read and write the corresponding ends.
## Expected Output
The child receives the bytes written by the parent and exits; the parent reaps the child.
## Troubleshooting
If a read waits forever, verify every process closes its unused write end. If read fails, verify the child uses fd[0].
## Viva
What does read return at EOF? Why close unused pipe ends?
