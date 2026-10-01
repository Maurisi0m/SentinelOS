import os
import secrets
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".sentinel"

def ensure_token() -> str:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token_file = CONFIG_DIR / "node_token.json"
    if token_file.exists():
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            if data.get("token"):
                return data["token"]
        except Exception:
            pass

    token = f"sentinel-{secrets.token_hex(16)}"
    token_file.write_text(json.dumps({"token": token, "created_at": os.times()[4]}), encoding="utf-8")
    return token

if __name__ == "__main__":
    print(ensure_token())
