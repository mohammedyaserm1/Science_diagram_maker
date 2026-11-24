import pytest
from config.app_config import AppConfig
from service.concept_service import ConceptService
from service.validation_service import ValidationService
from model.diagram_model import (
    DiagramResultModel,
    TokenUsageModel,
    RetryModel
)


@pytest.fixture
def isolated_results_file(tmp_path, monkeypatch):
    results_file = tmp_path / "results.json"
    monkeypatch.setattr(
        AppConfig,
        "RESULTS_FILE",
        results_file
    )
    return results_file


@pytest.fixture
def create_saved_result():
    def create_result(concept_id: int):
        concept = ConceptService.get_concept_by_id(concept_id)
        svg = """
        <svg xmlns="http://www.w3.org/2000/svg"
             viewBox="0 0 800 500">
            <title>Test diagram</title>
            <circle cx="200" cy="200" r="30" fill="#2563eb">
                <animate attributeName="cx"
                         values="200;300;200"
                         dur="3s"
                         repeatCount="indefinite"/>
            </circle>
            <text x="100" y="60" font-family="monospace"
                  font-size="16">Label 1</text>
            <text x="100" y="90" font-family="monospace"
                  font-size="16">Label 2</text>
            <text x="100" y="120" font-family="monospace"
                  font-size="16">Label 3</text>
        </svg>
        """
        validation = ValidationService.validate_svg(svg)
        return DiagramResultModel(
            concept=concept,
            model_name="gemini-3.5-flash-lite",
            svg=svg,
            passed=validation.passed,
            validation=validation,
            token_usage=TokenUsageModel(
                input_tokens=100,
                output_tokens=200,
                total_tokens=300
            ),
            retries=RetryModel(),
            estimated_cost_usd=0.00053,
            attempts=[],
            generated_at="2026-01-01T00:00:00+00:00"
        )
    return create_result