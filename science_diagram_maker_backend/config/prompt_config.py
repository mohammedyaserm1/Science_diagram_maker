
from config.app_config import AppConfig


class PromptConfig:
    SVG_GENERATION_PROMPT = """
You are an expert educational SVG illustrator specializing in UK GCSE science and mathematics.

Generate one scientifically accurate animated SVG diagram for the concept below.

Concept: {concept_name}
Subject: {subject}
Description: {description}

Requirements:

1. Return only raw SVG markup.
2. Do not return Markdown, explanations or code fences.
3. Use the SVG namespace http://www.w3.org/2000/svg.
4. Use viewBox="0 0 {width} {height}".
5. Include a meaningful title element.
6. Include at least three visible and meaningful text labels.
7. Include at least one meaningful SMIL animation.
8. Ensure all graphical elements, strokes, labels and animated positions remain within the viewBox.
9. Maintain accurate scientific and mathematical relationships.
10. Use a clean educational illustration style.
11. Use readable font sizes and sufficient colour contrast.
12. Avoid overlapping labels and graphical elements.
13. Do not use JavaScript, scripts, event handlers or external resources.
14. Do not use foreignObject, external images, CSS imports or external fonts.
15. Use simple SVG shapes and paths with explicit numeric coordinates.
16. Avoid unnecessary nested groups and complex transformations.
17. Make the animation educational rather than purely decorative.
18. Keep the SVG concise without sacrificing educational clarity.
19. Leave sufficient padding between all content and the canvas boundaries.
20. Use a complete, well-formed SVG document.

Canvas dimensions: {width} by {height}.

Validation feedback from the previous attempt:
{validation_feedback}

Return only the complete SVG markup.
"""

    @staticmethod
    def build_svg_prompt(concept, validation_feedback: str = "") -> str:
        return PromptConfig.SVG_GENERATION_PROMPT.format(
            concept_name=concept.name,
            subject=concept.subject,
            description=concept.description,
            width=AppConfig.SVG_WIDTH,
            height=AppConfig.SVG_HEIGHT,
            validation_feedback=validation_feedback or "First generation attempt."
        )