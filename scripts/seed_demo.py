import argparse
import os
import time
from getpass import getpass
from pathlib import Path

import httpx


def seed_collection(api: httpx.Client, document_path: Path) -> str:
    collection = api.post("/collections", json={"name": document_path.stem})
    collection.raise_for_status()
    collection_id = collection.json()["id"]
    documents_url = f"/collections/{collection_id}/documents"
    with document_path.open("rb") as document:
        upload = api.post(
            documents_url, files={"file": (document_path.name, document, "text/markdown")}
        )
    upload.raise_for_status()
    document_id = upload.json()["id"]
    print(f"Коллекция {collection_id}. Ждём индексацию документа…", flush=True)

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        response = api.get(documents_url)
        response.raise_for_status()
        document = next(item for item in response.json() if item["id"] == document_id)
        if document["status"] == "ready":
            return collection_id
        if document["status"] == "failed":
            raise SystemExit(f"Обработка не удалась: {document['error']}")
        time.sleep(2)
    raise SystemExit("Документ ещё обрабатывается. Его статус можно проверить в веб-чате.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("document", type=Path, help="Path to a Markdown file")
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()
    if not args.document.is_file():
        parser.error(f"File not found: {args.document}")
    password = os.getenv("RAG_DEMO_PASSWORD") or getpass("Пароль: ")
    with httpx.Client(base_url=args.url, timeout=20, trust_env=False) as api:
        login = api.post("/auth/login", data={"username": args.username, "password": password})
        login.raise_for_status()
        api.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        seed_collection(api, args.document)
    print("Коллекция готова. Задайте вопрос по загруженному документу.")


if __name__ == "__main__":
    main()
