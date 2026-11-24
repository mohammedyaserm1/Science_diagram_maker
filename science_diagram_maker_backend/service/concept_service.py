import json
from config.app_config import AppConfig
from model.diagram_model import ConceptModel


class ConceptService:
    @staticmethod
    def get_all_concepts() -> list[ConceptModel]:
        with AppConfig.CONCEPTS_FILE.open("r", encoding="utf-8") as file:
            concepts = json.load(file)
        return [ConceptModel(**concept) for concept in concepts]

    @staticmethod
    def get_concept_by_id(concept_id: int) -> ConceptModel:
        concepts = ConceptService.get_all_concepts()
        for concept in concepts:
            if concept.id == concept_id:
                return concept
        raise ValueError(f"Concept with ID {concept_id} was not found")