import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from config.app_config import AppConfig
from config.validation_config import ValidationConfig
from model.diagram_model import GenerationAttemptModel, GenerationResultModel, RetryModel

logger = logging.getLogger(__name__)


class GenerationDiagnosticService:
    @staticmethod
    def save_rejected_response(
        generation: GenerationResultModel,
        attempt: GenerationAttemptModel,
        requested_model_name: str,
        retries: RetryModel
    ) -> None:
        directory = AppConfig.SVG_DIAGNOSTICS_DIR
        raw_svg = generation.raw_svg
        if directory is None or attempt.validation.passed or not raw_svg:
            return
        if len(raw_svg) > ValidationConfig.MAX_SVG_LENGTH:
            logger.warning("Skipping oversized SVG diagnostic for concept %s", generation.concept_id)
            return
        diagnostic = {
            "concept_id": generation.concept_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "requested_model_name": requested_model_name,
            "attempt": attempt.model_dump(mode="json"),
            "retries_at_response": retries.model_dump(mode="json"),
            "raw_svg": raw_svg
        }
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"concept_{generation.concept_id}_{uuid4().hex}.json"
            with path.open("x", encoding="utf-8") as file:
                json.dump(diagnostic, file, indent=2)
        except OSError:
            logger.warning("Could not save SVG diagnostic for concept %s", generation.concept_id)
