# Primeiro incremento do fork: geometria de varejo

Este incremento corrige falhas da geração original e acrescenta um caminho explícito para validar uma proposta de loja e exportá-la em DXF. Ainda não gera uma estratégia comercial por IA nem posiciona equipamentos automaticamente. O exemplo é inteiramente sintético, criado para testar o motor; não substitui o escopo comercial do projeto.

## Executar o exemplo

Na raiz, com Python 3.12 e as dependências de `audit/requirements-audit.txt` instaladas:

```bash
PYTHONPATH=backend python -m src.retail.demo examples/retail-demo.json examples/generated
PYTHONPATH=backend python -m pytest backend/tests -q
```

Os arquivos DXF e SVG são gerados a partir das mesmas coordenadas, em metros. A origem é o canto inferior esquerdo. Neste primeiro esquema os equipamentos são retângulos alinhados aos eixos. Alturas são atributos e aparecem nas legendas. O contorno representa o limite da área, não paredes detalhadas com vãos.

O exemplo tem 12 × 10 m, entrada à direita, saída à esquerda, hortifruti baixo e visível na entrada, básicos ao fundo e caixa junto à saída. Seu ponto forte declarado é hortifruti fresco. Trata-se de uma proposta fixa para testar desenho e validação, não de uma solução ideal calculada.

## API

Inicialização: `cd backend && uvicorn src.main:app --host 127.0.0.1 --port 8000`.

- `POST /api/v1/retail/validate`: recebe o JSON do exemplo; retorna `valid`, `issues` e o alcance da validação.
- `POST /api/v1/retail/export.dxf`: retorna DXF ou HTTP 422 se houver conflito. Não grava caminhos fornecidos pelo usuário.

Validações: medidas finitas e positivas, IDs únicos, referências de entrada/saída distintas, limites do prédio, sobreposição de equipamentos, invasão das áreas livres, largura dos retângulos de circulação declarados, conexão dessa rede e altura máxima de equipamentos na área de visibilidade da entrada.

Isso não certifica acessibilidade, evacuação ou normas. A rede de circulação declarada não substitui simulação de percurso, fila de caixa ou área de operação de cada equipamento. Não há análise estrutural, mezaninos, rotação, pisos irregulares ou cálculo de iluminação. A intenção de iluminação fica explícita no JSON; não foi executado cálculo luminotécnico.

## Correções do fluxo original

- A chamada de análise usa as dimensões do dicionário corretamente.
- Otimização recebe `issues` e suas sugestões em lista são transmitidas; não são anunciadas como alterações executadas.
- Geração incompleta falha em vez de declarar sucesso.
- Nomes vazios, separadores de caminho e dimensões inválidas são rejeitados.
- Texto usa a API atual de ezdxf; limites são calculados com `bbox.extents`.
- Exportador rejeita nomes que tentam sair da pasta.

## Verificação realizada

23 testes passaram em ambiente isolado. Incluem leitura do DXF gerado, auditoria estrutural do arquivo, rejeição de conflitos, exportação HTTP e chamadas de IA com provedor simulado. O antigo `test_api.py` era um roteiro manual que dependia de um servidor já aberto; foi movido para `scripts/check_live_api.py` para não ser coletado pelo pytest. Nenhuma chave real, inferência externa ou GPU foi usada. A auditoria anterior em `audit/` continua sendo evidência do commit upstream, não um relatório de regressão desta branch.

## Próximos incrementos

1. Adaptar o esquema à impressão digital e às proporções de seções validadas pelo consultor, indicando a unidade de cada proporção (área, frente linear ou exposição).
2. Implementar posicionamento de equipamentos e teste de rotas, incluindo entrada que convida ao interior, caixas e reposição.
3. Refinar o prompt com a estratégia do consultor, e comparar várias propostas com critérios objetivos. A ponte ZeroGPU já está preparada; a implantação e chamada real ainda dependem de criar/configurar o Space.
4. Integrar o editor visual e corrigir o conflito de dependências do frontend identificado na auditoria.
5. Resolver autenticação, configuração de segredos, exclusão de arquivos e metadados antes de disponibilizar um serviço multiusuário.
6. Testar modelos e GPUs externas com métricas de qualidade, custo e latência; ainda falta uma chamada remota real.

O caminho residencial legado ainda não aplica as restrições comerciais arbitrárias de `constraints`. As novas verificações estão nos endpoints `/retail/`. Não há alegação de que o sistema todo esteja pronto para produção.

## Testar proposta com GPU Hugging Face

O protótipo agora inclui um adaptador para Space Gradio ZeroGPU, em `spaces/retail-zerogpu/`. O FastAPI chama o endpoint `/generate_layout`; ele recebe JSON atual e instruções. O backend valida novamente esquema, dimensões fixas e geometria antes de aceitar.

1. No Hugging Face, crie um Space Gradio selecionando ZeroGPU e coloque o conteúdo de `spaces/retail-zerogpu/` na raiz do Space.
2. Configure o repositório do Space, aguarde o build e teste o endpoint pela página do Space.
3. No ambiente local, instale `backend/requirements-huggingface.txt` e configure `HF_RETAIL_SPACE_ID=usuario/nome-do-space`. Para Space privado, configure `HF_TOKEN` como variável local, sem enviá-lo ao Git.
4. Inicie a API no VS Code e envie `POST /api/v1/retail/generate` com `{"layout": <conteúdo do examples/retail-demo.json>, "instructions": "Mantenha entrada e saída separadas e preserve a área do hortifruti"}`.
5. Só exporte a proposta depois da validação. O modelo pode retornar JSON malformado ou geometria inválida; nesses casos a API rejeita a resposta.

ZeroGPU exige Gradio e usa fila e cota diária. A documentação consultada informa, no momento, cinco minutos diários de GPU para conta gratuita, sujeitos a fila; isto serve para poucas chamadas de demonstração, não para serviço contínuo. O ZeroGPU do Hugging Face não é uma GPU arbitrária anexada ao FastAPI. O Space é um serviço separado e o adaptador conversa com ele via cliente Gradio. Para testar a chamada agora, crie o Space na sua conta; não publiquei um Space nem usei uma GPU remota nesta etapa.

Os layouts enviados ao Space saem da máquina local. Use apenas o exemplo sintético até definir consentimento, retenção e tratamento dos dados de lojas reais.

Fontes oficiais: [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [Gradio Python Client](https://gradio.app/docs/python-client/client) e [ZeroGPU Spaces pelo cliente](https://gradio.app/docs/python-client/using-zero-gpu-spaces).
