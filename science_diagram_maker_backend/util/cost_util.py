from config.pricing_config import PricingConfig
from model.diagram_model import TokenUsageModel


class CostUtil:
    @staticmethod
    def calculate_cost(
        model_name: str | None,
        token_usage: TokenUsageModel
    ) -> float | None:
        if not model_name:
            return None
        pricing = PricingConfig.MODEL_PRICING.get(
            model_name.removeprefix("models/")
        )
        if pricing is None:
            return None
        if token_usage.input_tokens is None:
            return None
        if token_usage.output_tokens is None:
            return None
        thinking_tokens = token_usage.thinking_tokens or 0
        input_cost = token_usage.input_tokens * pricing["input"]
        output_cost = (
            token_usage.output_tokens + thinking_tokens
        ) * pricing["output"]
        return round(
            (input_cost + output_cost) /
            PricingConfig.TOKENS_PER_MILLION,
            8
        )

    @staticmethod
    def aggregate_token_usage(
        usages: list[TokenUsageModel]
    ) -> TokenUsageModel:
        return TokenUsageModel(
            input_tokens=CostUtil.sum_optional(
                [usage.input_tokens for usage in usages]
            ),
            output_tokens=CostUtil.sum_optional(
                [usage.output_tokens for usage in usages]
            ),
            thinking_tokens=CostUtil.sum_optional(
                [usage.thinking_tokens for usage in usages]
            ),
            total_tokens=CostUtil.sum_optional(
                [usage.total_tokens for usage in usages]
            )
        )

    @staticmethod
    def sum_optional(values: list[int | None]) -> int | None:
        if not values or any(value is None for value in values):
            return None
        return sum(values)
