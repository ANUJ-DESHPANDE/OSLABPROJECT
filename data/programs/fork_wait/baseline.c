#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    pid_t child = fork();
    if (child < 0) { perror("fork"); return 1; }
    if (child == 0) { puts("child finished"); fflush(stdout); _exit(0); }
    int status;
    if (waitpid(child, &status, 0) < 0) { perror("waitpid"); return 1; }
    puts("parent complete");
    return 0;
}
