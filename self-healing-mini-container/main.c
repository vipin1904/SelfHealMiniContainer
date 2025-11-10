#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <fcntl.h>

void setup_cgroup(pid_t pid) {
    const char *cg_base = "/sys/fs/cgroup";
    char cpu_path[256], mem_path[256], procs_file[256], buf[64];

    // CPU Cgroup
    snprintf(cpu_path, sizeof(cpu_path), "%s/mycontainer_cpu", cg_base);
    mkdir(cpu_path, 0755);
    int cpu_fd = open(strcat(strcpy(buf, cpu_path), "/cpu.max"), O_WRONLY | O_CREAT, 0644);
    if (cpu_fd >= 0) {
        write(cpu_fd, "50000 100000\n", 13); // 50% CPU
        close(cpu_fd);
    }

    // Memory Cgroup
    snprintf(mem_path, sizeof(mem_path), "%s/mycontainer_mem", cg_base);
    mkdir(mem_path, 0755);
    int mem_fd = open(strcat(strcpy(buf, mem_path), "/memory.max"), O_WRONLY | O_CREAT, 0644);
    if (mem_fd >= 0) {
        write(mem_fd, "104857600\n", 10); // 100MB
        close(mem_fd);
    }

    // Add process to both
    snprintf(procs_file, sizeof(procs_file), "%s/cgroup.procs", cpu_path);
    FILE *f1 = fopen(procs_file, "w");
    if (f1) { fprintf(f1, "%d", pid); fclose(f1); }

    snprintf(procs_file, sizeof(procs_file), "%s/cgroup.procs", mem_path);
    FILE *f2 = fopen(procs_file, "w");
    if (f2) { fprintf(f2, "%d", pid); fclose(f2); }

    printf("✅ Cgroups set: CPU=50%%, Memory=100MB\n");
}

int main(int argc, char *argv[]) {
    char *cmd = "/bin/sh"; // Default shell
    if (argc > 2 && strcmp(argv[1], "--cmd") == 0) {
        cmd = argv[2];
    }

    printf("🚀 Starting container with PID, UTS, Mount, and Network namespaces...\n");

    if (unshare(CLONE_NEWPID | CLONE_NEWUTS | CLONE_NEWNS | CLONE_NEWNET) == -1) {
        perror("unshare");
        return 1;
    }

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork failed");
        return 1;
    }

    if (pid == 0) {
        // Child = container process
        sethostname("mini-container", 13);
        printf("Inside container: PID=%d, hostname changed.\n", getpid());

        const char *rootfs = "/home/vipin/mini-container/rootfs";

        if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) == -1) {
            perror("Failed to make / private");
        }

        if (mount(rootfs, rootfs, "bind", MS_BIND | MS_REC, NULL) == -1) {
            perror("Bind mount failed");
        }

        if (chdir(rootfs) != 0) {
            perror("chdir failed");
            exit(1);
        }

        if (chroot(".") != 0) {
            perror("chroot failed");
            exit(1);
        }

        chdir("/");

        char *argv_exec[] = {"/bin/sh", "-c", cmd, NULL};
        execve("/bin/sh", argv_exec, NULL);
        perror("execve failed");
        exit(1);
    } else {
        // Parent = host
        setup_cgroup(pid);

        wait(NULL);
        printf("🧹 Cleaning up...\n");
        system("rmdir /sys/fs/cgroup/mycontainer_cpu");
        system("rmdir /sys/fs/cgroup/mycontainer_mem");
        printf("✅ Container process ended.\n");
    }

    return 0;
}
