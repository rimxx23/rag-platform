import asyncio
import json
import time
from pathlib import Path

import numpy as np

from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.llm import NO_ANSWER, generate_answer

EVALS_DIR = Path(__file__).parent
CHUNK_SIZES = [300, 150, 100, 60, 40]
TOP_K = [1, 3, 5]
ANSWER_CHUNK_SIZE = 60
ANSWER_TOP_K = 5


class Index:
    def __init__(self, text: str, size: int) -> None:
        self.chunks = chunk_text(text, size=size, overlap=size // 5)
        self.vectors = np.array(embed_texts(self.chunks))

    def search(self, question: str, limit: int) -> list[str]:
        question_vector = np.array(embed_texts([question])[0])
        distances = np.linalg.norm(self.vectors - question_vector, axis=1)
        return [self.chunks[i] for i in np.argsort(distances)[:limit]]


def is_hit(found_chunks: list[str], expected: str) -> bool:
    return any(expected in chunk for chunk in found_chunks)


def evaluate_retrieval(index: Index, questions: list[dict]) -> tuple[dict[int, float], list[str]]:
    answerable = [q for q in questions if q["expected"] is not None]
    hits = {k: 0 for k in TOP_K}
    misses = []
    for q in answerable:
        found = index.search(q["question"], max(TOP_K))
        for k in TOP_K:
            if is_hit(found[:k], q["expected"]):
                hits[k] += 1
        if not is_hit(found[:1], q["expected"]):
            misses.append(q["question"])
    return {k: hits[k] / len(answerable) for k in TOP_K}, misses


async def evaluate_answers(index: Index, questions: list[dict]) -> None:
    correct_refusals = 0
    false_refusals = 0
    failures = []
    latencies = []

    for q in questions:
        start = time.perf_counter()
        answer = await generate_answer(q["question"], index.search(q["question"], ANSWER_TOP_K))
        latencies.append(time.perf_counter() - start)

        refused = answer.startswith(NO_ANSWER)
        should_refuse = q["expected"] is None
        if should_refuse and refused:
            correct_refusals += 1
        elif refused:
            false_refusals += 1
            failures.append(f"ложный отказ: {q['question']}")
        elif should_refuse:
            failures.append(f"выдумал: {q['question']} → {answer}")

    no_answer = sum(1 for q in questions if q["expected"] is None)
    print(f"Правильные отказы: {correct_refusals}/{no_answer}")
    print(f"Ложные отказы:     {false_refusals}/{len(questions) - no_answer}")
    print(f"Среднее время:     {sum(latencies) / len(latencies):.2f} с")
    for failure in failures:
        print(f"  ✗ {failure}")


async def main() -> None:
    text = (EVALS_DIR / "docs" / "handbook.md").read_text(encoding="utf-8")
    questions = json.loads((EVALS_DIR / "questions.json").read_text(encoding="utf-8"))

    print("=== Поиск ===")
    print(f"{'размер':>6} {'чанков':>6} " + " ".join(f"hit@{k:<3}" for k in TOP_K))
    indexes = {}
    for size in CHUNK_SIZES:
        indexes[size] = Index(text, size)
        scores, misses = evaluate_retrieval(indexes[size], questions)
        print(f"{size:>6} {len(indexes[size].chunks):>6} " + " ".join(f"{scores[k]:>6.0%}" for k in TOP_K))
        if size == ANSWER_CHUNK_SIZE:
            answer_misses = misses

    print(f"\nНе на первом месте при размере {ANSWER_CHUNK_SIZE}:")
    for question in answer_misses or ["—"]:
        print(f"  ✗ {question}")

    print(f"\n=== Ответы (размер {ANSWER_CHUNK_SIZE}, top-{ANSWER_TOP_K}) ===")
    await evaluate_answers(indexes[ANSWER_CHUNK_SIZE], questions)


if __name__ == "__main__":
    asyncio.run(main())
