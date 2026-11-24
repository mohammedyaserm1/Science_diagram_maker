from fastapi import APIRouter
from controller.diagram_controller import DiagramController
from model.diagram_model import DiagramResultModel

router = APIRouter(
    prefix="/api/diagrams",
    tags=["Diagrams"]
)

router.add_api_route(
    "",
    DiagramController.io_get_all_diagrams,
    methods=["GET"],
    response_model=list[DiagramResultModel]
)

router.add_api_route(
    "/{concept_id}",
    DiagramController.io_get_diagram,
    methods=["GET"],
    response_model=DiagramResultModel
)

router.add_api_route(
    "/{concept_id}/generate",
    DiagramController.io_generate_diagram,
    methods=["POST"],
    response_model=DiagramResultModel,
    responses={
        404: {"description": "Unknown concept"},
        429: {"description": "Gemini rate limit reached"},
        500: {"description": "Unexpected generation error"},
        502: {"description": "Gemini request or SVG validation failed"},
        503: {"description": "Gemini unavailable or unconfigured"},
        504: {"description": "Gemini request timed out"}
    }
)
