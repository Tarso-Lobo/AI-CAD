# Primeiro incremento do fork: geometria de varejo

Este incremento corrige falhas da geração original e acrescenta um caminho explícito para validar uma proposta de loja e exportá-la em DXF. Ainda não gera uma estratégia comercial por IA nem posiciona equipamentos automaticamente. O exemplo é inteiramente sintético, criado para testar o motor; não substitui o escopo comercial do projeto.

## Executar o exemplo

O incremento I0 implementa `src.retail.demo`. Na raiz, crie um ambiente com Python 3.12 e instale o perfil de dependências existente:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r audit/requirements-audit.txt
PYTHONPATH=backend python -m src.retail.demo examples/retail-demo.json examples/generated
PYTHONPATH=backend python -m pytest backend/tests -q
```

No Windows, use a tarefa **Varejo: validar e exportar exemplo** do VS Code após ativar o ambiente; ela configura `PYTHONPATH`. O diretório de saída deve ser novo ou vazio. Para repetir, escolha outro diretório ou remova somente as saídas anteriores que não deseja preservar. O comando falha com código 1 para arquivo ausente, JSON/esquema inválido ou conflito geométrico; não exporta nesses casos e não sobrescreve saídas existentes.

Saídas: `retail-layout.dxf`, `retail-layout.svg` e `validation.json`. O relatório lista verificações executadas e pendências, com escopo `declared_geometry_only`. A origem dos dados de entrada não é verificada pelo comando; intenções comerciais e de iluminação permanecem declaradas. Nenhuma credencial, servidor ou cliente remoto é necessário. O perfil de auditoria instala dependências adicionais para executar a suíte do backend, mas não é um lock completo de produção.

Os arquivos DXF e SVG são gerados a partir das mesmas coordenadas, em metros. A origem é o canto inferior esquerdo. Neste primeiro esquema os equipamentos são retângulos alinhados aos eixos. Alturas são atributos e aparecem nas legendas. O contorno representa o limite da área, não paredes detalhadas com vãos.

O exemplo tem 12 × 10 m, entrada à direita, saída à esquerda, hortifruti baixo e visível na entrada, básicos ao fundo e caixa junto à saída. Seu ponto forte declarado é hortifruti fresco. Trata-se de uma proposta fixa para testar desenho e validação, não de uma solução ideal calculada.

## API

Inicialização: `cd backend && uvicorn src.main:app --host 127.0.0.1 --port 8000`.

- `POST /api/v1/retail/validate`: recebe o JSON do exemplo; retorna `valid`, `issues` e o alcance da validação.
- `POST /api/v1/retail/export.dxf`: retorna DXF ou HTTP 422 se houver conflito. Não grava caminhos fornecidos pelo usuário.

Validações: medidas finitas e positivas, IDs únicos, referências de entrada/saída distintas, limites do prédio, sobreposição de equipamentos, invasão das áreas livres, largura dos retângulos de circulação declarados, conexão dessa rede e altura máxima de equipamentos na área de visibilidade da entrada.

**Limites reproduzidos em 09/10/2026:** IDs distintos não impedem entrada e saída coincidentes; sobreposição mínima entre zonas pode ser aceita mesmo quando não comporta a largura declarada. Não há entidade de abertura física no limite do prédio. O adaptador de propostas verifica dimensões externas e geometria da resposta, mas não protege inventário obrigatório ou geometria de elementos fixos por comparação com a entrada. Portanto, `valid: true` significa somente aprovação pelas verificações limitadas existentes. Não comprova fidelidade de inventário, percurso ou adequação comercial.

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

A ordem operacional desta lista histórica foi refinada no [repasse ao desenvolvimento](RETAIL_HANDOFF.md): I0, demonstração local reproduzível; I1, proteção de inventário/acessos e conexões de circulação; I2, percurso visual revisável. Proporções comerciais e integração remota não bloqueiam esses incrementos.

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

As cotas citadas acima são registro da consulta anterior, não foram reconfirmadas neste repasse e precisam ser verificadas quando houver teste remoto. O próximo desenvolvimento é local; ZeroGPU permanece opcional.


### Situação da implantação Hugging Face (2026-10-09)

- O diretório `spaces/retail-zerogpu/` contém uma aplicação Gradio configurada para ZeroGPU e o modelo `Qwen/Qwen2.5-1.5B-Instruct`; o adaptador do backend está implementado. Isso é preparação versionada, não uma implantação concluída.
- Tentamos abrir a criação do Space e autenticar na conta Hugging Face. Após o envio seguro do formulário, o site respondeu `403 ERROR` do CloudFront (“The request could not be satisfied”). A autenticação não foi confirmada e não repetimos tentativas.
- Portanto, nenhum Space foi criado ou configurado: ainda não há proprietário/ID, URL, visibilidade, segredo configurado ou build remoto. Nenhuma inferência ZeroGPU foi executada. O próximo passo de implantação depende de o Hugging Face voltar a permitir o acesso; depois disso, registrar aqui o ID e a visibilidade escolhida, configuração sem valores secretos, resultado do build e testes remotos.
- Nenhuma senha, token ou dado real de loja foi adicionado ao repositório.

## Registro obrigatório de alterações e testes

Toda alteração nova nesta linha de trabalho, em qualquer branch, deve atualizar as especificações do projeto no mesmo conjunto de mudanças. Registre a data, o comportamento ou decisão alterada, os arquivos/partes afetados, o motivo e os casos de teste executados com seus resultados. Se um teste não se aplicar ou não puder ser executado, declare isso e o motivo. Diferencie testes locais, simulados e remotos; nunca descreva uma integração externa como testada quando só foi preparada. Atualize também a seção funcional pertinente (por exemplo, API, escopo ou implantação) para que a especificação continue refletindo o estado atual, e não apenas acrescente um histórico sem contexto.

### Registro desta atualização (2026-10-09)

- **Alteração:** documentado o protótipo ZeroGPU como preparado, o bloqueio de autenticação 403 e o estado ainda não implantado; estabelecida a regra de registrar mudanças e testes nas especificações independentemente da branch.
- **Verificações:** inspeção do formulário e do estado visível do Hugging Face; tentativa de autenticação por fluxo seguro; resposta visível 403 CloudFront. A autenticação e a implantação não foram verificadas com sucesso.
- **Testes de software:** a execução anterior desta branch registrou 23 testes passando, incluindo cliente Gradio simulado e validação local. Esses testes não incluem chamada remota nem uso de GPU. Nenhuma nova suíte foi executada nesta atualização, que altera documentação.


### Auditoria do conector Hugging Face (2026-10-09)

- **Acesso confirmado:** o conector autenticou como `@Tarso-Lobo`; a consulta de metadados do modelo `Qwen/Qwen2.5-1.5B-Instruct` funcionou. O contexto de autorização informou os escopos `read-repos` e `jobs`, além dos escopos de identidade.
- **Limite de escrita:** as ferramentas Hugging Face disponíveis nesta sessão oferecem identidade, busca/leitura de modelos, datasets, Spaces e documentação. Não há ferramenta exposta para criar um Space, enviar/alterar arquivos de Space ou editar configurações/segredos. Os escopos observados também não incluem escrita de repositórios. Portanto, o conector não permite concluir a implantação por conta própria nesta configuração.
- **Jobs:** a chamada de consulta de Jobs foi tentada, mas o servidor retornou `UNAVAILABLE` (“hf_jobs was not returned by tools/list”). Nenhum Job foi criado. O comando local `hf` também não está instalado neste ambiente; o OAuth do conector não foi copiado para o CLI.
- **Testes desta verificação:** identidade autenticada confirmada; leitura de metadados públicos do modelo confirmada; consulta de Jobs indisponível; criação/edição de Space não pôde ser testada porque não existe ferramenta de escrita exposta. O erro 403 observado no navegador continua distinto do login do conector.
- **Conclusão operacional:** o plugin melhorou o acesso de leitura à conta e aos metadados, mas não concede “liberdade” de administração do Space. Para criar/configurar, é necessário um canal de escrita autorizado (por exemplo, habilitar permissões de escrita na integração ou usar uma sessão autenticada/CLI com token de escrita mantido fora do repositório). Não registrar nem compartilhar esse token em arquivos ou mensagens.


### Repasse de requisitos ao desenvolvimento (2026-10-09)

- **Mudança e motivo:** criação de `docs/RETAIL_HANDOFF.md`, com escopo, baseline auditada, defeitos reproduzidos, IDs de requisitos, critérios de aceitação, incrementos e contrato de retorno entre chats; alinhamento desta referência com limitações reais do comando local, circulação e preservação de inventário.
- **Arquivos afetados:** `docs/RETAIL_FOUNDATION.md` e `docs/RETAIL_HANDOFF.md`. Nenhuma alteração funcional.
- **Verificação:** revisão de consistência documental e `git diff --check`.
- **Evidência anterior desta sessão:** 23 testes passaram, com 6 avisos; API local de validação/exportação funcionou; DXF em metros com 9 polilinhas e zero erros de auditoria. Casos exploratórios aceitaram acessos coincidentes, conexão de 1 cm e remoção de equipamentos por provedor simulado; o CLI documentado falhou por módulo ausente.
- **Não executados nesta atualização:** nova suíte funcional, build frontend, AutoCAD, implantação/inferência ou GPU remota; mudança exclusivamente documental. Os requisitos novos continuam propostos, não implementados nem validados com o consultor.


### I0 — demonstração local reproduzível (2026-10-09)

- **Requisitos:** RF-LAY-01 e RQ-LAY-01 implementados; RQ-LAY-02 parcialmente atendido pelo relatório e pela legenda SVG. DEF-01 corrigido.
- **Arquivos:** `backend/src/retail/demo.py`, `backend/src/retail/preview.py`, `backend/tests/test_retail_demo.py`, tarefa VS Code e documentação/handoff.
- **Decisão:** reutilizar o esquema e exportador DXF existentes; SVG usa retângulos métricos e transformação vertical explícita para origem inferior esquerda. Saídas existentes são preservadas. Não se amplia o alcance do validador neste incremento.
- **Verificação:** ambiente virtual novo com Python 3.12.14 e `audit/requirements-audit.txt`; comando documentado gerou as três saídas. Suíte completa: 30 passaram, 6 avisos de depreciação existentes. Os sete novos casos cobrem correspondência métrica DXF/SVG, auditoria DXF, relatório, entrada inválida/ausente, preservação de saídas e escape XML.
- **Limitações:** validação comercial/humana, AutoCAD, frontend e integração remota não executados. DEF-02/03/04, acessos físicos e percurso continuam pendentes em I1/I2.

Verificação visual de I0: SVG renderizado com CairoSVG e inspecionado; corrigida altura explícita da imagem para preservar a proporção. CairoSVG/Black foram ferramentas de desenvolvimento locais, não dependências do CLI. `git diff --check` sem erros.

### Revisão de requisitos após I0 (2026-10-09)

A orientação de I1 está refinada em [RETAIL_HANDOFF.md](RETAIL_HANDOFF.md), v0.3, seção “Revisão de requisitos após I0”. A revisão inspecionou o commit `f0ed33c`; não reexecutou os testes nem realizou nova inspeção visual. Os 30 testes/6 avisos permanecem evidência reportada pelo desenvolvimento.

I1 será dividido em I1a (políticas independentes de presença, mobilidade e substituição; comparação de inventário) e I1b (acessos físicos e circulação). Políticas da entrada não podem ser relaxadas pela proposta do provedor. Aberturas são segmentos no limite, distintos de corredores. A circulação considera largura utilizável e caminhos alternativos; conexões aos pares não autorizam alegação geral de passagem em curvas. Compatibilidade legada deve explicitar aprovação parcial. RF-LAY-08 permanece em I2.

Estas convenções são propostas para cenários sintéticos; não confirmam dados de lojas reais. Atualização exclusivamente documental, sem código ou novos testes funcionais; verificação por leitura e revisão de consistência com os IDs existentes.
