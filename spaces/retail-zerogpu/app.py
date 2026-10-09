"""Hugging Face ZeroGPU experiment. The API caller validates all returned geometry."""
import json
import os

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = os.getenv("RETAIL_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
# ZeroGPU provides CUDA emulation at startup so model placement is prepared
# outside the decorated call, as required for efficient ZeroGPU allocation.
_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
).to("cuda")


@spaces.GPU(duration=120)
def generate_layout(current_layout_json: str, instructions: str) -> str:
    """Suggest a full JSON proposal. The caller must validate it before use."""
    try:
        layout = json.loads(current_layout_json)
    except json.JSONDecodeError as exc:
        raise gr.Error("O layout enviado não é JSON válido.") from exc
    if not isinstance(layout, dict) or not instructions.strip():
        raise gr.Error("Informe o layout e as instruções de revisão.")

    tokenizer, model = _tokenizer, _model
    system = (
        "Você propõe layouts de varejo. Retorne apenas um objeto JSON, sem markdown. "
        "Preserve dimensões do prédio, intenção comercial, elementos fixos e todas as chaves. "
        "Não invente medições nem alegue conformidade legal. A aplicação validará sua proposta."
    )
    user = (
        "Layout atual JSON:\n" + json.dumps(layout, ensure_ascii=False) +
        "\n\nInstrução do responsável:\n" + instructions +
        "\n\nResponda somente com o JSON completo do layout revisado."
    )
    prompt = tokenizer.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=1800, do_sample=False)
    generated = output[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True).strip()
    # Keep malformed JSON visible to the caller; it will be rejected locally.
    return text


demo = gr.Interface(
    fn=generate_layout,
    inputs=[gr.Textbox(lines=12, label="Layout atual (JSON)"), gr.Textbox(lines=3, label="Instruções")],
    outputs=gr.Textbox(lines=16, label="Proposta do modelo (validar antes de usar)"),
    api_name="generate_layout",
    title="Retail layout proposal · GPU experiment",
)

demo.launch()
