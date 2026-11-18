import re

import httpx

from app.core.config import get_settings

NO_ANSWER = "В документах нет ответа на этот вопрос"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class LLMUnavailableError(Exception):
    pass


SYSTEM_PROMPT = f"""Ты помощник, который отвечает на вопросы по документам компании.

Правила:
1. Используй только информацию из фрагментов. Не добавляй свои знания.
2. Вопрос может быть задан другими словами, чем во фрагментах: например, «зарплата» и «оклад» означают одно и то же. Если ответ прямо следует из фрагментов, ответь.
3. Ответь полным предложением, а в конце укажи номера фрагментов, на которые опираешься, в квадратных скобках.
4. Если во фрагментах нет ответа, даже если ты знаешь его сам, напиши ровно: {NO_ANSWER}
Без номеров фрагментов и без пояснений.

Пример ответа, когда ответ есть: Сотрудникам положено 28 календарных дней отпуска [1].
Пример ответа, когда ответа нет: {NO_ANSWER}"""


def build_user_message(question: str, fragments: list[str]) -> str:
    context = "\n".join(f"[{number}] {text}" for number, text in enumerate(fragments, start=1))
    allowed_citations = ", ".join(f"[{number}]" for number in range(1, len(fragments) + 1))
    return (
        f"Фрагменты:\n{context}\n\n"
        f"Вопрос: {question}\n"
        f"Если цитируешь фрагменты, используй только эти ссылки: {allowed_citations or 'нет доступных ссылок'}."
    )


async def generate_answer(question: str, fragments: list[str]) -> str:
    settings = get_settings()
    payload = {
        "model": settings.LLM_MODEL,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(question, fragments)},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{settings.OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMUnavailableError("LLM is unavailable") from e
    return response.json()["message"]["content"].strip()


def extract_citations(answer: str, count: int) -> list[int]:
    result = []
    for match in CITATION_PATTERN.findall(answer):
        number = int(match)
        if 1 <= number <= count and number not in result:
            result.append(number)
    return result
