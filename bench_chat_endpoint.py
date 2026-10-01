import urllib.request
import json
import time

payload = {
    "messages": [
        {"role": "user", "content": "Que es la Ley de Ohm?"}
    ],
    "model": "sentinel:latest",
    "effort": "low",
    "enable_thinking": False,
    "enable_research": False
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8001/api/sentinel/chat', data=data, headers={'Content-Type': 'application/json'})

t0 = time.time()
ttft = None
chunks = 0

with urllib.request.urlopen(req) as resp:
    for chunk in resp:
        if chunk:
            chunks += 1
            if ttft is None:
                ttft = round(time.time() - t0, 3)
                print(f"Backend TTFT: {ttft} s")

total_time = round(time.time() - t0, 3)
print(f"Total Backend Time: {total_time} s, chunks: {chunks}")
