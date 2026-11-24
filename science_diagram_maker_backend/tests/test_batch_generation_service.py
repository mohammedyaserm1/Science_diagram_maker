from unittest.mock import patch
from service.batch_generation_service import BatchGenerationService
from service.result_service import ResultService


def test_generate_all_diagrams(
    isolated_results_file,
    create_saved_result
):
    with patch(
        "service.batch_generation_service.DiagramService.generate_diagram",
        side_effect=create_saved_result
    ) as generate:
        with patch(
            "service.batch_generation_service.time.sleep"
        ) as sleep:
            results = BatchGenerationService.generate_all_diagrams()
    assert len(results) == 5
    assert generate.call_count == 5
    assert sleep.call_count == 4
    assert len(ResultService.get_all_results()) == 5


def test_resume_batch_generation(
    isolated_results_file,
    create_saved_result
):
    ResultService.save_result(
        create_saved_result(1)
    )
    ResultService.save_result(
        create_saved_result(2)
    )
    with patch(
        "service.batch_generation_service.DiagramService.generate_diagram",
        side_effect=create_saved_result
    ) as generate:
        with patch(
            "service.batch_generation_service.time.sleep"
        ):
            results = BatchGenerationService.generate_all_diagrams()
    generated_ids = [
        call.args[0]
        for call in generate.call_args_list
    ]
    assert generated_ids == [3, 4, 5]
    assert len(results) == 5


def test_regenerate_single_diagram(
    isolated_results_file,
    create_saved_result
):
    ResultService.save_result(
        create_saved_result(2)
    )
    replacement = create_saved_result(2)
    replacement.estimated_cost_usd = 0.01
    with patch(
        "service.batch_generation_service.DiagramService.generate_diagram",
        return_value=replacement
    ) as generate:
        result = BatchGenerationService.regenerate_diagram(2)
    assert result.concept.id == 2
    assert result.estimated_cost_usd == 0.01
    assert len(ResultService.get_all_results()) == 1
    generate.assert_called_once_with(2)


def test_skip_completed_batch(
    isolated_results_file,
    create_saved_result
):
    for concept_id in range(1, 6):
        ResultService.save_result(
            create_saved_result(concept_id)
        )
    with patch(
        "service.batch_generation_service.DiagramService.generate_diagram"
    ) as generate:
        results = BatchGenerationService.generate_all_diagrams()
    assert len(results) == 5
    generate.assert_not_called()


def test_failed_regeneration_keeps_passing_saved_result(
    isolated_results_file, create_saved_result
):
    saved = create_saved_result(2)
    ResultService.save_result(saved)
    failed = saved.model_copy(update={"passed": False, "svg": None})
    with patch(
        "service.batch_generation_service.DiagramService.generate_diagram",
        return_value=failed
    ):
        assert BatchGenerationService.regenerate_diagram(2) == failed
    assert ResultService.get_result_by_concept_id(2) == saved
