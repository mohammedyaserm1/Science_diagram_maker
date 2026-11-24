import hashlib
import json

from config.app_config import AppConfig
from service.result_service import ResultService
from service.validation_service import ValidationService


def test_local_fallback_manifest_matches_validated_source_files():
    directory = AppConfig.DATA_DIR / "fallback"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["diagrams"]) == {"1", "2", "3"}
    for entry in manifest["diagrams"].values():
        svg = (directory / entry["file"]).read_text(encoding="utf-8")
        assert hashlib.sha256(svg.encode("utf-8")).hexdigest() == entry["revision"]
        current_validation = ValidationService.validate_svg(svg)
        assert current_validation.passed
        assert current_validation.model_dump(mode="json") == entry["validation"]


def test_saved_science_review_is_tied_to_the_reviewed_svg_revision():
    manifest_path = AppConfig.DATA_DIR / "fallback" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for concept_id, revision in manifest["reviewed_gemini_revisions"].items():
        result = ResultService.get_result_by_concept_id(int(concept_id))
        assert result is not None and result.svg and result.passed
        assert result.generated_at == revision
        assert ValidationService.validate_svg(result.svg).passed


def test_failed_replacement_preserves_its_prior_saved_svg():
    data_dir = AppConfig.DATA_DIR
    failures = json.loads((data_dir / "replacement_failures.json").read_text(encoding="utf-8"))
    manifest = json.loads((data_dir / "fallback" / "manifest.json").read_text(encoding="utf-8"))
    for failure in failures:
        concept_id = failure["concept"]["id"]
        result = ResultService.get_result_by_concept_id(concept_id)
        assert result is not None and result.svg and result.passed
        assert failure["base_generated_at"] == manifest["diagrams"][str(concept_id)]["replaces_generated_at"]
        assert not failure["passed"] and failure["svg"] is None and failure["error"]
