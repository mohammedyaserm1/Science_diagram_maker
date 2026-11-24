from pydantic import BaseModel


class ConceptModel(BaseModel):
    id: int
    name: str
    subject: str
    description: str


class TokenUsageModel(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    total_tokens: int | None = None


class GenerationResultModel(BaseModel):
    concept_id: int
    model_name: str | None
    svg: str
    token_usage: TokenUsageModel


class ValidationCheckModel(BaseModel):
    name: str
    passed: bool
    message: str


class ValidationResultModel(BaseModel):
    passed: bool
    checks: list[ValidationCheckModel]

    def get_failure_feedback(self) -> str:
        return "\n".join(
            f"{check.name}: {check.message}"
            for check in self.checks
            if not check.passed
        )


class RetryModel(BaseModel):
    api_retries: int = 0
    validation_retries: int = 0
    total_retries: int = 0


class GenerationAttemptModel(BaseModel):
    attempt_number: int
    token_usage: TokenUsageModel
    validation: ValidationResultModel
    estimated_cost_usd: float | None
    reported_model_name: str | None = None


class DiagramResultModel(BaseModel):
    concept: ConceptModel
    model_name: str
    svg: str | None = None
    passed: bool
    validation: ValidationResultModel
    token_usage: TokenUsageModel
    retries: RetryModel
    estimated_cost_usd: float | None
    attempts: list[GenerationAttemptModel]
    generated_at: str
    error: str | None = None
    error_status: int | None = None
    requested_model_name: str | None = None
    reported_model_name: str | None = None
