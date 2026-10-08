"""Reproduce upstream findings without credentials, external inference or a server.

Run from the repository: python audit/reproduce.py
Only temporary directories receive runtime database/DXF files.
This is an audit probe: findings are observations, not passing product tests.
"""
import asyncio
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL_NAME", "API_KEY", "BASE_URL", "MODEL_NAME"):
    os.environ.pop(key, None)

result = {"upstream_commit": "4a79926ef5e154403d1724c3796004b8b37e324d", "checks": {}}
result["versions"] = {p: importlib.metadata.version(p) for p in ("ezdxf", "fastapi", "openai", "sqlalchemy", "shapely", "pydantic", "numpy", "networkx", "httpx")}
checks = result["checks"]
with tempfile.TemporaryDirectory(prefix="aicad-audit-") as temporary:
    previous = Path.cwd()
    os.chdir(temporary)
    try:
        from fastapi.testclient import TestClient
        import ezdxf
        import numpy as np
        from src import main
        from src.cad.dxf_generator import DXFGenerator

        main.settings.output_directory = str(Path(temporary) / "outputs")
        main.settings.openai_api_key = None
        client = TestClient(main.app)
        checks["health_status"] = client.get("/api/v1/health").status_code

        def generate(name, area=12, constraints=None):
            np.random.seed(42)
            response = client.post("/api/v1/plans/generate", json={
                "name": name, "dimensions": {"width": 24, "height": 12},
                "rooms": [{"type": "office", "area": area}],
                "constraints": constraints or {}, "building_type": "commercial",
            })
            response.raise_for_status()
            plan_id = response.json()["plan_id"]
            state = client.get(f"/api/v1/plans/{plan_id}/status").json()
            return plan_id, state

        plan_id, normal = generate("Audit normal")
        checks["normal_plan"] = {"status": normal["status"], "rooms_placed": normal.get("result", {}).get("rooms_placed")}
        dxf_path = Path(normal["dxf_file_path"])
        drawing = ezdxf.readfile(dxf_path)
        checks["dxf_readback"] = {"entities": len(drawing.modelspace()), "units": drawing.units, "audit_errors": len(drawing.audit().errors)}
        checks["download_status"] = client.get(f"/api/v1/plans/{plan_id}/download").status_code
        checks["preview"] = client.get(f"/api/v1/plans/{plan_id}/preview").json().get("preview_data")

        def geometry(state):
            doc = ezdxf.readfile(state["dxf_file_path"])
            return [[list(point) for point in entity.get_points("xy")] for entity in doc.modelspace().query('LWPOLYLINE[layer=="ROOMS"]')]

        _, constrained = generate("Audit constraints", constraints={"min_hallway_width": 100, "fixed_columns": [[12, 6]], "entry": [0, 0], "exit": [24, 0]})
        checks["constraints_ignored"] = {"same_room_geometry": geometry(normal) == geometry(constrained), "status": constrained["status"], "note": "Identical seed and room; impossible 100m aisle and fixed column added."}
        _, oversized = generate("Audit impossible", area=10000)
        checks["impossible_room"] = {"status": oversized["status"], "rooms_placed": oversized.get("result", {}).get("rooms_placed")}

        class FakeAI:
            analysis_calls = 0
            optimization_calls = 0
            async def analyze_cad_requirements(self, user_requirements, context=None):
                self.analysis_calls += 1
                return {"rooms": []}
            async def suggest_optimizations(self, current_layout, issues):
                self.optimization_calls += 1
                return []

        fake = FakeAI()
        original_ai = main.OpenAIClient
        main.OpenAIClient = lambda: fake
        main.settings.openai_api_key = "audit-dummy-not-a-real-key"
        try:
            _, ai_state = generate("Audit fake AI")
            checks["ai_execution"] = {"analysis_calls": fake.analysis_calls, "optimization_calls": fake.optimization_calls, "status": ai_state["status"], "ai_enabled": ai_state.get("ai_enabled"), "ai_analysis_performed": ai_state.get("result", {}).get("ai_analysis_performed")}
        finally:
            main.OpenAIClient = original_ai
            main.settings.openai_api_key = None

        _, escaped = generate("../audit-escaped")
        checks["filename_escapes_plan_folder"] = Path(escaped["dxf_file_path"]).resolve().parent != (Path(main.settings.output_directory) / escaped["id"]).resolve()
        client.delete(f"/api/v1/plans/{plan_id}").raise_for_status()
        checks["delete_leaves_dxf"] = dxf_path.exists()
        listing = client.get("/api/v1/plans").json()["plans"]
        checks["listing_metadata"] = [{"building_type": p["building_type"], "score": p["summary"]["efficiency_score"]} for p in listing]

        generator = DXFGenerator()
        generator.create_drawing("Audit helpers")
        text = generator.add_text("Test label", (2, 3))
        generator.add_wall((0, 0), (10, 0))
        checks["text_helper_returns_none"] = text is None
        checks["drawing_bounds"] = generator.get_drawing_info()["bounds"]
        try:
            main.FloorPlanRequest(name="invalid", dimensions={"width": -1, "height": 0}, rooms=[])
            checks["invalid_dimensions_accepted"] = True
        except Exception:
            checks["invalid_dimensions_accepted"] = False
        schema = client.get("/openapi.json").json()
        checks["global_auth_defined"] = bool(schema.get("security") or schema.get("components", {}).get("securitySchemes"))
        checks["legacy_key_location"] = [p["in"] for p in schema["paths"]["/api/v1/ai/configure"]["post"]["parameters"] if p["name"] == "api_key"]
    finally:
        os.chdir(previous)

destination = ROOT / "audit" / "evidence.json"
destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
