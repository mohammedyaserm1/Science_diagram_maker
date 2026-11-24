from config.app_config import AppConfig
from model.diagram_model import ConceptModel


class PromptConfig:
    CONCEPT_LAYOUT_GUIDANCE = {
        1: (
            "Draw one right triangle with a right-angle marker. Use a 180-unit "
            "vertical leg labelled 3 and a 240-unit horizontal leg labelled 4, "
            "so the sloping side labelled 5 is proportional. Show both a² + b² = c² "
            "and 3² + 4² = 5² next to the triangle. Highlight the sides or equation "
            "terms in sequence. Use at most 20 shapes and labels. Omit drawn squares."
        ),
        2: (
            "Use one unbroken circular outline with a centre dot. Draw the horizontal "
            "diameter between opposite points on that outline through the centre. "
            "Draw a vertical radius from the centre to the same outline. Label centre, "
            "radius, diameter and circumference where they cannot overlap, and state "
            "Diameter = 2 × radius. Animate the outline or feature highlights. "
            "Use at most 20 shapes and labels."
        ),
        3: (
            "Draw a single closed loop using exactly one cell and two rectangular "
            "resistor symbols. The cell has exactly two parallel plates: one long "
            "positive plate and one short negative plate. Wires meet the outer side "
            "of each plate and do not bridge the gap. Label the source Cell. Show "
            "Current is the same throughout and Vcell = V1 + V2 in short captions. "
            "Explain that the resistors share the cell voltage, and label the resistor "
            "drops V1 and V2. Pulse highlights on the loop in sequence to show the "
            "path without implying that current is used up. Use at most 30 shapes and labels."
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
