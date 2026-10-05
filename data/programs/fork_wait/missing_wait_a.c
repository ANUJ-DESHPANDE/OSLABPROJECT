#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
int main(void) {
    pid_t child = fork();
    if (child < 0) { perror("fork"); return 1; }
    if (child == 0) { sleep(1); puts("child finished"); return 0; }
    puts("parent complete");
    return 0;
}
