import asyncio
import json
import re
import time
from pathlib import Path

import numpy as np

from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.llm import CITATION_PATTERN, NO_ANSWER, extract_citations, generate_answer

EVALS_DIR = Path(__file__).parent
CHUNK_SIZES = [300, 150, 100, 60, 40]
TOP_K = [1, 3, 5]
ANSWER_CHUNK_SIZE = 300
ANSWER_TOP_K = 5


class Index:
    def __init__(self, text: str, size: int) -> None:
        overlap = 50 if size == 300 else size // 5
        self.chunks = chunk_text(text, size=size, overlap=overlap)
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


def contains_expected(text: str, expected: str) -> bool:
    def words(value: str) -> list[str]:
        return re.findall(r"\w+", value.casefold().replace("ё", "е"))

    answer_words = words(text)
    expected_words = words(expected)
    length = len(expected_words)
    return any(
        answer_words[start:start + length] == expected_words
        for start in range(len(answer_words) - length + 1)
    )


async def evaluate_answers(index: Index, questions: list[dict]) -> None:
    correct_answers = 0
    correct_citations = 0
    correct_refusals = 0
    false_refusals = 0
    missing_citations = 0
    invalid_citations = 0
    failures = []
    latencies = []

    for q in questions:
        question = q["question"]
        expected = q["expected"]
        start = time.perf_counter()
        fragments = index.search(question, ANSWER_TOP_K)
        answer = await generate_answer(question, fragments)
        latencies.append(time.perf_counter() - start)

        refused = answer.startswith(NO_ANSWER)
        if not refused:
            references = CITATION_PATTERN.findall(answer)
            if not references:
                missing_citations += 1
                failures.append(f"ответ без ссылок: {question} → {answer}")
            elif any(not 1 <= int(number) <= len(fragments) for number in references):
                invalid_citations += 1
                failures.append(f"номер ссылки вне диапазона: {question} → {answer}")
            elif expected is not None:
                citations = extract_citations(answer, len(fragments))
                if any(contains_expected(fragments[n - 1], expected) for n in citations):
                    correct_citations += 1
                else:
                    failures.append(f"цитаты не содержат эталонный фрагмент: {question} → {answer}")

        if expected is None:
            if refused:
                correct_refusals += 1
            else:
                failures.append(f"ответ без эталона: {question} → {answer}")
            continue
        if refused:
            false_refusals += 1
            failures.append(f"ложный отказ: {question} → {answer!r}")
            continue

        answer_text = CITATION_PATTERN.sub("", answer)
        if any(contains_expected(answer_text, variant) for variant in q.get("answers", [expected])):
            correct_answers += 1
        else:
            failures.append(f"ответ не совпал с эталоном: {question} → {answer}")

    no_answer = sum(1 for q in questions if q["expected"] is None)
    answerable = len(questions) - no_answer
    print(f"Ответы с эталонной фразой: {correct_answers}/{answerable}")
    print(f"Цитаты с эталонным фрагментом: {correct_citations}/{answerable}")
    print(f"Правильные отказы: {correct_refusals}/{no_answer}")
    print(f"Ложные отказы:     {false_refusals}/{answerable}")
    print(f"Ответы без ссылок: {missing_citations}/{len(questions)}")
    print(f"Ответы с номером ссылки вне диапазона: {invalid_citations}/{len(questions)}")
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
