from fastapi import APIRouter
from controller.health_controller import HealthController

router = APIRouter(
    prefix="/api",
    tags=["Health"]
)

router.add_api_route(
    "/health",
    HealthController.io_health_check,
    methods=["GET"]
)