Self-Healing Mini Container (Demo + Runtime Integration)
=======================================================

This project demonstrates Self-Healing Containers:

- A normal container runs an app and fails when the app leaks memory, hogs CPU, or hangs.
- A self-healing container runs the same app plus a tiny agent inside the container that detects the problem and restarts the app automatically.
- The same pattern can be integrated into our mini container runtime.

------------------------------------------------------------
What is a Self-Healing Container?
------------------------------------------------------------
A self-healing container monitors the application process inside it and automatically recovers from failures.

Architecture Diagram
------------------------------------------------------------
+--------------------------------------------------------+
|                    Self-Healing Container              |
|                                                        |
|   +-------------------+     +----------------------+   |
|   |   Application     |<--->|   Monitoring Agent   |   |
|   |   (app.py)        |     |   (agent.py)         |   |
|   +-------------------+     +----------------------+   |
|            ^                           |               |
|            | (restart if unhealthy)     | monitors      |
+--------------------------------------------------------+
                 Container Runtime / Docker

The monitoring agent:
- Tracks the app's PID
- Checks memory, CPU, and responsiveness
- Restarts the app when misbehavior is detected

------------------------------------------------------------
System Requirements
------------------------------------------------------------
- Linux (Ubuntu/Kali/WSL) or macOS
- Docker installed
- 4GB RAM recommended

------------------------------------------------------------
Build Images
------------------------------------------------------------
cd self_heal_demo

docker build -t normal-demo -f Dockerfile.normal .
docker build -t selfheal-demo -f Dockerfile.selfheal .

------------------------------------------------------------
Run Test Scenarios
------------------------------------------------------------

Memory Leak Test:
docker run -it --rm -e MODE=MEM normal-demo
docker run -it --rm -e MODE=MEM selfheal-demo

High CPU Test:
docker run -it --rm -e MODE=CPU normal-demo
docker run -it --rm -e MODE=CPU selfheal-demo

App Hang Test:
docker run -it --rm -e MODE=HANG normal-demo
docker run -it --rm -e MODE=HANG selfheal-demo

------------------------------------------------------------
Internal Working Logic
------------------------------------------------------------
entrypoint.sh:
- start app -> store PID -> run agent

agent.py:
- monitor PID -> detect high resource usage or hang -> restart app

------------------------------------------------------------
Troubleshooting
------------------------------------------------------------
entrypoint.sh permission issue:
chmod +x entrypoint.sh

Docker permission issue:
sudo usermod -aG docker $USER

------------------------------------------------------------
Cheat-Sheet
------------------------------------------------------------
cd self_heal_demo2
docker build -t normal-demo -f Dockerfile.normal .
docker build -t selfheal-demo -f Dockerfile.selfheal .
