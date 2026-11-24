from fastapi import HTTPException
from model.diagram_model import DiagramResultModel
from service.concept_service import ConceptNotFoundError
from service.diagram_service import DiagramService
from service.result_service import ResultService


class DiagramController:
    @staticmethod
    def io_get_all_diagrams() -> list[DiagramResultModel]:
        return ResultService.get_all_results()

    @staticmethod
    def io_get_diagram(
        concept_id: int
    ) -> DiagramResultModel:
        result = ResultService.get_result_by_concept_id(
            concept_id
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No saved diagram found for concept {concept_id}"
            )
        return result

    @staticmethod
    def io_generate_diagram(concept_id: int) -> DiagramResultModel:
        try:
            result = DiagramService.generate_diagram(concept_id)
        except ConceptNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        if not result.passed:
            raise HTTPException(
                status_code=result.error_status or 502,
                detail=result.model_dump(mode="json", exclude={"svg"})
            )
        return result
