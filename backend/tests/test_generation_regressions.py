"""Offline regressions for the generation path audited in October 2026."""
import importlib
import numpy as np
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from src.utils import settings
    monkeypatch.setattr(settings, 'database_url', 'sqlite:///:memory:')
    monkeypatch.setattr(settings, 'output_directory', str(tmp_path / 'outputs'))
    monkeypatch.setattr(settings, 'openai_api_key', None)
    main = importlib.import_module('src.main')
    main.init_database()
    return main, TestClient(main.app)

def payload():
    return {'name':'Regression', 'dimensions':{'width':24,'height':12}, 'rooms':[{'type':'office','area':12}]}

@pytest.mark.parametrize('name', ['../escape', 'a/b', 'a\\b', '', '..'])
def test_rejects_unsafe_name(api, name):
    data = payload()
    data['name'] = name
    assert api[1].post('/api/v1/plans/generate',json=data).status_code == 422

def test_incomplete_plan_fails(api):
    data = payload()
    data['rooms'][0]['area'] = 10000
    response = api[1].post('/api/v1/plans/generate',json=data)
    response.raise_for_status()
    state = api[1].get('/api/v1/plans/' + response.json()['plan_id'] + '/status').json()
    assert state['status'] == 'failed'

def test_ai_calls_reached_and_suggestions_not_applied(api, monkeypatch):
    main, client = api
    calls = []
    class FakeAI:
        async def analyze_cad_requirements(self, text):
            calls.append('analysis')
            return {'rooms':[]}
        async def suggest_optimizations(self, layout, issues):
            calls.append('optimization')
            return [{'description':'Move fixture', 'confidence':0.99}]
    monkeypatch.setattr(main, 'OpenAIClient', FakeAI)
    monkeypatch.setattr(main.settings, 'openai_api_key', 'test-placeholder')
    np.random.seed(42)
    response = client.post('/api/v1/plans/generate',json=payload())
    response.raise_for_status()
    state = client.get('/api/v1/plans/' + response.json()['plan_id'] + '/status').json()
    assert state['status'] == 'completed'
    assert calls == ['analysis', 'optimization']
    assert state['result']['ai_optimizations_applied'] is False
