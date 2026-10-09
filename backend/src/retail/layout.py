"""Metric retail geometry. This validates a proposal, not building-code compliance."""
from io import StringIO
from typing import Literal

import ezdxf
from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import box


class Rectangle(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1)
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    depth: float = Field(gt=0)

    def polygon(self):
        return box(self.x, self.y, self.x + self.width, self.y + self.depth)


class Fixture(Rectangle):
    kind: Literal["gondola", "checkout", "freezer", "column", "display"]
    height: float = Field(gt=0)
    category: str = Field(min_length=1)


class RetailLayout(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: str = Field(min_length=1)
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    fixtures: list[Fixture] = Field(min_length=1)
    clear_zones: list[Rectangle] = Field(min_length=1)
    entrance_zone: str
    exit_zone: str
    minimum_clear_width: float = Field(gt=0)
    entrance_max_fixture_height: float = Field(gt=0)
    entrance_visibility_zone: Rectangle
    commercial_strength: str = Field(min_length=1)
    lighting_intent: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [x.id for x in self.fixtures + self.clear_zones]
        if len(ids) != len(set(ids)):
            raise ValueError("Fixture and zone IDs must be unique")
        if self.entrance_zone == self.exit_zone:
            raise ValueError("Entrance and exit must have separate zone IDs")
        if not {self.entrance_zone, self.exit_zone} <= {x.id for x in self.clear_zones}:
            raise ValueError("Entrance and exit must reference clear zones")
        return self


def validate_layout(layout: RetailLayout) -> list[str]:
    """Return blockers: bounds, overlap, protected circulation, entry sightlines."""
    issues = []
    boundary = box(0, 0, layout.width, layout.depth)
    for item in layout.fixtures + layout.clear_zones + [layout.entrance_visibility_zone]:
        if not boundary.covers(item.polygon()):
            issues.append(f"outside_boundary:{item.id}")
    for i, fixture in enumerate(layout.fixtures):
        for other in layout.fixtures[i + 1:]:
            if fixture.polygon().intersection(other.polygon()).area > 1e-8:
                issues.append(f"overlap:{fixture.id}:{other.id}")
        for zone in layout.clear_zones:
            if fixture.polygon().intersection(zone.polygon()).area > 1e-8:
                issues.append(f"blocked_clear_zone:{fixture.id}:{zone.id}")
        if fixture.height > layout.entrance_max_fixture_height and fixture.polygon().intersection(layout.entrance_visibility_zone.polygon()).area > 1e-8:
            issues.append(f"entry_sightline:{fixture.id}")
    for zone in layout.clear_zones:
        if min(zone.width, zone.depth) < layout.minimum_clear_width:
            issues.append(f"narrow_clear_zone:{zone.id}")
    # Require every declared circulation zone to connect to the entrance network.
    zones = {z.id: z.polygon() for z in layout.clear_zones}
    reachable = {layout.entrance_zone}
    while True:
        added = {key for key, poly in zones.items() if key not in reachable and any(poly.intersection(zones[r]).area > 1e-8 or poly.intersection(zones[r]).length >= layout.minimum_clear_width for r in reachable)}
        if not added:
            break
        reachable |= added
    for key in zones.keys() - reachable:
        issues.append(f"disconnected_clear_zone:{key}")
    return sorted(issues)


def export_dxf(layout: RetailLayout) -> str:
    issues = validate_layout(layout)
    if issues:
        raise ValueError("; ".join(issues))
    doc = ezdxf.new("R2010")
    doc.units = 6  # meters
    msp = doc.modelspace()
    for layer, color in [("BOUNDARY", 7), ("FIXTURES", 3), ("CIRCULATION", 4), ("LABELS", 7)]:
        doc.layers.new(layer, dxfattribs={"color": color})
    msp.add_lwpolyline([(0, 0), (layout.width, 0), (layout.width, layout.depth), (0, layout.depth)], close=True, dxfattribs={"layer": "BOUNDARY"})
    for item in layout.fixtures + layout.clear_zones:
        layer = "FIXTURES" if isinstance(item, Fixture) else "CIRCULATION"
        msp.add_lwpolyline(list(item.polygon().exterior.coords)[:-1], close=True, dxfattribs={"layer": layer})
        label = item.id
        if isinstance(item, Fixture):
            label += f" | {item.category} | h={item.height:g}m"
        msp.add_text(label, dxfattribs={"height": 0.18, "layer": "LABELS"}).set_placement((item.x + 0.1, item.y + 0.2))
    msp.add_text(layout.commercial_strength, dxfattribs={"height": 0.3, "layer": "LABELS"}).set_placement((0, layout.depth + 1))
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue()
