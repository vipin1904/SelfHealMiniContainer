# 🐧 Mini Container in C

A lightweight container runtime built **from scratch in C** using **Linux namespaces**, **cgroups**, and **BusyBox**.  
This project replicates the core ideas behind **Docker**, showing how containers isolate processes, filesystems, and resources at a low level.

---

## 🚀 Features

- **PID Namespace** → Process isolation (your container starts with PID 1)
- **UTS Namespace** → Custom hostname inside the container
- **Mount Namespace** → Isolated filesystem using `chroot`
- **Cgroups** → CPU and Memory limits
- **Network Namespace (optional)** → Virtual network isolation
- **BusyBox Integration** → Minimal Linux environment with shell commands
- **Clean Exit Handling** → Proper cleanup after container termination

---

## 🧱 Project Structure

mini-container/
├── main.c # Core container implementation
├── container.out # Compiled executable (ignored in .gitignore)
├── rootfs/ # Root filesystem (BusyBox installed here)
├── .gitignore
└── README.md



---

## ⚙️ Setup Instructions

### 1️⃣ Prerequisites
Make sure you have the following installed:
```bash
sudo apt update
sudo apt install gcc busybox
Prepare Root Filesystem

## Clone the Repository

git clone https://github.com/<your-username>/mini-container.git
cd mini-container

Prepare Root Filesystem

We’ll use BusyBox to create a minimal root filesystem:

sudo rm -rf rootfs
mkdir rootfs
cd rootfs
sudo busybox --install -s .
cd ..
This installs basic commands like /bin/sh, /bin/ls, etc. inside rootfs/.

Compile and Run

Compile:

sudo ./container.out
You’ll drop into a shell inside your container:

🚀 Starting container with PID, UTS, Mount, and Network namespaces...
Inside container: PID=1, hostname changed.

BusyBox v1.37.0 (Debian) built-in shell (ash)
Enter 'help' for a list of built-in commands.

/ #
Exit the container:

/ # exit
✅ Container process ended.
