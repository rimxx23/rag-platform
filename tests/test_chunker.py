import pytest

from app.services.chunker import chunk_text


def test_chunks_with_overlap():
    assert chunk_text("a b c d e f g", size=3, overlap=1) == ["a b c", "c d e", "e f g"]


def test_no_tail_of_only_overlap():
    assert chunk_text("a b c d e", size=3, overlap=1) == ["a b c", "c d e"]


def test_short_text_is_one_chunk():
    assert chunk_text("hello world", size=300, overlap=50) == ["hello world"]


def test_empty_text():
    assert chunk_text("   \n  ") == []


def test_extra_whitespace_is_normalized():
    assert chunk_text("a\n\nb   c", size=5, overlap=0) == ["a b c"]


def test_no_overlap():
    assert chunk_text("a b c d", size=2, overlap=0) == ["a b", "c d"]


@pytest.mark.parametrize("size, overlap", [(3, 3), (3, 5), (0, 0), (3, -1)])
def test_invalid_params(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("a b c", size=size, overlap=overlap)
