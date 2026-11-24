import logging
import time
from config.app_config import AppConfig
from model.diagram_model import DiagramResultModel
from service.concept_service import ConceptService
from service.diagram_service import DiagramService
from service.result_service import ResultService

logger = logging.getLogger(__name__)


class BatchGenerationService:
    @staticmethod
    def generate_all_diagrams() -> list[DiagramResultModel]:
        concepts = ConceptService.get_all_concepts()
        saved_results = {
            result.concept.id: result
            for result in ResultService.get_all_results()
        }
        pending_concepts = [
            concept for concept in concepts
            if concept.id not in saved_results
        ]
        for index, concept in enumerate(pending_concepts):
            logger.info(
                "Generating concept %s of %s: %s",
                index + 1,
                len(pending_concepts),
                concept.name
            )
            result = DiagramService.generate_diagram(concept.id)
            ResultService.save_result(result)
            logger.info(
                "Saved concept %s | Passed: %s",
                concept.id,
                result.passed
            )
            if index < len(pending_concepts) - 1:
                logger.info(
                    "Waiting %s seconds before next concept",
                    AppConfig.BATCH_GENERATION_DELAY
                )
                time.sleep(AppConfig.BATCH_GENERATION_DELAY)
        return ResultService.get_all_results()

    @staticmethod
    def regenerate_diagram(
        concept_id: int
    ) -> DiagramResultModel:
        result = DiagramService.generate_diagram(concept_id)
        previous = ResultService.get_result_by_concept_id(concept_id)
        if result.passed or previous is None or not previous.passed:
            ResultService.save_result(result)
        return result
