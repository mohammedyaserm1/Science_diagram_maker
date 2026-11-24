class HealthController:
    @staticmethod
    def io_health_check():
        return {
            "status": "healthy",
            "message": "Science Diagram Maker API is running"
        }