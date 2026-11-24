import re
from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import Element, ParseError
from config.validation_config import ValidationConfig
from model.diagram_model import (
    ValidationCheckModel,
    ValidationResultModel
)
from util.svg_util import SvgUtil
from util.svg_bounds_util import SvgBoundsUtil


class ValidationService:
    @staticmethod
    def validate_svg(svg: str) -> ValidationResultModel:
        try:
            root = ValidationService.parse_svg(svg)
        except (ValueError, ParseError, DefusedXmlException) as error:
            checks = [
                ValidationCheckModel(
                    name=name,
                    passed=False,
                    message=str(error) if name == "svg_validity"
                    else "Not evaluated because SVG parsing failed"
                )
                for name in ValidationConfig.CHECK_NAMES
            ]
            return ValidationResultModel(passed=False, checks=checks)
        validity = ValidationCheckModel(
            name="svg_validity",
            passed=True,
            message="SVG parsed successfully"
        )
        security = ValidationService.check_security(svg, root)
        bounds = (
            ValidationService.check_viewbox_bounds(root)
            if security.passed
            else ValidationCheckModel(
                name="viewbox_bounds",
                passed=False,
                message="Cannot verify bounds for unsupported or unsafe SVG"
            )
        )
        checks = [
            validity,
            bounds,
            ValidationService.check_title_and_labels(root),
            ValidationService.check_animation(root),
            security
        ]
        return ValidationResultModel(
            passed=all(check.passed for check in checks),
            checks=checks
        )

    @staticmethod
    def parse_svg(svg: str) -> Element:
        if not svg.strip():
            raise ValueError("SVG is empty")
        if len(svg) > ValidationConfig.MAX_SVG_LENGTH:
            raise ValueError("SVG exceeds the maximum permitted length")
        root = SafeET.fromstring(
            svg,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True
        )
        if SvgUtil.get_tag_name(root) != "svg":
            raise ValueError("Root element must be svg")
        if SvgUtil.get_namespace(root) != ValidationConfig.SVG_NAMESPACE:
            raise ValueError("Invalid SVG namespace")
        return root

    @staticmethod
    def check_security(svg: str, root: Element) -> ValidationCheckModel:
        try:
            if "<?" in svg:
                raise ValueError("XML processing instructions are not supported")
            for element in root.iter():
                tag = SvgUtil.get_tag_name(element)
                if SvgUtil.get_namespace(element) != ValidationConfig.SVG_NAMESPACE:
                    raise ValueError(f"Invalid namespace on {tag}")
                allowed = ValidationConfig.ALLOWED_ATTRIBUTES.get(tag)
                if allowed is None:
                    raise ValueError(f"Unsupported or unsafe element: {tag}")
                for attribute, value in element.attrib.items():
                    if attribute not in allowed:
                        raise ValueError(
                            f"Unsupported or unsafe attribute: {tag}.{attribute}"
                        )
                    if attribute in {"fill", "stroke"}:
                        if not re.fullmatch(
                            r"(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|none|black|white)",
                            value
                        ):
                            raise ValueError(f"Unsupported paint value: {value}")
                    if attribute == "font-weight" and value not in {"normal", "bold"}:
                        raise ValueError("Unsupported font weight")
                    if (
                        attribute == "stroke-linecap"
                        and value.strip() not in ValidationConfig.ALLOWED_STROKE_LINECAPS
                    ):
                        raise ValueError("Unsupported stroke-linecap value")
                for child in element:
                    child_tag = SvgUtil.get_tag_name(child)
                    if tag == "svg" and child_tag in (
                        ValidationConfig.SHAPE_TAGS | {"title"}
                    ):
                        continue
                    if tag in ValidationConfig.SHAPE_TAGS and child_tag == "animate":
                        continue
                    raise ValueError(
                        f"Unsupported nesting: {tag} contains {child_tag}"
                    )
            return ValidationCheckModel(
                name="security",
                passed=True,
                message="SVG follows the supported safe element and attribute profile"
            )
        except ValueError as error:
            return ValidationCheckModel(
                name="security",
                passed=False,
                message=str(error)
            )

    @staticmethod
    def check_viewbox_bounds(root: Element) -> ValidationCheckModel:
        try:
            left, top, right, bottom = SvgUtil.get_viewbox(root)
            for attribute in ("width", "height"):
                value = root.get(attribute)
                if value is not None and value != "100%":
                    if SvgUtil.parse_number(value) <= 0:
                        raise ValueError(f"SVG {attribute} must be positive")
            for element in root:
                tag = SvgUtil.get_tag_name(element)
                if tag not in ValidationConfig.SHAPE_TAGS:
                    continue
                x1, y1, x2, y2 = SvgBoundsUtil.get_element_bounds(element)
                if x1 < left or y1 < top or x2 > right or y2 > bottom:
                    raise ValueError(
                        f"{tag} exceeds viewBox: "
                        f"bounds=({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})"
                    )
            return ValidationCheckModel(
                name="viewbox_bounds",
                passed=True,
                message="Supported shape and animation bounds fit inside the viewBox; text bounds are estimated"
            )
        except ValueError as error:
            return ValidationCheckModel(
                name="viewbox_bounds",
                passed=False,
                message=str(error)
            )

    @staticmethod
    def check_title_and_labels(root: Element) -> ValidationCheckModel:
        titles = [
            element for element in root
            if SvgUtil.get_tag_name(element) == "title"
            and (element.text or "").strip()
        ]
        labels = []
        for element in root.iter():
            if SvgUtil.get_tag_name(element) != "text":
                continue
            if not (element.text or "").strip():
                continue
            if element.get("fill") == "none":
                continue
            try:
                if SvgUtil.get_number(element, "opacity", 1) <= 0:
                    continue
            except ValueError:
                continue
            labels.append(element)
        if not titles:
            return ValidationCheckModel(
                name="title_and_labels",
                passed=False,
                message="SVG is missing a non-empty title"
            )
        if len(labels) < ValidationConfig.MIN_TEXT_LABELS:
            return ValidationCheckModel(
                name="title_and_labels",
                passed=False,
                message=f"Expected at least 3 text labels, found {len(labels)}"
            )
        return ValidationCheckModel(
            name="title_and_labels",
            passed=True,
            message=f"Title and {len(labels)} text labels found"
        )

    @staticmethod
    def check_animation(root: Element) -> ValidationCheckModel:
        try:
            count = 0
            for parent in root.iter():
                attributes = set()
                for child in parent:
                    if SvgUtil.get_tag_name(child) != "animate":
                        continue
                    attribute = child.get("attributeName")
                    if attribute in attributes:
                        raise ValueError(
                            f"Multiple animations target the same attribute: {attribute}"
                        )
                    SvgUtil.get_animation_values(child, parent)
                    attributes.add(attribute)
                    count += 1
            if count == 0:
                raise ValueError("SVG does not contain a supported animation")
            return ValidationCheckModel(
                name="animation",
                passed=True,
                message=f"Found {count} valid SMIL animations"
            )
        except ValueError as error:
            return ValidationCheckModel(
                name="animation",
                passed=False,
                message=str(error)
            )
