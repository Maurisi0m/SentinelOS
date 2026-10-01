import json

with open("dataset/ultimate_sentinel_dataset.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total samples: {len(lines)}")

first = json.loads(lines[0])
msgs = first.get("messages", [])
print("\n--- Primera muestra ---")
for m in msgs:
    print(f"[{m['role']}]: {str(m['content'])[:150]}")

last = json.loads(lines[-1])
msgs2 = last.get("messages", [])
print("\n--- Ultima muestra ---")
for m in msgs2:
    print(f"[{m['role']}]: {str(m['content'])[:150]}")
