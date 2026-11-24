import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from config.app_config import AppConfig
from model.diagram_model import DiagramResultModel


class ResultService:
    @staticmethod
    def get_all_results() -> list[DiagramResultModel]:
        if not AppConfig.RESULTS_FILE.exists():
            return []
        with AppConfig.RESULTS_FILE.open("r", encoding="utf-8") as file:
            results = json.load(file)
        return [
            DiagramResultModel.model_validate(result)
            for result in results
        ]

    @staticmethod
    def get_result_by_concept_id(
        concept_id: int
    ) -> DiagramResultModel | None:
        for result in ResultService.get_all_results():
            if result.concept.id == concept_id:
                return result
        return None

    @staticmethod
    def save_result(result: DiagramResultModel) -> None:
        results = ResultService.get_all_results()
        result_map = {
            item.concept.id: item
            for item in results
        }
        result_map[result.concept.id] = result
        sorted_results = sorted(
            result_map.values(),
            key=lambda item: item.concept.id
        )
        ResultService.write_results(sorted_results)

    @staticmethod
    def write_results(
        results: list[DiagramResultModel]
    ) -> None:
        AppConfig.RESULTS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )
        data = [
            result.model_dump(mode="json")
            for result in results
        ]
        temporary_file = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=AppConfig.RESULTS_FILE.parent,
                prefix=f"{AppConfig.RESULTS_FILE.name}.",
                suffix=".tmp",
                delete=False
            ) as file:
                temporary_file = Path(file.name)
                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )
            ResultService.replace_results_file(temporary_file)
        finally:
            if temporary_file is not None:
                temporary_file.unlink(missing_ok=True)

    @staticmethod
    def replace_results_file(temporary_file: Path) -> None:
        for attempt in range(3):
            try:
                os.replace(temporary_file, AppConfig.RESULTS_FILE)
                return
            except PermissionError as error:
                # Windows readers or file scanners can briefly hold the destination open.
                if getattr(error, "winerror", None) not in {5, 32} or attempt == 2:
                    raise
                time.sleep(0.05 * (attempt + 1))
