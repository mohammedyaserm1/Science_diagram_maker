import math
import re
from xml.etree.ElementTree import Element
from config.validation_config import ValidationConfig


class SvgUtil:
    @staticmethod
    def get_tag_name(element: Element) -> str:
        return element.tag.split("}")[-1]

    @staticmethod
    def get_namespace(element: Element) -> str:
        if element.tag.startswith("{"):
            return element.tag.split("}")[0][1:]
        return ""

    @staticmethod
    def parse_number(value: str) -> float:
        if not re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
            value.strip()
        ):
            raise ValueError(f"Invalid numeric value: {value}")
        number = float(value)
        if not math.isfinite(number) or abs(number) > 1000000:
            raise ValueError(f"Unsupported numeric value: {value}")
        return number

    @staticmethod
    def get_number(
        element: Element,
        attribute: str,
        default: float | None = None
    ) -> float:
        value = element.get(attribute)
        if value is None and default is not None:
            return default
        if value is None:
            raise ValueError(
                f"{SvgUtil.get_tag_name(element)} is missing {attribute}"
            )
        return SvgUtil.parse_number(value)

    @staticmethod
    def parse_numbers(value: str) -> list[float]:
        parts = re.split(r"[\s,]+", value.strip())
        return [SvgUtil.parse_number(part) for part in parts]

    @staticmethod
    def get_viewbox(root: Element) -> tuple[float, float, float, float]:
        viewbox = root.get("viewBox")
        if not viewbox:
            raise ValueError("SVG is missing its viewBox")
        values = SvgUtil.parse_numbers(viewbox)
        if len(values) != 4:
            raise ValueError("viewBox must contain exactly 4 numbers")
        x, y, width, height = values
        if width <= 0 or height <= 0:
            raise ValueError("viewBox dimensions must be positive")
        return x, y, x + width, y + height

    @staticmethod
    def get_animation_values(
        animation: Element,
        parent: Element
    ) -> list[float]:
        attribute = animation.get("attributeName", "")
        parent_tag = SvgUtil.get_tag_name(parent)
        if attribute not in ValidationConfig.ALLOWED_ANIMATION_ATTRIBUTES:
            raise ValueError(f"Unsupported animation attribute: {attribute}")
        if attribute in {"cx", "cy"} and parent_tag != "circle":
            raise ValueError(f"{attribute} animation requires a circle")
        if parent_tag not in ValidationConfig.SHAPE_TAGS:
            raise ValueError("Animation must belong to a graphical element")
        duration = animation.get("dur", "")
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s)", duration)
        if not match or SvgUtil.parse_number(match.group(1)) <= 0:
            raise ValueError("Animation must have a positive duration")
        repeat = animation.get("repeatCount", "1")
        if repeat != "indefinite" and SvgUtil.parse_number(repeat) <= 0:
            raise ValueError("Animation repeatCount must be positive")
        values = animation.get("values")
        if values is not None:
            if animation.get("from") is not None or animation.get("to") is not None:
                raise ValueError("Use values or from/to, not both")
            numbers = [
                SvgUtil.parse_number(value)
                for value in values.split(";")
            ]
        else:
            start = animation.get("from")
            end = animation.get("to")
            if start is None or end is None:
                raise ValueError("Animation requires values or from/to")
            numbers = [
                SvgUtil.parse_number(start),
                SvgUtil.parse_number(end)
            ]
        if len(numbers) < 2 or len(set(numbers)) < 2:
            raise ValueError("Animation must contain a changing value")
        if attribute == "opacity" and any(
            value < 0 or value > 1 for value in numbers
        ):
            raise ValueError("Animated opacity must be between 0 and 1")
        return numbers