import json
from service.concept_service import ConceptService
from service.gemini_service import GeminiService
from service.validation_service import ValidationService


def main():
    concept = ConceptService.get_concept_by_id(2)
    print(f"Generating diagram: {concept.name}")
    result = GeminiService.generate_svg(concept)
    print(f"Model: {result.model_name}")
    print(f"SVG length: {len(result.svg)} characters")
    print("Token usage:")
    print(json.dumps(result.token_usage.model_dump(), indent=4))
    validation = ValidationService.validate_svg(result.svg)
    print("\nValidation results:")
    for check in validation.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.message}")
    print(f"\nOverall result: {'PASS' if validation.passed else 'FAIL'}")
    if not validation.passed:
        print("\nValidation feedback:")
        print(validation.get_failure_feedback())


if __name__ == "__main__":
    main()