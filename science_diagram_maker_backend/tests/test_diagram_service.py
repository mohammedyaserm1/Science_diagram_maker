import pytest
from unittest.mock import patch
from google.genai.errors import APIError
from model.diagram_model import (
    GenerationResultModel,
    TokenUsageModel
)
from service.diagram_service import DiagramService


VALID_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500">
    <title>Circle demonstration</title>
    <circle cx="200" cy="200" r="50" fill="#2563eb">
        <animate attributeName="cx"
                 values="200;300;200"
                 dur="3s"
                 repeatCount="indefinite"/>
    </circle>
    <text x="100" y="60" font-family="monospace" font-size="16">Radius</text>
    <text x="100" y="90" font-family="monospace" font-size="16">Diameter</text>
    <text x="100" y="120" font-family="monospace" font-size="16">Centre</text>
</svg>
"""

INVALID_SVG = VALID_SVG.replace(
    "<title>Circle demonstration</title>",
    ""
)


def create_generation(svg: str):
    return GenerationResultModel(
        concept_id=2,
        model_name="gemini-3.5-flash-lite",
        svg=svg,
        token_usage=TokenUsageModel(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300
        )
    )


def test_successful_generation():
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        return_value=create_generation(VALID_SVG)
    ) as generate:
        result = DiagramService.generate_diagram(2)
    assert result.passed
    assert result.svg is not None
    assert len(result.attempts) == 1
    assert result.retries.total_retries == 0
    assert generate.call_count == 1


def test_validation_retry():
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        side_effect=[
            create_generation(INVALID_SVG),
            create_generation(VALID_SVG)
        ]
    ) as generate:
        result = DiagramService.generate_diagram(2)
    assert result.passed
    assert len(result.attempts) == 2
    assert result.retries.validation_retries == 1
    assert result.retries.total_retries == 1
    assert result.token_usage.input_tokens == 200
    assert result.token_usage.output_tokens == 400
    assert result.estimated_cost_usd == pytest.approx(0.00106)
    second_call = generate.call_args_list[1]
    assert "title_and_labels" in second_call.args[1]


def test_validation_retry_exhausted():
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        return_value=create_generation(INVALID_SVG)
    ) as generate:
        result = DiagramService.generate_diagram(2)
    assert not result.passed
    assert result.svg is None
    assert generate.call_count == 2
    assert result.retries.validation_retries == 1
    assert result.error is not None


def test_api_failure():
    error = APIError(
        403,
        {
            "error": {
                "code": 403,
                "message": "Permission denied"
            }
        }
    )
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        side_effect=error
    ) as generate:
        result = DiagramService.generate_diagram(2)
    assert not result.passed
    assert result.svg is None
    assert result.retries.total_retries == 0
    assert result.estimated_cost_usd is None
    assert "403" in result.error
    assert generate.call_count == 1


def test_empty_svg_retry():
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        side_effect=[
            create_generation(""),
            create_generation(VALID_SVG)
        ]
    ):
        result = DiagramService.generate_diagram(2)
    assert result.passed
    assert result.retries.validation_retries == 1
    assert not result.attempts[0].validation.passed


def test_combined_api_and_validation_retry():
    error = APIError(
        429,
        {
            "error": {
                "code": 429,
                "message": "Rate limit exceeded"
            }
        }
    )
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        side_effect=[
            error,
            create_generation(INVALID_SVG),
            create_generation(VALID_SVG)
        ]
    ) as generate:
        with patch("util.retry_util.time.sleep"):
            result = DiagramService.generate_diagram(2)
    assert result.passed
    assert generate.call_count == 3
    assert result.retries.api_retries == 1
    assert result.retries.validation_retries == 1
    assert result.retries.total_retries == 2
    assert len(result.attempts) == 2