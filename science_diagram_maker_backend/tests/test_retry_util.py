import pytest
from unittest.mock import Mock, patch
from google.genai.errors import APIError
from model.diagram_model import RetryModel
from util.retry_util import RetryUtil


def create_api_error(code: int):
    return APIError(
        code,
        {
            "error": {
                "code": code,
                "message": "Simulated API error"
            }
        }
    )


def test_success_without_retry():
    operation = Mock(return_value="success")
    retries = RetryModel()
    result = RetryUtil.execute(operation, retries)
    assert result == "success"
    assert operation.call_count == 1
    assert retries.total_retries == 0


@pytest.mark.parametrize("status_code", [429, 503])
def test_retryable_api_errors(status_code):
    operation = Mock(
        side_effect=[
            create_api_error(status_code),
            "success"
        ]
    )
    retries = RetryModel()
    with patch("util.retry_util.time.sleep") as sleep:
        result = RetryUtil.execute(operation, retries)
    assert result == "success"
    assert operation.call_count == 2
    assert retries.api_retries == 1
    assert retries.total_retries == 1
    sleep.assert_called_once_with(5)


def test_maximum_api_retries():
    operation = Mock(side_effect=create_api_error(429))
    retries = RetryModel()
    with patch("util.retry_util.time.sleep") as sleep:
        with pytest.raises(APIError):
            RetryUtil.execute(operation, retries)
    assert operation.call_count == 4
    assert retries.api_retries == 3
    assert retries.total_retries == 3
    delays = [
        call.args[0]
        for call in sleep.call_args_list
    ]
    assert delays == [5, 10, 20]


def test_non_retryable_error():
    operation = Mock(side_effect=create_api_error(400))
    retries = RetryModel()
    with patch("util.retry_util.time.sleep") as sleep:
        with pytest.raises(APIError):
            RetryUtil.execute(operation, retries)
    assert operation.call_count == 1
    assert retries.total_retries == 0
    sleep.assert_not_called()