/* Fixed fork/wait teaching fixture. The app reads this source for static
 * comparison; the browser never compiles or runs pasted student code. */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }
    if (pid == 0) { int status; waitpid(-1, &status, 0); puts("child finished"); return 0; }
    puts("parent complete");
    return 0;
}
