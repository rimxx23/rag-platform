import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from evals import run_evals


def test_reports_answer_citation_and_refusal_metrics(monkeypatch, capsys):
    fragments = ["Отпуск составляет 28 календарных дней.", "Офис открывается в 10:00."]
    index = SimpleNamespace(search=lambda question, limit: fragments)
    questions = [
        {"question": "Сколько дней отпуска?", "expected": "28 календарных дней"},
        {"question": "Во сколько открывается офис?", "expected": "10:00"},
        {"question": "Когда начинается отпуск?", "expected": None},
        {"question": "Есть ли парковка?", "expected": None},
        {"question": "Чему равна продолжительность отпуска?", "expected": "28 календарных дней"},
        {"question": "На сколько дней дают отпуск?", "expected": "28 календарных дней"},
        {"question": "Какая зарплата?", "expected": None},
    ]
    answers = [
        "Отпуск составляет 28 календарных дней [1].",
        "В 10:00 [1].",
        "В июле [9].",
        "Да [2].",
        "28 календарных дней.",
        f"{run_evals.NO_ANSWER} [9]",
        run_evals.NO_ANSWER,
    ]
    monkeypatch.setattr(run_evals, "generate_answer", AsyncMock(side_effect=answers))

    asyncio.run(run_evals.evaluate_answers(index, questions))

    report = capsys.readouterr().out
    assert "Ответы с эталонной фразой: 3/4" in report
    assert "Цитаты с эталонным фрагментом: 1/4" in report
    assert "Правильные отказы: 1/3" in report
    assert "Ложные отказы:     1/4" in report
    assert "Ответы без ссылок: 1/7" in report
    assert "Ответы с номером ссылки вне диапазона: 1/7" in report
