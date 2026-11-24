from math import hypot
from xml.etree.ElementTree import Element
from util.svg_util import SvgUtil


class SvgBoundsUtil:
    @staticmethod
    def get_rect_bounds(element: Element) -> tuple:
        x = SvgUtil.get_number(element, "x", 0)
        y = SvgUtil.get_number(element, "y", 0)
        width = SvgUtil.get_number(element, "width")
        height = SvgUtil.get_number(element, "height")
        if width <= 0 or height <= 0:
            raise ValueError("Rectangle dimensions must be positive")
        for attribute in ("rx", "ry"):
            if SvgUtil.get_number(element, attribute, 0) < 0:
                raise ValueError("Rectangle corner radius cannot be negative")
        return x, y, x + width, y + height

    @staticmethod
    def get_circle_bounds(element: Element) -> tuple:
        cx = SvgUtil.get_number(element, "cx", 0)
        cy = SvgUtil.get_number(element, "cy", 0)
        radius = SvgUtil.get_number(element, "r")
        if radius <= 0:
            raise ValueError("Circle radius must be positive")
        x_positions = [cx]
        y_positions = [cy]
        for animation in element:
            if SvgUtil.get_tag_name(animation) != "animate":
                continue
            values = SvgUtil.get_animation_values(animation, element)
            if animation.get("attributeName") == "cx":
                x_positions.extend(values)
            if animation.get("attributeName") == "cy":
                y_positions.extend(values)
        return (
            min(x_positions) - radius,
            min(y_positions) - radius,
            max(x_positions) + radius,
            max(y_positions) + radius
        )

    @staticmethod
    def get_ellipse_bounds(element: Element) -> tuple:
        cx = SvgUtil.get_number(element, "cx", 0)
        cy = SvgUtil.get_number(element, "cy", 0)
        rx = SvgUtil.get_number(element, "rx")
        ry = SvgUtil.get_number(element, "ry")
        if rx <= 0 or ry <= 0:
            raise ValueError("Ellipse radii must be positive")
        return cx - rx, cy - ry, cx + rx, cy + ry

    @staticmethod
    def get_line_bounds(element: Element, stroke_width: float = 0) -> tuple:
        x1 = SvgUtil.get_number(element, "x1", 0)
        y1 = SvgUtil.get_number(element, "y1", 0)
        x2 = SvgUtil.get_number(element, "x2", 0)
        y2 = SvgUtil.get_number(element, "y2", 0)
        half_width = stroke_width / 2
        cap = element.get("stroke-linecap", "butt").strip()
        delta_x = abs(x2 - x1)
        delta_y = abs(y2 - y1)
        length = hypot(delta_x, delta_y)
        if cap == "round" or (length == 0 and cap == "square"):
            pad_x = pad_y = half_width
        elif length == 0:
            pad_x = pad_y = 0
        else:
            # The stroke extends perpendicular to the line. Square caps extend along it as well.
            unit_x = delta_x / length
            unit_y = delta_y / length
            pad_x = half_width * unit_y
            pad_y = half_width * unit_x
            if cap == "square":
                pad_x += half_width * unit_x
                pad_y += half_width * unit_y
        return (
            min(x1, x2) - pad_x, min(y1, y2) - pad_y,
            max(x1, x2) + pad_x, max(y1, y2) + pad_y
        )

    @staticmethod
    def get_polygon_bounds(element: Element) -> tuple:
        points = SvgUtil.parse_numbers(element.get("points", ""))
        minimum = 6 if SvgUtil.get_tag_name(element) == "polygon" else 4
        if len(points) < minimum or len(points) % 2 != 0:
            raise ValueError("Invalid polygon or polyline coordinates")
        x_positions = points[::2]
        y_positions = points[1::2]
        return (
            min(x_positions),
            min(y_positions),
            max(x_positions),
            max(y_positions)
        )

    @staticmethod
    def get_text_bounds(element: Element) -> tuple:
        x = SvgUtil.get_number(element, "x")
        y = SvgUtil.get_number(element, "y")
        font_size = SvgUtil.get_number(element, "font-size")
        if font_size <= 0:
            raise ValueError("Font size must be positive")
        if element.get("font-family") != "monospace":
            raise ValueError("Text must explicitly use a monospace font")
        text = " ".join((element.text or "").split())
        width = len(text) * font_size * 0.75
        anchor = element.get("text-anchor", "start")
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        elif anchor != "start":
            raise ValueError(f"Unsupported text-anchor: {anchor}")
        padding = font_size * 0.25
        return (
            x - padding,
            y - font_size * 1.3,
            x + width + padding,
            y + font_size * 0.5
        )

    @staticmethod
    def get_element_bounds(element: Element) -> tuple:
        tag = SvgUtil.get_tag_name(element)
        handlers = {
            "rect": SvgBoundsUtil.get_rect_bounds,
            "circle": SvgBoundsUtil.get_circle_bounds,
            "ellipse": SvgBoundsUtil.get_ellipse_bounds,
            "polygon": SvgBoundsUtil.get_polygon_bounds,
            "polyline": SvgBoundsUtil.get_polygon_bounds,
            "text": SvgBoundsUtil.get_text_bounds
        }
        opacity = SvgUtil.get_number(element, "opacity", 1)
        if opacity < 0 or opacity > 1:
            raise ValueError("Opacity must be between 0 and 1")
        stroke_width = SvgUtil.get_number(element, "stroke-width", 1)
        if stroke_width < 0:
            raise ValueError("Stroke width cannot be negative")
        has_stroke = element.get("stroke", "none") != "none"
        if tag == "line":
            return SvgBoundsUtil.get_line_bounds(element, stroke_width if has_stroke else 0)
        handler = handlers.get(tag)
        if handler is None:
            raise ValueError(f"Unsupported graphical element: {tag}")
        bounds = handler(element)
        if not has_stroke:
            return bounds
        # Four half-widths bound default miter joins as well as all permitted endpoint caps.
        padding = stroke_width * (2 if tag in {"polygon", "polyline"} else 0.5)
        left, top, right, bottom = bounds
        return (
            left - padding,
            top - padding,
            right + padding,
            bottom + padding
        )
