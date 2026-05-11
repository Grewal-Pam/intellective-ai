from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen


def post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        return json.load(resp)


def main():
    host = "http://127.0.0.1:8700"
    prompt = "Say hello and identify yourself."
    body = {"prompt": prompt}
    print("Posting to MCP shim generate...")
    resp = post(f"{host}/mcp/generate", body)
    print(json.dumps(resp, indent=2))


if __name__ == "__main__":
    sys.exit(main())
