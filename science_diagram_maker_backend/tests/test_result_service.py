import json
from service.result_service import ResultService


def test_missing_results_file(isolated_results_file):
    assert ResultService.get_all_results() == []


def test_save_and_read_result(
    isolated_results_file,
    create_saved_result
):
    result = create_saved_result(1)
    ResultService.save_result(result)
    results = ResultService.get_all_results()
    assert len(results) == 1
    assert results[0].concept.id == 1
    assert isolated_results_file.exists()


def test_update_existing_result(
    isolated_results_file,
    create_saved_result
):
    result = create_saved_result(2)
    ResultService.save_result(result)
    result.estimated_cost_usd = 0.005
    ResultService.save_result(result)
    results = ResultService.get_all_results()
    assert len(results) == 1
    assert results[0].estimated_cost_usd == 0.005


def test_results_sorted_by_concept_id(
    isolated_results_file,
    create_saved_result
):
    for concept_id in [3, 1, 2]:
        ResultService.save_result(
            create_saved_result(concept_id)
        )
    results = ResultService.get_all_results()
    assert [
        result.concept.id for result in results
    ] == [1, 2, 3]


def test_get_result_by_concept_id(
    isolated_results_file,
    create_saved_result
):
    ResultService.save_result(
        create_saved_result(4)
    )
    result = ResultService.get_result_by_concept_id(4)
    assert result is not None
    assert result.concept.name == "Photosynthesis"


def test_get_missing_concept(isolated_results_file):
    assert ResultService.get_result_by_concept_id(99) is None


def test_results_file_is_valid_json(
    isolated_results_file,
    create_saved_result
):
    ResultService.save_result(
        create_saved_result(1)
    )
    with isolated_results_file.open(
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)
    assert isinstance(data, list)
    assert data[0]["concept"]["id"] == 1
    assert not isolated_results_file.with_suffix(
        ".json.tmp"
    ).exists()