from datetime import date, datetime, timezone


class PricingConfig:
    TOKENS_PER_MILLION = 1000000

    # Standard paid-tier USD rates used for estimates, including on free-tier runs.
    MODEL_PRICING = {
        "gemini-3.5-flash-lite": {
            "input": 0.30,
            "output": 2.50
        },
        "gemini-3.5-flash": {
            "input": 1.50,
            "output": 9.00
        },
        "gemini-3.1-flash-lite": {
            "input": 0.25,
            "output": 1.50
        }
    }

    @staticmethod
    def get_price(model_name: str, on_date: date | None = None) -> dict[str, float] | None:
        model_name = model_name.removeprefix("models/")
        if model_name == "gemini-3.6-flash":
            effective_date = on_date or datetime.now(timezone.utc).date()
            if effective_date < date(2027, 1, 1):
                return {"input": 0.75, "output": 3.75}
            return {"input": 1.50, "output": 7.50}
        return PricingConfig.MODEL_PRICING.get(model_name)
