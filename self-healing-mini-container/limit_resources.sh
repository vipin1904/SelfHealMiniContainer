#!/bin/bash
CONTAINER_PID=$1
CGROUP_NAME=mini_container

sudo mkdir -p /sys/fs/cgroup/$CGROUP_NAME

# Limit memory to 100MB
echo $((100*1024*1024)) | sudo tee /sys/fs/cgroup/$CGROUP_NAME/memory.max

# Limit CPU (50% usage)
echo 50000 | sudo tee /sys/fs/cgroup/$CGROUP_NAME/cpu.max

# Attach process to cgroup
echo $CONTAINER_PID | sudo tee /sys/fs/cgroup/$CGROUP_NAME/cgroup.procs
