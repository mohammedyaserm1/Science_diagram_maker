from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.app_config import AppConfig
from config.logging_config import LoggingConfig
from route.health_route import router as health_router
from route.diagram_route import router as diagram_router

LoggingConfig.configure()

app = FastAPI(
    title="Science Diagram Maker API",
    description="AI-powered science diagram generation and validation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[AppConfig.FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

app.include_router(health_router)
app.include_router(diagram_router)