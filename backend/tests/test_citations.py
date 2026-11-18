from app.services.llm import extract_citations


def test_citations_in_order():
    assert extract_citations("отпуск [1], суточные [2].", count=3) == [1, 2]


def test_duplicates_removed_order_kept():
    assert extract_citations("a [2] b [1] c [2]", count=3) == [2, 1]


def test_out_of_range_ignored():
    assert extract_citations("a [0] b [3] c [9]", count=3) == [3]


def test_no_citations():
    assert extract_citations("просто текст без ссылок", count=3) == []


def test_multi_digit_number():
    assert extract_citations("см. [12]", count=15) == [12]


def test_not_a_citation():
    assert extract_citations("список [a] и [1, 2]", count=3) == []
