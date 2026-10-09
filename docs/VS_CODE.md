# Abrir e executar o protótipo no VS Code

Abra a pasta raiz do repositório clonado, a que contém `README.md` e `.vscode/`.

No terminal integrado, crie um ambiente e instale as dependências:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

No macOS/Linux, use `python3.12 -m venv .venv` e `source .venv/bin/activate`.

Selecione `.venv` com **Python: Select Interpreter**. As tarefas estão em **Terminal → Run Task**:

- `Varejo: testes locais`
- `Varejo: validar e exportar exemplo`
- `Varejo: iniciar API local`

Para experimentar o Space remoto, instale também `backend/requirements-huggingface.txt` e defina `HF_RETAIL_SPACE_ID`. Guarde `HF_TOKEN` apenas como variável de ambiente local, nunca em arquivo versionado. Use o endpoint `/docs` da API para enviar o JSON sintético.

A configuração de debug está em `.vscode/launch.json`. Este ambiente de execução não tem o aplicativo VS Code instalado; portanto, a pasta não foi aberta numa janela daqui. O repositório e as tarefas estão preparados para você abri-los no seu VS Code.
