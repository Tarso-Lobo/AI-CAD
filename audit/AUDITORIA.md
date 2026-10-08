# Auditoria do AI-CAD para layouts de varejo

Data: 08/10/2026. Repositório: https://github.com/ishan-parihar/AI-CAD

Commit examinado: `4a79926ef5e154403d1724c3796004b8b37e324d`.

## Decisão

Vale fazer um fork para experimentação e reaproveitamento seletivo. O projeto tem backend FastAPI, persistência, geração DXF e uma interface Next.js. Ainda não é uma base pronta para gerar layouts comerciais confiáveis, e o caminho de geração com IA está quebrado no commit examinado.

Manteríamos a estrutura de API, o uso de ezdxf e partes do visualizador. A representação de loja, equipamentos, categorias, acessos, alturas e estratégia comercial precisa ser criada. O algoritmo atual distribui cômodos com posições iniciais aleatórias; não implementa planogramas de varejo.

A existência de um DXF válido não demonstra que a planta respeita o pedido. Essa diferença apareceu diretamente nos testes: uma solicitação impossível terminou com status `completed` e nenhum cômodo colocado.

## O que foi verificado

- Leitura do fluxo HTTP, cliente de IA, configuração, persistência, ferramentas espaciais, geração DXF, frontend e testes fornecidos.
- Importação do backend em Python 3.12, com dependências instaladas em ambiente separado. As versões estão em `audit/evidence.json`.
- Chamadas HTTP locais com FastAPI TestClient, banco SQLite e arquivos em diretório temporário.
- Geração sem IA, download, leitura do DXF com ezdxf e auditoria estrutural do arquivo.
- Execução do fluxo de IA com cliente simulado, mantendo as assinaturas dos métodos originais. Nenhuma chave real, modelo remoto ou chamada paga foi usado.
- Testes de restrições ignoradas, pedido impossível, nome de arquivo, exclusão, metadados e auxiliares CAD.
- Tentativa de instalação padrão do frontend e execução da suíte `backend/tests/`.

Não foram executados o frontend no navegador, inferência real, GPU, AutoCAD, colaboração multiusuário ou avaliação de qualidade comercial. O frontend não chegou à etapa de build porque a instalação padrão falhou.

## Resultados reproduzidos

| Verificação | Resultado observado |
|---|---|
| Saúde HTTP | 200 |
| Planta simples sem IA | `completed`, um cômodo colocado |
| DXF gerado | Leitura bem-sucedida, unidade em metros, zero erros na auditoria estrutural do ezdxf |
| Download | 200 |
| Preview JSON | Objeto vazio |
| Corredor mínimo de 100 m em loja de 24 x 12 m, pilar e acessos enviados em constraints | Mesmo desenho dos cômodos do caso sem essas restrições, usando a mesma semente |
| Cômodo de 10.000 m² em área de 288 m² | `completed`, zero cômodos colocados |
| Caminho de IA com cliente simulado | Zero chamadas de análise e otimização, mas `ai_enabled=true` |
| Nome `../audit-escaped` | DXF escrito fora da pasta do plano, ainda dentro da pasta temporária controlada da auditoria |
| Exclusão de plano | Registro removido, DXF permanece |
| Listagem de plantas comerciais | Tipo `residential` e nota 85 para todas as plantas concluídas |
| Auxiliar de texto | Retorna `None` por uso de método inexistente |
| Limites do desenho | Todos zero mesmo após inserir geometria |
| Dimensões negativas/zero e lista vazia | Modelo de entrada aceita |
| Suíte original | 1 falha, 3 passes; os testes de CAD imprimem resultados sem assertions |
| Instalação padrão frontend | `npm ci --ignore-scripts --no-audit --no-fund` falha com ERESOLVE |

Os probes registram o comportamento observado; não são uma suíte que aprova a aplicação. Os três passes da suíte original tampouco demonstram correção geométrica.

## Achados prioritários

### A01 - A análise por IA falha antes de chamar o modelo

Prioridade: alta. `backend/src/main.py`, linha 577.

`dimensions` é um dicionário, mas é acessado como `request.dimensions.width` e `.height`. O erro é capturado e o fluxo continua com o algoritmo. O teste confirmou zero chamadas ao método de análise.

Além disso, o prompt do cliente retorna `rooms`, enquanto o consumidor procura `room_suggestions`. Mesmo corrigindo o acesso às dimensões, os contratos de resposta precisam ser alinhados e validados.

Correção prevista: definir um único esquema de entrada/saída, validar JSON e distinguir geração com IA, fallback e falha.

### A02 - A otimização por IA também tem contrato incompatível

Prioridade: alta. `backend/src/main.py`, chamada a `suggest_optimizations`; `backend/src/ai_agent/openai_client.py`.

O método exige `current_layout` e `issues`, mas recebe apenas o primeiro argumento. O cliente documenta uma lista de sugestões; o consumidor espera um dicionário com `optimizations`. A aplicação de sugestões contém apenas comentários e logs, sem transformação geométrica correspondente.

Correção prevista: separar sugestão de alteração executada, alinhar assinaturas e só registrar aplicação quando a geometria realmente mudar.

### A03 - Conclusão do arquivo é confundida com atendimento ao pedido

Prioridade: alta. `backend/src/main.py`, fluxo de geração; `backend/src/tools/spatial_reasoning.py`, `_place_rooms` e `_generate_initial_layout`.

O algoritmo pode deixar de colocar elementos e retornar sucesso. A API conclui o plano depois de salvar um DXF não vazio. As restrições comerciais/físicas recebidas não são encaminhadas ao posicionamento; a etapa anunciada como validação contém `pass` nas linhas 771-774.

Correção prevista: resultado explícito de viabilidade, lista de elementos não colocados e validação obrigatória de dimensões, limites, colisões, acessos e corredores. O sistema deve explicar quando não consegue atender ao pedido.

### A04 - Nome do plano controla o caminho do arquivo

Prioridade: alta para hospedagem. `backend/src/main.py`, linhas 781-782; `backend/src/cad/dxf_generator.py`, `save_drawing`.

O nome fornecido é concatenado ao caminho. O probe usou apenas uma pasta temporária própria e confirmou saída da pasta específica do plano. Isso também permite colisões entre arquivos. As rotas de criação, leitura e exclusão não têm autenticação implementada no backend examinado.

Correção prevista: usar identificador interno como nome físico, conferir confinamento do caminho e aplicar autenticação/autorização antes de exposição pública.

### A05 - Configuração de IA é global e desprotegida

Prioridade: alta para hospedagem. `backend/src/main.py`, rotas `/api/v1/ai/configure` e `/api/v1/settings/ai-config`.

As rotas alteram o provedor e a chave do processo sem controle de usuário. A rota antiga recebe a chave na query string. A API também devolve prefixos da chave em algumas respostas. CORS não substitui autorização.

Correção prevista: segredos apenas no servidor, configuração restrita e nenhum fragmento de chave nas respostas. Uma implantação pública deve controlar também os destinos de inferência configuráveis.

### A06 - Metadados comunicam resultados que não foram medidos

Prioridade: alta para os testes do produto. `backend/src/main.py`, listagem e `result_data`.

A listagem fixa `building_type=residential` e nota 85 para qualquer plano concluído. O estado de IA depende da existência de um objeto cliente, mesmo quando as etapas falharam. A porcentagem de área ocupada não avalia fluxo comercial, qualidade do planograma ou preservação da estratégia.

Correção prevista: preservar o tipo recebido, registrar chamadas efetivas e substituir notas fixas por verificações explicadas.

### A07 - Há incompatibilidades no gerador CAD e na exclusão

Prioridade: média. `backend/src/cad/dxf_generator.py`; rota DELETE em `backend/src/main.py`.

`add_text` chama `Text.set_pos`, ausente no ezdxf 1.4.4 testado. `get_drawing_info` tenta ler `msp.bounds` e acaba retornando limites zero. A limpeza de arquivos da rota DELETE fica depois de um `return` e não é executada.

Correção prevista: atualizar os auxiliares CAD para a versão fixada, usar cálculo real de extents e executar a limpeza antes da resposta de exclusão.

### A08 - Instalação e testes não são reproduzíveis pelo guia atual

Prioridade: média. README, `backend/requirements.txt`, `frontend/package.json` e `backend/tests/`.

O guia principal manda instalar um `requirements.txt` na raiz, que não existe. Há divergências de porta e ponto de entrada entre documentos. As dependências Python têm apenas limites inferiores.

O npm rejeitou o conflito entre React/types 19 e `@testing-library/react-hooks@8.0.1`, que espera versões anteriores. Não foi usado `--force` para esconder o conflito. A suíte Python falhou no teste assíncrono sem marca/configuração de asyncio; os demais testes não possuem assertions.

Há também chamadas relativas a `/api/v1/settings/...` no frontend, sem rota Next.js nem rewrite correspondente na árvore examinada. Isso precisa ser corrigido ou suprido por um proxy explicitamente documentado. O endpoint de preview devolveu dados vazios no teste HTTP.

## O que reaproveitar e o que adaptar

| Componente | Decisão |
|---|---|
| FastAPI, respostas HTTP e organização básica do backend | Reaproveitar após corrigir contratos e validação |
| ezdxf e conceitos de camadas/blocos | Manter; corrigir auxiliares e conferir geometria |
| Persistência de planos e versões | Reaproveitar parcialmente; acrescentar contexto de loja e estados coerentes |
| Visualizador web | Avaliar depois de corrigir dependências e executar no navegador |
| Cliente de API compatível com OpenAI | Adaptar como um provedor de inferência, independente do domínio |
| Posicionamento residencial por cômodos | Substituir ou isolar como demonstração antiga |
| Notas fixas e status de sucesso atuais | Substituir |
| Regras comerciais e planograma de varejo | Implementar: não existem no código auditado |

O primeiro modelo de loja deve representar contorno, acessos fixos, pilares, equipamentos com medidas e alturas, seções, áreas de circulação e distribuição das categorias. A estratégia deve produzir critérios verificáveis, como posição do setor de atração e exposição por categoria. O layout em planta e as vistas de prateleira precisam compartilhar os mesmos equipamentos.

## Hugging Face, modelos abertos e GPU externa

O código já possui `OPENAI_BASE_URL`, `OPENAI_API_KEY` e `OPENAI_MODEL_NAME`. Isso favorece a criação de um adaptador para um servidor compatível com chat completions. O caminho de geração precisa ser corrigido antes de testar qualquer modelo.

Proposta de separação:

1. GitHub guarda código, esquemas, testes e exemplos sintéticos.
2. O backend valida a loja, chama a inferência e confere o resultado.
3. O modelo aberto é obtido no Hugging Face e executado no computador ou em GPU remota.
4. O gerador DXF roda em CPU. GPU será necessária conforme o modelo de inferência escolhido, não para desenhar linhas e blocos.

Não há integração Hugging Face/ZeroGPU pronta neste fork em preparação. Um Space Gradio com ZeroGPU usa um fluxo próprio; não basta colocar a URL do Space em `OPENAI_BASE_URL`. Será necessário um adaptador ou cliente apropriado.

Segundo a documentação oficial consultada em 08/10/2026, ZeroGPU compartilha GPU por chamadas, tem cotas e filas e exige Gradio. A página informa condições de elegibilidade para hospedagem gratuita por contas pessoais. Portanto, é uma opção para experimentos, sem assumir GPU contínua ou serviço de produção gratuito. Não foi criada conta, contratado recurso nem executado modelo.

Fontes: https://huggingface.co/docs/hub/spaces-zerogpu e https://huggingface.co/docs/hub/spaces-overview .

## Sequência de desenvolvimento após o fork

1. Preservar a licença MIT e a referência ao upstream. Abrir uma branch de adaptação para varejo.
2. Corrigir instalação, chamadas de IA, status, caminhos de arquivos e configuração de segredos.
3. Criar o esquema de loja e validar medidas, elementos fixos e circulação.
4. Gerar planta e planograma de um caso sintético com estratégia pronta; comparar com critérios, não apenas pela aparência.
5. Acrescentar um provedor de modelo aberto e medir correção do JSON, atendimento às restrições, latência e uso de memória.
6. Experimentar GPU externa somente depois de o fluxo funcionar com um provedor simulado e um caso reproduzível.

## Reprodução

Em ambiente Python 3.12 isolado, instalar `audit/requirements-audit.txt` e executar `python audit/reproduce.py` na raiz. O script usa dados sintéticos, remove configurações de IA do próprio processo e grava `audit/evidence.json`. Banco e DXFs são criados em pasta temporária e removidos ao terminar.

O arquivo de dependências registra as versões principais usadas; não é um lock completo de produção. Os testes originais foram executados com `python -m pytest tests/ -q` a partir de `backend/`.

## Estado da entrega

Auditoria concluída no commit indicado. Código de aplicação upstream preservado. Acrescentados relatório, probe e evidências na branch `audit/retail-readiness-20261008`.

Fork criado em https://github.com/Tarso-Lobo/AI-CAD pela interface do GitHub, com a licença e o histórico upstream preservados. Esta entrega registra a auditoria; as correções de aplicação acima permanecem trabalho futuro.
