import time

print("This app will leak memory and eventually crash...")
data = []

while True:
    data.append("X" * 10_000_000)  # adds 10MB every loop
    print("Leaked +10MB")
    time.sleep(1)
