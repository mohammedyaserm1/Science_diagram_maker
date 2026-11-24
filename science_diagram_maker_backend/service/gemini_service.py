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
        validation_feedback: str = "",
        reviewer_feedback: str = ""
    ) -> GenerationResultModel:
        if not AppConfig.GEMINI_API_KEY:
            raise GeminiConfigurationError("Gemini API key is not configured")
        prompt = PromptConfig.build_svg_prompt(concept, validation_feedback, reviewer_feedback)
        model_name = AppConfig.GEMINI_MODEL
        thinking = (
            types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)
            if model_name.removeprefix("models/") in AppConfig.MINIMAL_THINKING_MODELS
            else None
        )
        with genai.Client(
            api_key=AppConfig.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                api_version=AppConfig.GEMINI_API_VERSION,
                timeout=AppConfig.GEMINI_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        ) as client:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=AppConfig.GEMINI_TEMPERATURE,
                    max_output_tokens=AppConfig.GEMINI_MAX_OUTPUT_TOKENS,
                    candidate_count=1,
                    response_mime_type="text/plain",
                    system_instruction=PromptConfig.build_system_instruction(),
                    thinking_config=thinking,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
            )
        raw_svg = response.text or ""
        usage = response.usage_metadata
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        return GenerationResultModel(
            concept_id=concept.id,
            model_name=response.model_version or None,
            svg=GeminiService.extract_svg(raw_svg),
            raw_svg=raw_svg,
            finish_reason=finish_reason.value if finish_reason else None,
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
