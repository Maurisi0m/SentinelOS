python3 - << 'EOF'
import urllib.request
import json
import time

def test(sys_msg, user_msg):
    t0 = time.time()
    payload = {
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.15,
        "max_tokens": 400,
        "cache_prompt": True,
        "stop": ["<|im_end|>", "<|endoftext|>"]
    }
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        t1 = time.time()
        print(f"\n=== PROMPT: '{user_msg}' ({t1-t0:.2f}s) ===")
        print(res["choices"][0]["message"]["content"])

sys_prompt = "Eres SENTINEL, mentor pedagogico del Laboratorio STEM. Enseñas ciencia, ingenieria y control de sistemas con rigor tecnico, formulas LaTeX y tablas Markdown. No uses emojis."

test(sys_prompt, "hola")
test(sys_prompt, "¿Que es SSH?")
EOF
