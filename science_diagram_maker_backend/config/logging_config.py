import logging


class LoggingConfig:
    @staticmethod
    def configure():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )