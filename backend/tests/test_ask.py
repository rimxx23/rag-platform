import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import ask
from app.services.llm import NO_ANSWER


@pytest.mark.parametrize(
    ("model_answer", "expected_answer", "expected_numbers"),
    [
        ("Отпуск длится 28 дней.", NO_ANSWER, []),
        ("Отпуск длится 28 дней [2].", NO_ANSWER, []),
        ("Отпуск длится 28 дней [1].", "Отпуск длится 28 дней [1].", [1]),
    ],
)
def test_answer_requires_a_valid_citation(
    monkeypatch, model_answer, expected_answer, expected_numbers
):
    chunk = SimpleNamespace(
        document_id="document-1",
        document=SimpleNamespace(filename="handbook.pdf"),
        page=3,
        content="Ежегодный отпуск длится 28 дней.",
    )
    repository = SimpleNamespace(search=AsyncMock(return_value=[chunk]))
    monkeypatch.setattr(ask, "embed_texts", lambda texts: [[0.5]])
    monkeypatch.setattr(ask, "generate_answer", AsyncMock(return_value=model_answer))

    result = asyncio.run(ask.answer_question(repository, "collection-1", "Сколько дней отпуска?"))

    assert result.answer == expected_answer
    assert [source.number for source in result.sources] == expected_numbers
    if expected_numbers:
        assert result.sources[0].filename == "handbook.pdf"
        assert result.sources[0].page == 3
        assert result.sources[0].content == chunk.content
