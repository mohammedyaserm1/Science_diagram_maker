class PricingConfig:
    TOKENS_PER_MILLION = 1000000

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
