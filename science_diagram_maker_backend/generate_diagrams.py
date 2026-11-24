import argparse
from config.logging_config import LoggingConfig
from service.batch_generation_service import BatchGenerationService
from service.result_service import ResultService


def print_summary():
    results = ResultService.get_all_results()
    print("\n" + "=" * 90)
    print("SCIENCE DIAGRAM GENERATION SUMMARY")
    print("=" * 90)
    print(
        f"{'Concept':<25}"
        f"{'Status':<10}"
        f"{'Cost (USD)':<18}"
        f"{'Retries':<10}"
    )
    print("-" * 90)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        cost = (
            f"${result.estimated_cost_usd:.8f}"
            if result.estimated_cost_usd is not None
            else "Unknown"
        )
        print(
            f"{result.concept.name:<25}"
            f"{status:<10}"
            f"{cost:<18}"
            f"{result.retries.total_retries:<10}"
        )
    print("-" * 90)
    passed_count = sum(
        result.passed for result in results
    )
    costs = [
        result.estimated_cost_usd
        for result in results
    ]
    total_cost = (
        sum(costs)
        if costs and all(cost is not None for cost in costs)
        else None
    )
    print(f"Total diagrams: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(results) - passed_count}")
    print(
        f"Total estimated cost: ${total_cost:.8f}"
        if total_cost is not None
        else "Total estimated cost: Unknown"
    )
    print("=" * 90)


def main():
    LoggingConfig.configure()
    parser = argparse.ArgumentParser(
        description="Generate and save animated science diagrams"
    )
    parser.add_argument(
        "--concept-id",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Explicitly generate or replace one concept"
    )
    args = parser.parse_args()
    if args.concept_id is not None:
        BatchGenerationService.regenerate_diagram(
            args.concept_id
        )
    else:
        BatchGenerationService.generate_all_diagrams()
    print_summary()


if __name__ == "__main__":
    main()