import httpx

from app.core.config import get_settings

NO_ANSWER = "В документах нет ответа на этот вопрос"

SYSTEM_PROMPT = f"""Ты помощник, который отвечает на вопросы по документам компании.

Правила:
1. Используй только информацию из фрагментов. Не добавляй свои знания.
2. Ответь полным предложением, а в конце укажи номера фрагментов, на которые опираешься, в квадратных скобках.
3. Если во фрагментах нет ответа, даже если ты знаешь его сам, напиши ровно: {NO_ANSWER}
Без номеров фрагментов и без пояснений.

Пример ответа, когда ответ есть: Сотрудникам положено 28 календарных дней отпуска [1].
Пример ответа, когда ответа нет: {NO_ANSWER}"""


def build_user_message(question: str, fragments: list[str]) -> str:
    context = "\n".join(f"[{number}] {text}" for number, text in enumerate(fragments, start=1))
    return f"Фрагменты:\n{context}\n\nВопрос: {question}"


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
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{settings.OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
    return response.json()["message"]["content"].strip()
