buf = []
step = 10  # MB leak each time

print("Leaky App Running...")

while True:
    buf.append(bytearray(step * 1024 * 1024))  # leak memory
    print("Leaked +10MB")
