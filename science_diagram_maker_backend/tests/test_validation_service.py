import pytest
from service.validation_service import ValidationService


VALID_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500">
    <title>Circle demonstration</title>
    <circle cx="200" cy="200" r="50" fill="#2563eb">
        <animate attributeName="cx"
                 values="200;300;200"
                 dur="3s"
                 repeatCount="indefinite"/>
    </circle>
    <text x="100" y="60" font-family="monospace" font-size="16">Radius</text>
    <text x="100" y="90" font-family="monospace" font-size="16">Diameter</text>
    <text x="100" y="120" font-family="monospace" font-size="16">Centre</text>
</svg>
"""


def get_check(svg: str, name: str):
    result = ValidationService.validate_svg(svg)
    return next(
        check for check in result.checks
        if check.name == name
    )


def test_valid_svg():
    result = ValidationService.validate_svg(VALID_SVG)
    assert result.passed
    assert len(result.checks) == 5
    assert all(check.passed for check in result.checks)


def test_invalid_xml():
    svg = "<svg><circle></svg>"
    assert not get_check(svg, "svg_validity").passed


def test_invalid_namespace():
    svg = VALID_SVG.replace(
        "http://www.w3.org/2000/svg",
        "http://example.com"
    )
    assert not get_check(svg, "svg_validity").passed


def test_missing_viewbox():
    svg = VALID_SVG.replace('viewBox="0 0 800 500"', "")
    assert not get_check(svg, "viewbox_bounds").passed


def test_static_shape_outside_viewbox():
    svg = VALID_SVG.replace('r="50"', 'r="300"')
    assert not get_check(svg, "viewbox_bounds").passed


def test_animated_shape_outside_viewbox():
    svg = VALID_SVG.replace("200;300;200", "200;790;200")
    assert not get_check(svg, "viewbox_bounds").passed


def test_stroke_outside_viewbox():
    svg = VALID_SVG.replace(
        'cx="200"',
        'cx="50" stroke="black" stroke-width="10"'
    )
    assert not get_check(svg, "viewbox_bounds").passed


def test_stroked_circle_can_touch_viewbox_edge():
    svg = VALID_SVG.replace(
        'cx="200"',
        'cx="55" stroke="black" stroke-width="10"'
    )
    assert get_check(svg, "viewbox_bounds").passed


@pytest.mark.parametrize("cap", ["butt", "round", "square"])
def test_supported_stroke_linecaps_pass(cap):
    line = f'<line x1="30" y1="200" x2="770" y2="200" stroke="black" stroke-width="10" stroke-linecap="{cap}"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    assert ValidationService.validate_svg(svg).passed


@pytest.mark.parametrize("cap", ["inherit", "triangle", "url(#paint)"])
def test_unsupported_stroke_linecap_is_rejected(cap):
    line = f'<line x1="40" x2="100" stroke-linecap="{cap}"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    check = get_check(svg, "security")
    assert not check.passed
    assert check.message == "Unsupported stroke-linecap value"


@pytest.mark.parametrize("cap, fits", [("butt", True), ("round", False), ("square", False)])
def test_horizontal_cap_extension_at_viewbox_edge(cap, fits):
    line = f'<line x1="50" y1="200" x2="800" y2="200" stroke="black" stroke-width="10" stroke-linecap="{cap}"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    assert get_check(svg, "viewbox_bounds").passed is fits


@pytest.mark.parametrize("cap, fits", [("round", True), ("square", False)])
def test_diagonal_square_cap_extends_beyond_round_cap(cap, fits):
    line = f'<line x1="6" y1="200" x2="26" y2="220" stroke="black" stroke-width="10" stroke-linecap="{cap}"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    assert get_check(svg, "viewbox_bounds").passed is fits


@pytest.mark.parametrize("cap, fits", [("butt", True), ("round", False), ("square", False)])
def test_zero_length_line_uses_the_cap_shape(cap, fits):
    line = f'<line x1="3" y1="200" x2="3" y2="200" stroke="black" stroke-width="10" stroke-linecap="{cap}"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    assert get_check(svg, "viewbox_bounds").passed is fits


def test_polyline_stroke_bound_includes_caps():
    polyline = '<polyline points="3,200 40,200 40,240" stroke="black" stroke-width="10" stroke-linecap="round"/>'
    svg = VALID_SVG.replace("</svg>", polyline + "</svg>")
    assert get_check(svg, "security").passed
    assert not get_check(svg, "viewbox_bounds").passed


def test_explicit_stroke_linejoin_stays_outside_allowlist():
    line = '<line x1="40" x2="100" stroke-linejoin="round"/>'
    svg = VALID_SVG.replace("</svg>", line + "</svg>")
    assert not get_check(svg, "security").passed


def test_text_outside_viewbox():
    svg = VALID_SVG.replace('x="100"', 'x="795"', 1)
    assert not get_check(svg, "viewbox_bounds").passed


def test_missing_title():
    svg = VALID_SVG.replace(
        "<title>Circle demonstration</title>",
        ""
    )
    assert not get_check(svg, "title_and_labels").passed


def test_insufficient_labels():
    svg = VALID_SVG.replace(
        '<text x="100" y="120" font-family="monospace" font-size="16">Centre</text>',
        ""
    )
    assert not get_check(svg, "title_and_labels").passed


def test_missing_animation():
    svg = VALID_SVG.replace(
        '<animate attributeName="cx"'
        '\n                 values="200;300;200"'
        '\n                 dur="3s"'
        '\n                 repeatCount="indefinite"/>',
        ""
    )
    assert not get_check(svg, "animation").passed


def test_static_animation_values():
    svg = VALID_SVG.replace("200;300;200", "200;200;200")
    assert not get_check(svg, "animation").passed


def test_invalid_animation_duration():
    svg = VALID_SVG.replace('dur="3s"', 'dur="0s"')
    assert not get_check(svg, "animation").passed


@pytest.mark.parametrize("content", [
    "<script>alert(1)</script>",
    '<image href="https://example.com/image.png"/>',
    '<foreignObject width="100" height="100"/>',
    "<style>circle { fill: red; }</style>",
    '<circle cx="50" cy="50" r="10" onload="alert(1)"/>'
])
def test_unsafe_content(content):
    svg = VALID_SVG.replace("</svg>", content + "</svg>")
    assert not get_check(svg, "security").passed


def test_external_stylesheet():
    svg = '<?xml-stylesheet href="external.css"?>' + VALID_SVG
    assert not get_check(svg, "security").passed


def test_failure_feedback():
    svg = VALID_SVG.replace(
        "<title>Circle demonstration</title>",
        ""
    )
    result = ValidationService.validate_svg(svg)
    assert not result.passed
    assert "title_and_labels" in result.get_failure_feedback()
