#!/usr/bin/env python3
"""
Eval harness for the News Knowledge Base Query workflow.

Hits the live search-news webhook with a fixed set of queries and checks
that the expected company/story shows up in the ranked results (retrieval
quality), plus one negative case (a query with no matches should report
zero results, not error or hang).

Usage:
    WEBHOOK_URL=https://<your-n8n-domain>/webhook/search-news python3 eval_search.py
"""

import json
import os
import sys
import urllib.request

WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL", "https://htj2.app.n8n.cloud/webhook/search-news"
)

# (query, substring expected somewhere in the results, human label)
CASES = [
    ("Glow", "Glow", "stealth endpoint-security launch"),
    ("Anthropic", "AMD", "AMD's $5B Anthropic infrastructure deal"),
    ("Hugging Face", "OpenAI", "OpenAI/Hugging Face security incident"),
    ("Chinese models", "Arcee", "China open-source models coverage"),
    ("raise", "Passionfroot", "funding-round articles"),
    ("zzz_nonexistent_query_12345", None, "no-match query returns 0, not an error"),
]


def call(query: str) -> dict:
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        WEBHOOK_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode()
    if not raw:
        return {}
    return json.loads(raw)


def run() -> int:
    passed = 0
    failed = 0

    for query, expect, label in CASES:
        try:
            result = call(query)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  [{label}] query={query!r} -> request error: {exc}")
            failed += 1
            continue

        results_text = result.get("results", "")
        count = result.get("count")

        if expect is None:
            ok = count == 0 and "No matching articles found" in results_text
        else:
            ok = expect in results_text

        status = "PASS" if ok else "FAIL"
        print(f"{status}  [{label}] query={query!r} count={count}")
        if not ok:
            print(f"      expected {expect!r} in results, got: {results_text[:200]}")

        passed += ok
        failed += not ok

    total = passed + failed
    print(f"\n{passed}/{total} cases passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
