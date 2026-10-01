import urllib.request
import json
import time

payload = {
    "messages": [
        {"role": "system", "content": "Eres SENTINEL, mentor de ciencias y STEM. Responde de forma concisa."},
        {"role": "user", "content": "Que es la Ley de Ohm?"}
    ],
    "stream": True,
    "max_tokens": 100
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions', data=data, headers={'Content-Type': 'application/json'})

t0 = time.time()
ttft = None
tokens = 0

with urllib.request.urlopen(req) as resp:
    for line in resp:
        line_str = line.decode('utf-8', errors='ignore').strip()
        if line_str.startswith('data: ') and line_str != 'data: [DONE]':
            try:
                chunk = json.loads(line_str[6:])
                content = chunk['choices'][0]['delta'].get('content', '')
                if content:
                    tokens += 1
                    if ttft is None:
                        ttft = round(time.time() - t0, 3)
                        print(f"Time to First Token (TTFT): {ttft} s")
            except:
                pass

total_time = round(time.time() - t0, 3)
gen_time = round(total_time - (ttft or 0), 3)
speed = round(tokens / gen_time, 2) if gen_time > 0 else 0
print(f"Total time: {total_time}s | Gen time: {gen_time}s | Tokens: {tokens} | Gen Speed: {speed} tok/s")
