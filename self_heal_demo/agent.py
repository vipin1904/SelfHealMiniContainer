#!/usr/bin/env python3
import psutil, time, os, signal

print("Self-Healing Agent Started")

def get_pid():
    while True:
        try:
            with open("/app/app.pid") as f:
                return int(f.read().strip())
        except:
            time.sleep(0.5)

while True:
    pid = get_pid()
    try:
        p = psutil.Process(pid)
    except:
        time.sleep(1)
        continue

    mem = p.memory_percent()
    cpu = p.cpu_percent(interval=1) / 100

    print(f"Memory: {mem:.1f}%, CPU: {cpu:.1f}")

    if mem > 30:
        print("High Memory! Restarting...")
        p.send_signal(signal.SIGTERM)
        time.sleep(2)
        continue

    if cpu > 0.80:
        print("High CPU! Restarting...")
        p.send_signal(signal.SIGTERM)
        time.sleep(2)
        continue

    if cpu == 0 and mem < 5:
        print("App Hung! Restarting...")
        p.send_signal(signal.SIGTERM)
        time.sleep(2)
        continue
