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
    def get_line_bounds(element: Element) -> tuple:
        x1 = SvgUtil.get_number(element, "x1", 0)
        y1 = SvgUtil.get_number(element, "y1", 0)
        x2 = SvgUtil.get_number(element, "x2", 0)
        y2 = SvgUtil.get_number(element, "y2", 0)
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

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
        width = len(text) * font_size * 1.1
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
            "line": SvgBoundsUtil.get_line_bounds,
            "polygon": SvgBoundsUtil.get_polygon_bounds,
            "polyline": SvgBoundsUtil.get_polygon_bounds,
            "text": SvgBoundsUtil.get_text_bounds
        }
        handler = handlers.get(tag)
        if handler is None:
            raise ValueError(f"Unsupported graphical element: {tag}")
        bounds = handler(element)
        opacity = SvgUtil.get_number(element, "opacity", 1)
        if opacity < 0 or opacity > 1:
            raise ValueError("Opacity must be between 0 and 1")
        stroke_width = SvgUtil.get_number(element, "stroke-width", 1)
        if stroke_width < 0:
            raise ValueError("Stroke width cannot be negative")
        if element.get("stroke", "none") == "none":
            return bounds
        padding = stroke_width * 2
        left, top, right, bottom = bounds
        return (
            left - padding,
            top - padding,
            right + padding,
            bottom + padding
        )