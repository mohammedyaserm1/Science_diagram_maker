class PricingConfig:
    TOKENS_PER_MILLION = 1000000

    MODEL_PRICING = {
        "gemini-3.5-flash-lite": {
            "input": 0.30,
            "output": 2.50
        }
    }