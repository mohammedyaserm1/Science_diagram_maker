import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from google.genai.errors import APIError
from httpx2 import ConnectError, ReadTimeout
from config.app_config import AppConfig
from main import app
from model.diagram_model import GenerationResultModel
from service.result_service import ResultService

client = TestClient(app)


def test_get_empty_diagrams(isolated_results_file):
    response = client.get("/api/diagrams")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_diagrams(
    isolated_results_file,
    create_saved_result
):
    for concept_id in range(1, 6):
        ResultService.save_result(
            create_saved_result(concept_id)
        )
    with patch(
        "service.gemini_service.GeminiService.generate_svg"
    ) as generate:
        response = client.get("/api/diagrams")
    assert response.status_code == 200
    assert len(response.json()) == 5
    generate.assert_not_called()


def test_get_single_diagram(
    isolated_results_file,
    create_saved_result
):
    ResultService.save_result(
        create_saved_result(4)
    )
    response = client.get("/api/diagrams/4")
    assert response.status_code == 200
    assert response.json()["concept"]["name"] == "Photosynthesis"


def test_get_nonexistent_diagram(isolated_results_file):
    response = client.get("/api/diagrams/99")
    assert response.status_code == 404


def test_invalid_concept_id(isolated_results_file):
    response = client.get("/api/diagrams/invalid")
    assert response.status_code == 422


def test_live_generation_reuses_pipeline(isolated_results_file, create_saved_result):
    saved = create_saved_result(3)
    generation = GenerationResultModel(
        concept_id=3, model_name=saved.model_name, svg=saved.svg,
        token_usage=saved.token_usage
    )
    with patch("service.diagram_service.GeminiService.generate_svg", return_value=generation):
        response = client.post("/api/diagrams/3/generate")
    assert response.status_code == 200
    assert response.json()["passed"]
    assert response.json()["svg"] == saved.svg
    assert not isolated_results_file.exists()


def test_live_generation_rejects_unknown_concept():
    with patch("service.diagram_service.GeminiService.generate_svg") as generate:
        assert client.post("/api/diagrams/99/generate").status_code == 404
        generate.assert_not_called()


def test_live_generation_preserves_saved_svg_on_provider_failure(
    isolated_results_file, create_saved_result
):
    saved = create_saved_result(3)
    ResultService.save_result(saved)
    error = APIError(503, {"error": {"code": 503, "message": "private upstream detail"}})
    with patch("service.diagram_service.GeminiService.generate_svg", side_effect=error):
        with patch("util.retry_util.time.sleep") as delay:
            response = client.post("/api/diagrams/3/generate")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "temporarily unavailable" in detail["error"]
    assert "private upstream detail" not in response.text
    assert "svg" not in detail
    assert detail["retries"]["api_retries"] == 3
    assert [call.args[0] for call in delay.call_args_list] == [5, 10, 20]
    assert ResultService.get_result_by_concept_id(3) == saved


def test_live_generation_rejects_invalid_svg(isolated_results_file, create_saved_result):
    saved = create_saved_result(2)
    generation = GenerationResultModel(
        concept_id=2, model_name=saved.model_name, svg="",
        token_usage=saved.token_usage
    )
    with patch("service.diagram_service.GeminiService.generate_svg", return_value=generation):
        response = client.post("/api/diagrams/2/generate")
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert not detail["passed"]
    assert detail["retries"]["validation_retries"] == 1
    assert detail["token_usage"]["total_tokens"] == 600
    assert "svg" not in detail


def test_live_generation_without_api_key(isolated_results_file, monkeypatch):
    monkeypatch.setattr(AppConfig, "GEMINI_API_KEY", None)
    response = client.post("/api/diagrams/2/generate")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]["error"]


@pytest.mark.parametrize(
    ("network_error", "status_code", "message"),
    [(ConnectError, 502, "could not reach"), (ReadTimeout, 504, "timed out")]
)
def test_live_generation_handles_transport_failure(network_error, status_code, message):
    with patch(
        "service.diagram_service.GeminiService.generate_svg",
        side_effect=network_error("private transport details")
    ):
        response = client.post("/api/diagrams/2/generate")
    assert response.status_code == status_code
    assert message in response.json()["detail"]["error"]
    assert "private transport details" not in response.text


def test_live_generation_cors_only_allows_configured_frontend():
    preflight = {"Access-Control-Request-Method": "POST"}
    allowed = client.options(
        "/api/diagrams/2/generate",
        headers={**preflight, "Origin": AppConfig.FRONTEND_URL}
    )
    denied = client.options(
        "/api/diagrams/2/generate",
        headers={**preflight, "Origin": "https://unconfigured.example"}
    )
    assert allowed.status_code == 200
    assert allowed.headers["Access-Control-Allow-Origin"] == AppConfig.FRONTEND_URL
    assert denied.status_code == 400
    assert "Access-Control-Allow-Origin" not in denied.headers
