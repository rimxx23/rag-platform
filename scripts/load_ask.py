import argparse
import asyncio
import os
import time
from collections import Counter
from getpass import getpass
from statistics import median

import httpx


async def run(args: argparse.Namespace, token: str) -> None:
    async with httpx.AsyncClient(
        base_url=args.url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=90,
        trust_env=False,
    ) as api:
        async def ask() -> tuple[int, float, str | None]:
            start = time.perf_counter()
            response = await api.post(
                f"/collections/{args.collection_id}/ask", json={"question": args.question}
            )
            duration = time.perf_counter() - start
            retry_after = response.headers.get("Retry-After")
            return response.status_code, duration, retry_after

        results = await asyncio.gather(*(ask() for _ in range(args.requests)))

    codes = Counter(code for code, _, _ in results)
    print(f"Статусы: {dict(sorted(codes.items()))}")
    for code in sorted(codes):
        elapsed = [duration for status, duration, _ in results if status == code]
        print(f"HTTP {code}: медиана {median(elapsed):.3f} с, максимум {max(elapsed):.3f} с")
    retries = {retry for code, _, retry in results if code == 429}
    if retries:
        print(f"Retry-After: {', '.join(sorted(value for value in retries if value))} с")
    if (
        any(code not in (200, 429) for code in codes)
        or None in retries
        or (args.expected_ok is not None and codes[200] != args.expected_ok)
    ):
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a bounded burst to a test RAG collection.")
    parser.add_argument("collection_id")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, choices=range(1, 21), default=12, metavar="1–20")
    parser.add_argument("--expected-ok", type=int)
    parser.add_argument("--question", default="По какому пути доступен Swagger UI?")
    args = parser.parse_args()
    asyncio.run(run(args, os.environ.get("RAG_LOAD_TOKEN") or getpass("JWT: ")))


if __name__ == "__main__":
    main()
