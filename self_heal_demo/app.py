import os, time

mode = os.environ.get("MODE", "MEM").upper()

print(f"App running in mode: {mode}")

if mode == "MEM":
    data = []
    while True:
        data.append("X" * 10_000_000)   # leak 10MB each loop
        print("Leaked +10MB")
        time.sleep(1)

elif mode == "CPU":
    print("This app will use high CPU...")
    while True:
        x = 999999**999999

elif mode == "HANG":
    print("App will run for 5 seconds then hang...")
    time.sleep(5)
    print("Hanging now...")
    while True:
        pass
