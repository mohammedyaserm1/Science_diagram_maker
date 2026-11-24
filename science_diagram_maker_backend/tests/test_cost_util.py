import pytest
from model.diagram_model import TokenUsageModel
from util.cost_util import CostUtil


def test_cost_calculation():
    usage = TokenUsageModel(
        input_tokens=1000000,
        output_tokens=1000000,
        thinking_tokens=0
    )
    cost = CostUtil.calculate_cost(
        "gemini-3.5-flash-lite",
        usage
    )
    assert cost == pytest.approx(2.80)


@pytest.mark.parametrize(
    ("model", "expected_cost"),
    [("gemini-3.5-flash-lite", 5.30), ("gemini-3.5-flash", 19.50)]
)
def test_thinking_token_cost(model, expected_cost):
    usage = TokenUsageModel(
        input_tokens=1000000,
        output_tokens=1000000,
        thinking_tokens=1000000
    )
    cost = CostUtil.calculate_cost(model, usage)
    assert cost == pytest.approx(expected_cost)


def test_unknown_model_cost():
    usage = TokenUsageModel(
        input_tokens=100,
        output_tokens=200
    )
    assert CostUtil.calculate_cost(
        "unknown-model",
        usage
    ) is None


def test_missing_token_usage():
    usage = TokenUsageModel()
    assert CostUtil.calculate_cost(
        "gemini-3.5-flash-lite",
        usage
    ) is None


def test_aggregate_token_usage():
    usages = [
        TokenUsageModel(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300
        ),
        TokenUsageModel(
            input_tokens=150,
            output_tokens=250,
            total_tokens=400
        )
    ]
    result = CostUtil.aggregate_token_usage(usages)
    assert result.input_tokens == 250
    assert result.output_tokens == 450
    assert result.total_tokens == 700
    assert result.thinking_tokens is None


def test_empty_token_usage():
    result = CostUtil.aggregate_token_usage([])
    assert result.input_tokens is None
    assert result.output_tokens is None
