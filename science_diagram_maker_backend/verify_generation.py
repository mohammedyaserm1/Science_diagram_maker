from config.logging_config import LoggingConfig
from service.diagram_service import DiagramService


def main():
    LoggingConfig.configure()
    result = DiagramService.generate_diagram(2)
    print("\nGeneration summary")
    print("-" * 50)
    print(f"Concept: {result.concept.name}")
    print(f"Model: {result.model_name}")
    print(f"Passed: {result.passed}")
    print(f"Input tokens: {result.token_usage.input_tokens}")
    print(f"Output tokens: {result.token_usage.output_tokens}")
    print(f"Thinking tokens: {result.token_usage.thinking_tokens}")
    print(f"Estimated cost USD: {result.estimated_cost_usd}")
    print(f"API retries: {result.retries.api_retries}")
    print(f"Validation retries: {result.retries.validation_retries}")
    print(f"Total retries: {result.retries.total_retries}")
    print("\nFinal validation results:")
    for check in result.validation.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.message}")
    if result.error:
        print(f"\nError: {result.error}")


if __name__ == "__main__":
    main()