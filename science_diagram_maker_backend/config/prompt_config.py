from config.app_config import AppConfig
from model.diagram_model import ConceptModel


class PromptConfig:
    SVG_GENERATION_PROMPT = """
You are an expert educational SVG illustrator specializing in UK GCSE
science and mathematics.

Generate one scientifically accurate animated SVG diagram.

Concept: {concept_name}
Subject: {subject}
Description: {description}

Output requirements:

1. Return only complete raw SVG markup, without Markdown or explanations.
2. Use xmlns="http://www.w3.org/2000/svg".
3. Use viewBox="0 0 {width} {height}".
4. Include a meaningful non-empty title element.
5. Include at least three visible educational text labels.
6. Include at least one meaningful SMIL animate element.
7. Keep all shapes, strokes, labels and animated positions inside the viewBox.

Supported SVG elements:
svg, title, rect, circle, ellipse, line, polygon, polyline, text, animate.

Supported attributes:
- svg: viewBox, width, height.
- rect: x, y, width, height, rx, ry.
- circle: cx, cy, r.
- ellipse: cx, cy, rx, ry.
- line: x1, y1, x2, y2.
- polygon and polyline: points.
- Shapes: fill, stroke, stroke-width, opacity.
- text: x, y, font-size, font-family, text-anchor, font-weight, fill, opacity.
- animate: attributeName, from, to, values, dur, repeatCount.

Strict restrictions:

- Place shapes and text directly inside the root SVG.
- Place animate elements inside the graphical elements they animate.
- Do not use groups, paths, transforms, scripts, styles, CSS classes,
  external images, links, foreignObject or event handlers.
- Do not use IDs, CSS, gradients, filters, markers or additional attributes.
- Do not include XML declarations or processing instructions.
- Use explicit numeric coordinates and font sizes without units.
- Use only three-digit or six-digit hexadecimal colours, black, white or none.
- Use font-family="monospace" for every text element.
- Use normal or bold font weights.
- Keep text labels short and give them generous space.
- Use text-anchor="middle" where suitable.
- Leave generous space around strokes and moving elements.

Animation requirements:

- Animate opacity on graphical elements or cx and cy on circles.
- Use values or from/to attributes, not both.
- Separate animation values using semicolons.
- Use positive durations such as 2s or 4s.
- Use repeatCount="indefinite" for continuous animations.
- Do not animate the same attribute twice on one element.
- Animation values must actually change.
- Opacity values must be between 0 and 1.
- Ensure every animated position remains inside the viewBox.

Educational requirements:

- Preserve the scientific meaning of the supplied description.
- Use meaningful animations rather than decorative movement.
- Use clear visual hierarchy, readable text and strong colour contrast.
- Avoid overlapping labels and shapes.
- Use simple shapes to create a polished educational illustration.

Validation feedback:
{validation_feedback}

Return only the complete SVG markup.
"""

    @staticmethod
    def build_svg_prompt(
        concept: ConceptModel,
        validation_feedback: str = ""
    ) -> str:
        return PromptConfig.SVG_GENERATION_PROMPT.format(
            concept_name=concept.name,
            subject=concept.subject,
            description=concept.description,
            width=AppConfig.SVG_WIDTH,
            height=AppConfig.SVG_HEIGHT,
            validation_feedback=validation_feedback or "First generation attempt."
        )