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
    model_name: str
    svg: str
    token_usage: TokenUsageModel