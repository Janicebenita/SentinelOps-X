from pathlib import Path
import httpx
print(httpx.post("http://localhost:8000/api/demo/reset", timeout=10).json())
for folder in ("logs", "metrics", "traces"):
    for path in Path("data", folder).glob("*.jsonl"):
        path.unlink()
