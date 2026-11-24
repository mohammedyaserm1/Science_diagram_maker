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
        while True:
            try:
                return operation()
            except APIError as error:
                if error.code not in AppConfig.RETRYABLE_STATUS_CODES:
                    raise
                if retries.api_retries >= AppConfig.MAX_API_RETRIES:
                    raise
                delay = AppConfig.RETRY_INITIAL_DELAY * (2 ** retries.api_retries)
                logger.warning(
                    "Gemini API error %s. Retrying in %s seconds",
                    error.code,
                    delay
                )
                time.sleep(delay)
                retries.api_retries += 1
                retries.total_retries += 1
