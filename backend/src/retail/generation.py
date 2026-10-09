"""Optional Hugging Face Gradio Space adapter with strict local validation."""
import json
import os
from typing import Callable

from .layout import RetailLayout, validate_layout

class SpaceUnavailable(RuntimeError):
    """Remote GPU Space is not configured or did not return a usable proposal."""


def propose_layout(layout: RetailLayout, instructions: str, client_factory: Callable | None = None) -> RetailLayout:
    space_id = os.getenv("HF_RETAIL_SPACE_ID", "").strip()
    if not space_id:
        raise SpaceUnavailable("HF_RETAIL_SPACE_ID is not configured")
    if client_factory is None:
        try:
            from gradio_client import Client
        except ImportError as exc:
            raise SpaceUnavailable("Install gradio-client to connect to the Hugging Face Space") from exc
        client_factory = Client
    token = os.getenv("HF_TOKEN")
    try:
        client = client_factory(space_id, token=token, verbose=False)
        result = client.predict(layout.model_dump_json(), instructions, api_name="/generate_layout")
        if isinstance(result, dict):
            raw = result.get("text", result.get("layout", result))
        elif isinstance(result, (list, tuple)):
            raw = result[0]
        else:
            raw = result
        if isinstance(raw, dict):
            candidate_data = raw
        elif isinstance(raw, str):
            candidate_data = json.loads(raw)
        else:
            raise ValueError("Space returned an unsupported response")
        candidate = RetailLayout.model_validate(candidate_data)
        if (candidate.width, candidate.depth) != (layout.width, layout.depth):
            raise ValueError("Proposal changed the fixed building dimensions")
        issues = validate_layout(candidate)
        if issues:
            raise ValueError("Proposal rejected by local geometry checks: " + ", ".join(issues))
        return candidate
    except SpaceUnavailable:
        raise
    except Exception as exc:
        raise ValueError(f"Hugging Face proposal could not be accepted: {exc}") from exc
