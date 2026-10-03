import pytest

from evaluate_merger import EXAMPLE, evaluate_merger, main

BAD = {"revenue": 1000, "profit": 10, "assets": 1000, "liabilities": 900}


def test_example_is_interesting():
    ev = evaluate_merger(*EXAMPLE)
    assert ev.interesting and ev.metrics["revenue_growth"] > 0


def test_good_without_prev_revenue_still_works():
    a = {"revenue": 1000, "profit": 200, "assets": 1500, "liabilities": 500}
    ev = evaluate_merger(a, a)
    assert ev.interesting and ev.metrics["revenue_growth"] is None


def test_indebted_not_interesting():
    assert not evaluate_merger(BAD, BAD).interesting


def test_shrinking_revenue_penalised():
    a = dict(EXAMPLE[0], revenue_prev=2_000_000)
    b = dict(EXAMPLE[1], revenue_prev=2_000_000)
    ev = evaluate_merger(a, b)
    assert ev.metrics["revenue_growth"] < 0
    assert not ev.criteria["Croissance du chiffre d'affaires"][2]


@pytest.mark.parametrize("patch", [{"assets": 0}, {"revenue": 0}, {"liabilities": -1},
                                   {"profit": "x"}])
def test_invalid_input(patch):
    with pytest.raises(ValueError):
        evaluate_merger(dict(EXAMPLE[0], **patch), EXAMPLE[1])


def test_missing_field():
    with pytest.raises(ValueError):
        evaluate_merger({"revenue": 1}, EXAMPLE[1])


def test_cli(capsys):
    assert main([]) == 0
    assert "intéressante" in capsys.readouterr().out
    assert main(["nope.json", "nope2.json"]) == 1
