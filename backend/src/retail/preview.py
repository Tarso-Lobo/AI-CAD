"""Deterministic SVG preview of the declared metric geometry."""

from xml.etree import ElementTree as ET

from .layout import RetailLayout, validate_layout

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def export_svg(layout: RetailLayout) -> str:
    """Render metric rectangles with a bottom-left origin and readable labels."""
    issues = validate_layout(layout)
    if issues:
        raise ValueError("; ".join(issues))
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": f"-1 -2 {layout.width + 2:g} {layout.depth + 4:g}",
            "width": "960",
            "height": f"{960 * (layout.depth + 4) / (layout.width + 2):g}",
            "role": "img",
            "aria-labelledby": "title description",
        },
    )

    def node(parent, tag, attributes=None, text=None):
        element = ET.SubElement(parent, f"{{{SVG_NS}}}{tag}", attributes or {})
        element.text = text
        return element

    node(root, "title", {"id": "title"}, layout.name)
    node(
        root,
        "desc",
        {"id": "description"},
        "Dados declarados em metros; origem inferior esquerda. "
        "Somente geometria declarada: percurso e adequação técnica pendentes.",
    )
    node(
        root,
        "rect",
        {
            "x": "-1",
            "y": "-2",
            "width": f"{layout.width + 2:g}",
            "height": f"{layout.depth + 4:g}",
            "fill": "#ffffff",
        },
    )
    geometry = node(
        root,
        "g",
        {
            "id": "metric-geometry",
            "transform": f"translate(0 {layout.depth:g}) scale(1 -1)",
            "stroke-width": "0.035",
        },
    )

    def rectangle(item_id, x, y, width, depth, fill, stroke):
        node(
            geometry,
            "rect",
            {
                "id": item_id,
                "x": str(x),
                "y": str(y),
                "width": str(width),
                "height": str(depth),
                "fill": fill,
                "stroke": stroke,
            },
        )

    rectangle("boundary", 0, 0, layout.width, layout.depth, "none", "#18354c")
    for zone in layout.clear_zones:
        rectangle(
            f"zone-{zone.id}",
            zone.x,
            zone.y,
            zone.width,
            zone.depth,
            "#e3f3f7",
            "#6595a4",
        )
    for fixture in layout.fixtures:
        rectangle(
            f"fixture-{fixture.id}",
            fixture.x,
            fixture.y,
            fixture.width,
            fixture.depth,
            "#e7edc6",
            "#5d7130",
        )

    labels = node(
        root, "g", {"font-family": "sans-serif", "font-size": "0.18", "fill": "#18354c"}
    )
    node(labels, "text", {"x": "0", "y": "-1.25", "font-size": "0.3"}, layout.name)
    node(
        labels,
        "text",
        {"x": "0", "y": "-0.8"},
        f"{layout.width:g} × {layout.depth:g} m | origem (0,0): inferior esquerda",
    )
    node(
        labels,
        "text",
        {"x": "0", "y": "-0.4"},
        "Azul: áreas livres declaradas | Verde: equipamentos",
    )
    for fixture in layout.fixtures:
        for index, line in enumerate(
            (fixture.id, fixture.category, f"h={fixture.height:g} m")
        ):
            node(
                labels,
                "text",
                {
                    "x": str(fixture.x + 0.1),
                    "y": str(
                        layout.depth - fixture.y - fixture.depth + 0.35 + index * 0.28
                    ),
                },
                line,
            )
    for zone in layout.clear_zones:
        label = zone.id
        if zone.id == layout.entrance_zone:
            label += " (entrada declarada)"
        elif zone.id == layout.exit_zone:
            label += " (saída declarada)"
        node(
            labels,
            "text",
            {"x": str(zone.x + 0.1), "y": str(layout.depth - zone.y - 0.25)},
            label,
        )
    node(
        labels,
        "text",
        {"x": "0", "y": str(layout.depth + 0.5)},
        "Geometria declarada verificada; inventário, acessos físicos e percurso pendentes.",
    )
    node(
        labels,
        "text",
        {"x": "0", "y": str(layout.depth + 0.9)},
        "Intenções comerciais e de iluminação não foram calculadas ou aprovadas.",
    )
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
