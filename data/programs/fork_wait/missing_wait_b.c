#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
int main(void) {
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }
    switch (pid) {
      case 0: sleep(1); puts("child finished"); return 0;
      default: puts("parent complete"); return 0;
    }
}
