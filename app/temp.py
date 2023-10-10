from log import test

for s in ['comp', 'loop', 'chunk']:
    times = []
    for i in range(5):
        times.append(test(s))
    print(f"Time for {s}: {sum(times)/len(times)}")