#!/usr/bin/env python3
"""
Self-Healing Agent
- Samples CPU/memory/network
- Predicts next-step trend (linear extrapolation)
- Exposes Prometheus metrics at /metrics
- Emits webhook events for actions and alerts

Requirements:
  pip install psutil prometheus_client requests flask
Environment:
  TARGET_PID - PID to manage (default 1)
  AGENT_WEBHOOK - optional webhook URL to notify control-plane
  ACTION_COOLDOWN - seconds (default 30)
  CPU_THRESHOLD - fractional (default 0.90)
  MEM_THRESHOLD - fractional (default 0.90)
  METRICS_PORT - prometheus HTTP port (default 9100)
"""

import os
import time
import threading
import signal
import psutil
import requests
import statistics
from prometheus_client import start_http_server, Gauge
from http.server import HTTPServer, BaseHTTPRequestHandler

# CONFIG via env / default
SAMPLE_INTERVAL = float(os.environ.get("SAMPLE_INTERVAL", "2.0"))
WINDOW_SIZE = int(os.environ.get("WINDOW_SIZE", "12"))
CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", "0.90"))
MEM_THRESHOLD = float(os.environ.get("MEM_THRESHOLD", "0.90"))
ACTION_COOLDOWN = float(os.environ.get("ACTION_COOLDOWN", "30"))
WEBHOOK = os.environ.get("AGENT_WEBHOOK", "")
TARGET_PID = int(os.environ.get("TARGET_PID", "1"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9100"))

# PROMETHEUS METRICS
g_cpu_current = Gauge('selfheal_cpu_frac', 'Current CPU fraction (0..1)')
g_mem_current = Gauge('selfheal_mem_frac', 'Current memory fraction (0..1)')
g_cpu_pred = Gauge('selfheal_cpu_pred_frac', 'Predicted CPU fraction (0..1)')
g_mem_pred = Gauge('selfheal_mem_pred_frac', 'Predicted mem fraction (0..1)')
g_actions_total = Gauge('selfheal_actions_total', 'Number of corrective actions executed')

class RollingWindow:
    def __init__(self, size):
        self.size = size
        self.buf = []

    def add(self, x):
        self.buf.append(x)
        if len(self.buf) > self.size:
            self.buf.pop(0)

    def values(self):
        return list(self.buf)

def post_event(payload):
    if not WEBHOOK:
        return
    try:
        requests.post(WEBHOOK, json=payload, timeout=3)
    except Exception:
        pass

def linear_predict(values):
    if len(values) < 2:
        return values[-1] if values else 0.0
    n = len(values)
    x = list(range(n))
    y = values
    x_mean = sum(x)/n
    y_mean = sum(y)/n
    num = sum((xi - x_mean)*(yi - y_mean) for xi, yi in zip(x,y))
    den = sum((xi - x_mean)**2 for xi in x)
    slope = 0 if den == 0 else (num / den)
    prediction = y[-1] + slope
    return max(0.0, prediction)

class Monitor:
    def __init__(self, interval=SAMPLE_INTERVAL, window=WINDOW_SIZE):
        self.interval = interval
        self.window = window
        self.cpu_w = RollingWindow(window)
        self.mem_w = RollingWindow(window)
        self.last_net = psutil.net_io_counters()
        self.net_w = RollingWindow(window)

    def sample(self):
        cpu = psutil.cpu_percent(interval=None) / 100.0
        vm = psutil.virtual_memory()
        mem = vm.used / vm.total if vm.total else 0.0
        net = psutil.net_io_counters()
        sent_per_s = (net.bytes_sent - self.last_net.bytes_sent) / max(self.interval, 1e-6)
        recv_per_s = (net.bytes_recv - self.last_net.bytes_recv) / max(self.interval, 1e-6)
        self.last_net = net

        self.cpu_w.add(cpu)
        self.mem_w.add(mem)
        self.net_w.add((sent_per_s + recv_per_s) / 2.0)

        g_cpu_current.set(cpu)
        g_mem_current.set(mem)
        return {"cpu": cpu, "mem": mem, "net": (sent_per_s + recv_per_s) / 2.0}

    def windows(self):
        return self.cpu_w.values(), self.mem_w.values(), self.net_w.values()

class Executor:
    def __init__(self):
        self.last_action_ts = 0
        self.actions_count = 0

    def cooldown_ok(self):
        return (time.time() - self.last_action_ts) >= ACTION_COOLDOWN

    def record_action(self, name, detail=None):
        self.last_action_ts = time.time()
        self.actions_count += 1
        g_actions_total.set(self.actions_count)
        post_event({"event": "action", "action": name, "detail": detail, "ts": time.time()})

    def throttle_nice(self, pid=TARGET_PID, inc=5):
        try:
            p = psutil.Process(pid)
            old = p.nice()
            p.nice(old + inc)
            self.record_action("throttle_nice", {"pid": pid, "old": old, "new": p.nice()})
            return True, f"nice {old}->{p.nice()}"
        except Exception as e:
            return False, str(e)

    def restart(self, pid=TARGET_PID, graceful_timeout=5):
        try:
            p = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return False, "no process"
        try:
            p.send_signal(signal.SIGTERM)
            gone, alive = psutil.wait_procs([p], timeout=graceful_timeout)
            if alive:
                for a in alive:
                    a.kill()
            self.record_action("restart", {"pid": pid})
            return True, "restarted"
        except Exception as e:
            return False, str(e)

class Agent:
    def __init__(self):
        self.monitor = Monitor()
        self.exec = Executor()
        self.running = True

    def evaluate(self):
        cpu_vals, mem_vals, _ = self.monitor.windows()
        cpu_pred = linear_predict(cpu_vals)
        mem_pred = linear_predict(mem_vals)

        g_cpu_pred.set(cpu_pred)
        g_mem_pred.set(mem_pred)

        post_event({"event":"metrics_snapshot", "cpu_vals": cpu_vals, "mem_vals": mem_vals, "cpu_pred": cpu_pred, "mem_pred": mem_pred, "ts": time.time()})

        actions = []
        if self.exec.cooldown_ok():
            if cpu_pred >= CPU_THRESHOLD:
                ok, msg = self.exec.throttle_nice()
                actions.append(("cpu_throttle_nice", ok, msg))
            if mem_pred >= MEM_THRESHOLD:
                ok, msg = self.exec.restart()
                actions.append(("restart_for_mem", ok, msg))
            if actions:
                return actions
        else:
            post_event({"event":"cooldown", "since": time.time() - self.exec.last_action_ts})
        return []

    def run(self):
        # start prometheus metrics server
        start_http_server(METRICS_PORT)

        def sampler():
            while self.running:
                sample = self.monitor.sample()
                print(f"[monitor] cpu={sample['cpu']:.3f} mem={sample['mem']:.3f} net={sample['net']:.1f}")
                time.sleep(self.monitor.interval)

        t = threading.Thread(target=sampler, daemon=True)
        t.start()

        try:
            while True:
                time.sleep(self.monitor.interval)
                acts = self.evaluate()
                if acts:
                    print(f"[agent] actions={acts}")
        except KeyboardInterrupt:
            self.running = False
            print("Agent stopped")

if __name__ == "__main__":
    Agent().run()
