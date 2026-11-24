from config.app_config import AppConfig
from model.diagram_model import ConceptModel


class PromptConfig:
    CONCEPT_LAYOUT_GUIDANCE = {
        1: (
            "Draw a right-angle marker and a right triangle with legs 3 and 4 "
            "and hypotenuse 5. Label those sides and explain the equation using "
            "short lines. A full set of drawn squares is optional. Highlight "
            "the sides or equation terms in sequence."
        ),
        2: (
            "Use a horizontal diameter that touches both edges, a radius in a "
            "different direction, a centre dot, and a circle outline labelled "
            "Circumference. Pulse the outline or highlight the features in sequence."
        ),
        3: (
            "Draw one closed loop with one cell, represented by exactly one "
            "long plate and one short plate, and two rectangular resistor symbols. "
            "Label the source Cell. Use short captions to show current is the "
            "same throughout and the cell voltage is shared by the resistors. "
            "Animate markers along the wire in one consistent direction."
        )
    }

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
- Use a maximum font size of 24 for headings.
- Use font sizes between 12 and 18 for labels.
- Keep individual text elements under 40 characters.
- Split longer explanations into separate text elements.
- Leave at least 30 units of space from the canvas edges.
- Estimate text width as character count multiplied by font size multiplied by 0.75.
- Consider text-anchor when calculating text boundaries.

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
- Verify every rect satisfies x + width <= {width} - 30 and
  y + height <= {height} - 30, and check all label extents before returning.
- {layout_guidance}

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
            layout_guidance=PromptConfig.CONCEPT_LAYOUT_GUIDANCE.get(
                concept.id, "Keep each illustration focused on the supplied description."
            ),
            validation_feedback=validation_feedback or "First generation attempt."
        )
