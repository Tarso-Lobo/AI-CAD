import json
from io import StringIO
from pathlib import Path

import ezdxf
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from src.retail.layout import RetailLayout, validate_layout, export_dxf
from src.retail.generation import propose_layout, SpaceUnavailable
from src.retail.routes import router
from src.cad.dxf_generator import DXFGenerator

@pytest.fixture
def data():
    return json.loads((Path(__file__).resolve().parents[2] / 'examples/retail-demo.json').read_text())

def test_valid_export_roundtrip(data):
    layout = RetailLayout(**data)
    assert validate_layout(layout) == []
    doc = ezdxf.read(StringIO(export_dxf(layout)))
    assert doc.units == 6
    assert not doc.audit().errors
    assert len(doc.modelspace().query('LWPOLYLINE')) == 9

@pytest.mark.parametrize('change,expected', [
    ({'x':11}, 'outside_boundary'),
    ({'x':10}, 'blocked_clear_zone'),
    ({'height':2}, 'entry_sightline'),
    ({'x':7.5,'y':5}, 'overlap'),
])
def test_invalid_geometry_blocks_export(data, change, expected):
    data['fixtures'][0].update(change)
    layout = RetailLayout(**data)
    assert any(x.startswith(expected) for x in validate_layout(layout))
    with pytest.raises(ValueError):
        export_dxf(layout)

def test_bad_dimensions_and_duplicate_ids(data):
    data['width'] = -1
    with pytest.raises(ValidationError):
        RetailLayout(**data)
    data['width'] = 12
    data['fixtures'][0]['id'] = 'entrada'
    with pytest.raises(ValidationError):
        RetailLayout(**data)

def test_disconnected_route(data):
    data['clear_zones'][1].update(x=0, width=2)
    assert any(x.startswith('disconnected_clear_zone') for x in validate_layout(RetailLayout(**data)))

def test_http_export_rejects_blocked_entrance(data):
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.post('/api/v1/retail/export.dxf',json=data).status_code == 200
    data['fixtures'][0]['x'] = 10
    assert client.post('/api/v1/retail/export.dxf',json=data).status_code == 422

def test_dxf_text_bounds_and_path(tmp_path):
    generator = DXFGenerator()
    generator.create_drawing('test')
    assert generator.add_text('test', (4, 5)) is not None
    assert generator.get_drawing_info()['bounds']['max_x'] > 4
    assert not generator.save_drawing('../escape.dxf', str(tmp_path))
    assert not (tmp_path.parent / 'escape.dxf').exists()


def test_remote_proposal_is_revalidated(data, monkeypatch):
    layout = RetailLayout(**data)
    monkeypatch.setenv("HF_RETAIL_SPACE_ID", "demo/retail-layout-gpu")
    class FakeClient:
        def __init__(self, space, **kwargs):
            assert space == "demo/retail-layout-gpu"
        def predict(self, current, instructions, api_name):
            assert api_name == "/generate_layout"
            return current
    assert propose_layout(layout, "preserve", FakeClient) == layout


def test_remote_proposal_rejects_changed_dimensions(data, monkeypatch):
    layout = RetailLayout(**data)
    monkeypatch.setenv("HF_RETAIL_SPACE_ID", "demo/retail-layout-gpu")
    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def predict(self, current, instructions, api_name):
            proposed = json.loads(current)
            proposed["width"] = 18
            return json.dumps(proposed)
    with pytest.raises(ValueError, match="fixed building dimensions"):
        propose_layout(layout, "change dimensions", FakeClient)


def test_missing_remote_configuration_returns_clear_error(data, monkeypatch):
    monkeypatch.delenv("HF_RETAIL_SPACE_ID", raising=False)
    with pytest.raises(SpaceUnavailable, match="not configured"):
        propose_layout(RetailLayout(**data), "test")

def test_generate_endpoint_reports_unconfigured_space(data, monkeypatch):
    from src.retail import routes
    monkeypatch.delenv('HF_RETAIL_SPACE_ID', raising=False)
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post('/api/v1/retail/generate', json={
        'layout': data,
        'instructions': 'Preserve dimensions and separate entry and exit',
    })
    assert response.status_code == 503
