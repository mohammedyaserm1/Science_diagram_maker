import re
from google import genai
from google.genai import types
from config.app_config import AppConfig
from config.prompt_config import PromptConfig
from model.diagram_model import (
    ConceptModel,
    GenerationResultModel,
    TokenUsageModel
)


class GeminiConfigurationError(RuntimeError):
    pass


class GeminiService:
    @staticmethod
    def generate_svg(
        concept: ConceptModel,
        validation_feedback: str = ""
    ) -> GenerationResultModel:
        if not AppConfig.GEMINI_API_KEY:
            raise GeminiConfigurationError("Gemini API key is not configured")
        prompt = PromptConfig.build_svg_prompt(concept, validation_feedback)
        with genai.Client(
            api_key=AppConfig.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=60000,
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        ) as client:
            response = client.models.generate_content(
                model=AppConfig.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=AppConfig.GEMINI_TEMPERATURE,
                    max_output_tokens=AppConfig.GEMINI_MAX_OUTPUT_TOKENS,
                    candidate_count=1,
                    response_mime_type="text/plain"
                )
            )
        svg = GeminiService.extract_svg(response.text or "")
        usage = response.usage_metadata
        return GenerationResultModel(
            concept_id=concept.id,
            model_name=response.model_version or None,
            svg=svg,
            token_usage=TokenUsageModel(
                input_tokens=usage.prompt_token_count if usage else None,
                output_tokens=usage.candidates_token_count if usage else None,
                thinking_tokens=usage.thoughts_token_count if usage else None,
                total_tokens=usage.total_token_count if usage else None
            )
        )

    @staticmethod
    def extract_svg(response_text: str) -> str:
        cleaned_text = re.sub(
            r"\A\s*```(?:svg|xml)?\s*|\s*```\s*\Z",
            "",
            response_text,
            flags=re.IGNORECASE
        )
        return cleaned_text.strip()
