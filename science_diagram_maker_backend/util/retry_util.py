import logging
import time
from typing import Callable, TypeVar
from google.genai.errors import APIError
from config.app_config import AppConfig
from model.diagram_model import RetryModel

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RetryUtil:
    @staticmethod
    def execute(
        operation: Callable[[], T],
        retries: RetryModel
    ) -> T:
        for attempt in range(AppConfig.MAX_API_RETRIES + 1):
            try:
                return operation()
            except APIError as error:
                if error.code not in AppConfig.RETRYABLE_STATUS_CODES:
                    raise
                if attempt >= AppConfig.MAX_API_RETRIES:
                    raise
                delay = AppConfig.RETRY_INITIAL_DELAY * (2 ** attempt)
                logger.warning(
                    "Gemini API error %s. Retrying in %s seconds",
                    error.code,
                    delay
                )
                time.sleep(delay)
                retries.api_retries += 1
                retries.total_retries += 1
        raise RuntimeError("API retry limit exhausted")