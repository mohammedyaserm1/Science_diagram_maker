import logging
from datetime import datetime, timezone
from google.genai.errors import APIError
from httpx import RequestError, TimeoutException
from httpx2 import RequestError as GeminiRequestError
from httpx2 import TimeoutException as GeminiTimeoutError
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
from service.gemini_service import GeminiConfigurationError, GeminiService
from service.generation_diagnostic_service import GenerationDiagnosticService
from service.validation_service import ValidationService
from util.cost_util import CostUtil
from util.retry_util import RetryUtil

logger = logging.getLogger(__name__)

GEMINI_API_ERRORS = {
    401: (502, "Gemini rejected the backend credentials (HTTP 401)"),
    403: (502, "Gemini denied access to the configured model (HTTP 403)"),
    429: (429, "Gemini rate limit reached after retries (HTTP 429). Try again later."),
    503: (503, "Gemini is temporarily unavailable after retries (HTTP 503). Try again later."),
    504: (504, "Gemini timed out (HTTP 504). Try again later.")
}


class DiagramService:
    @staticmethod
    def generate_diagram(concept_id: int, reviewer_feedback: str = "") -> DiagramResultModel:
        concept = ConceptService.get_concept_by_id(concept_id)
        retries = RetryModel()
        attempts = []
        svg = None
        error_message = None
        error_status = None
        requested_model_name = AppConfig.GEMINI_MODEL
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
                        feedback,
                        reviewer_feedback=reviewer_feedback
                    ),
                    retries
                )
            except APIError as error:
                error_status, error_message = GEMINI_API_ERRORS.get(
                    error.code,
                    (502, f"Gemini API request failed (HTTP {error.code})")
                )
                break
            except GeminiConfigurationError:
                error_status = 503
                error_message = "Live generation is unavailable because Gemini is not configured."
                break
            except (TimeoutException, GeminiTimeoutError):
                error_status = 504
                error_message = "Gemini timed out. Try again later."
                break
            except (RequestError, GeminiRequestError):
                error_status = 502
                error_message = "The backend could not reach Gemini. Try again later."
                break
            except Exception as error:
                logger.error(
                    "Generation failed for concept %s: %s",
                    concept_id,
                    type(error).__name__
                )
                error_status = 500
                error_message = "Diagram generation failed"
                break
            svg = generation.svg
            validation = ValidationService.validate_svg(svg)
            if generation.finish_reason == "MAX_TOKENS":
                validity = validation.checks[0]
                reason = "Gemini reached its token limit before completing the response"
                if not validity.passed:
                    reason = f"{reason}: {validity.message}"
                validity.passed = False
                validity.message = reason
                validation.passed = False
            attempts.append(
                GenerationAttemptModel(
                    attempt_number=index + 1,
                    reported_model_name=generation.model_name,
                    finish_reason=generation.finish_reason,
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
            GenerationDiagnosticService.save_rejected_response(
                generation, attempts[-1], requested_model_name, retries
            )
            feedback = validation.get_failure_feedback()
            if generation.finish_reason == "MAX_TOKENS":
                feedback += "\nUse fewer shapes and labels so the SVG fits."
        if not validation.passed and error_message is None:
            error_message = "SVG validation failed after allowed attempts"
            error_status = 502
        reported_model_name = attempts[-1].reported_model_name if attempts else None
        result = DiagramResultModel(
            concept=concept,
            model_name=reported_model_name or requested_model_name,
            requested_model_name=requested_model_name,
            reported_model_name=reported_model_name,
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
            error=error_message,
            error_status=error_status
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
            "Concept: %s | Requested model: %s | Reported model: %s | Passed: %s | "
            "Input tokens: %s | Output tokens: %s | "
            "Thinking tokens: %s | Total tokens: %s | Estimated cost USD: %s | "
            "Generated at: %s | "
            "API retries: %s | Validation retries: %s | Total retries: %s",
            result.concept.name,
            result.requested_model_name,
            result.reported_model_name,
            result.passed,
            result.token_usage.input_tokens,
            result.token_usage.output_tokens,
            result.token_usage.thinking_tokens,
            result.token_usage.total_tokens,
            result.estimated_cost_usd,
            result.generated_at,
            result.retries.api_retries,
            result.retries.validation_retries,
            result.retries.total_retries
        )
        for attempt in result.attempts:
            logger.info("Attempt %s | Finish reason: %s", attempt.attempt_number, attempt.finish_reason)
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
