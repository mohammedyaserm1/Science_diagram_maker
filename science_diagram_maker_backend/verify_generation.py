import json
from service.concept_service import ConceptService
from service.gemini_service import GeminiService


def main():
    concept = ConceptService.get_concept_by_id(2)
    print(f"Generating diagram: {concept.name}")
    result = GeminiService.generate_svg(concept)
    print(f"Model: {result.model_name}")
    print(f"SVG length: {len(result.svg)} characters")
    print(json.dumps(result.token_usage.model_dump(), indent=4))
    print("SVG response preview:")
    print(result.svg[:500])


if __name__ == "__main__":
    main()