class ValidationConfig:
    SVG_NAMESPACE = "http://www.w3.org/2000/svg"
    MAX_SVG_LENGTH = 100000
    MIN_TEXT_LABELS = 3

    SHAPE_TAGS = {
        "rect",
        "circle",
        "ellipse",
        "line",
        "polygon",
        "polyline",
        "text"
    }

    COMMON_ATTRIBUTES = {
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "opacity"
    }

    ALLOWED_STROKE_LINECAPS = {"butt", "round", "square"}

    ALLOWED_ATTRIBUTES = {
        "svg": {"viewBox", "width", "height"},
        "title": set(),
        "rect": {
            "x", "y", "width", "height", "rx", "ry"
        } | COMMON_ATTRIBUTES,
        "circle": {
            "cx", "cy", "r"
        } | COMMON_ATTRIBUTES,
        "ellipse": {
            "cx", "cy", "rx", "ry"
        } | COMMON_ATTRIBUTES,
        "line": {
            "x1", "y1", "x2", "y2"
        } | COMMON_ATTRIBUTES,
        "polygon": {"points"} | COMMON_ATTRIBUTES,
        "polyline": {"points"} | COMMON_ATTRIBUTES,
        "text": {
            "x", "y", "font-size", "font-family",
            "text-anchor", "font-weight", "fill", "opacity"
        },
        "animate": {
            "attributeName", "from", "to", "values",
            "dur", "repeatCount"
        }
    }

    ALLOWED_ANIMATION_ATTRIBUTES = {
        "opacity",
        "cx",
        "cy"
    }

    CHECK_NAMES = (
        "svg_validity",
        "viewbox_bounds",
        "title_and_labels",
        "animation",
        "security"
    )
