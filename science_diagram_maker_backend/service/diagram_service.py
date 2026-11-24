import logging
from datetime import datetime, timezone
from google.genai.errors import APIError
from config.app_config import AppConfig
from config.validation_config import ValidationConfig
from model.diagram_model import (
    DiagramResultModel,
    GenerationAttemptModel,
    RetryModel,
    ValidationCheckModel,
    ValidationResultModel
)
from service.concept_service import ConceptService
from service.gemini_service import GeminiService
from service.validation_service import ValidationService
from util.cost_util import CostUtil
from util.retry_util import RetryUtil

logger = logging.getLogger(__name__)


class DiagramService:
    @staticmethod
    def generate_diagram(concept_id: int) -> DiagramResultModel:
        concept = ConceptService.get_concept_by_id(concept_id)
        retries = RetryModel()
        attempts = []
        svg = None
        error_message = None
        feedback = ""
        validation = DiagramService.create_failed_validation(
            "No SVG generated"
        )
        for index in range(AppConfig.MAX_VALIDATION_RETRIES + 1):
            if index > 0:
                retries.validation_retries += 1
                retries.total_retries += 1
                logger.info(
                    "Retrying validation for concept %s",
                    concept_id
                )
            try:
                generation = RetryUtil.execute(
                    lambda: GeminiService.generate_svg(
                        concept,
                        feedback
                    ),
                    retries
                )
            except APIError as error:
                error_message = (
                    f"Gemini API request failed (HTTP {error.code})"
                )
                break
            except Exception as error:
                logger.error(
                    "Generation failed for concept %s: %s",
                    concept_id,
                    type(error).__name__
                )
                error_message = "Diagram generation failed"
                break
            svg = generation.svg
            validation = ValidationService.validate_svg(svg)
            attempts.append(
                GenerationAttemptModel(
                    attempt_number=index + 1,
                    token_usage=generation.token_usage,
                    validation=validation,
                    estimated_cost_usd=CostUtil.calculate_cost(
                        generation.model_name,
                        generation.token_usage
                    )
                )
            )
            if validation.passed:
                break
            feedback = validation.get_failure_feedback()
        if not validation.passed and error_message is None:
            error_message = "SVG validation failed after allowed attempts"
        result = DiagramResultModel(
            concept=concept,
            model_name=AppConfig.GEMINI_MODEL,
            svg=svg if validation.passed else None,
            passed=validation.passed,
            validation=validation,
            token_usage=CostUtil.aggregate_token_usage(
                [attempt.token_usage for attempt in attempts]
            ),
            retries=retries,
            estimated_cost_usd=DiagramService.get_total_cost(attempts),
            attempts=attempts,
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=error_message
        )
        DiagramService.log_result(result)
        return result

    @staticmethod
    def create_failed_validation(
        message: str
    ) -> ValidationResultModel:
        return ValidationResultModel(
            passed=False,
            checks=[
                ValidationCheckModel(
                    name=name,
                    passed=False,
                    message=message
                )
                for name in ValidationConfig.CHECK_NAMES
            ]
        )

    @staticmethod
    def get_total_cost(
        attempts: list[GenerationAttemptModel]
    ) -> float | None:
        costs = [
            attempt.estimated_cost_usd
            for attempt in attempts
        ]
        if not costs or any(cost is None for cost in costs):
            return None
        return round(sum(costs), 8)

    @staticmethod
    def log_result(result: DiagramResultModel):
        logger.info(
            "Concept: %s | Model: %s | Passed: %s | "
            "Input tokens: %s | Output tokens: %s | "
            "Thinking tokens: %s | Estimated cost USD: %s | "
            "API retries: %s | Validation retries: %s | Total retries: %s",
            result.concept.name,
            result.model_name,
            result.passed,
            result.token_usage.input_tokens,
            result.token_usage.output_tokens,
            result.token_usage.thinking_tokens,
            result.estimated_cost_usd,
            result.retries.api_retries,
            result.retries.validation_retries,
            result.retries.total_retries
        )
        for attempt in result.attempts:
            for check in attempt.validation.checks:
                logger.info(
                    "Attempt %s | %s: %s | %s",
                    attempt.attempt_number,
                    check.name,
                    "PASS" if check.passed else "FAIL",
                    check.message
                )
        if result.error:
            logger.warning("Generation error: %s", result.error)