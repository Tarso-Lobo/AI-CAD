# Repasse para desenvolvimento e gestão — layout e planograma

Versão: 0.2 — 09/10/2026.
Estado: I0 implementado e testado localmente; I1/I2 propostos. Não é aprovação comercial.
Referência principal: [RETAIL_FOUNDATION.md](RETAIL_FOUNDATION.md).
Baseline auditada: branch `feat/retail-foundation`, commit `6eb691f061a106263ac05d1577109e73977d67a3`, PR nº 1 aberta em rascunho.
Antes de implementar, conferir HEAD, alterações locais e estado da PR. A baseline é evidência histórica, não pressuposição de que a branch ficará congelada.

## 1. Resultado esperado e fronteira

Apoiar consultor e proprietário na representação de uma loja, organização de equipamentos/seções, revisão de alternativas e exportação de artefatos espaciais verificáveis. O desenvolvimento começa com dados sintéticos e funcionamento local.

Este projeto tem escopo próprio. Vendas, margem, estoque, câmeras, identificação de pessoas, recomendações comerciais contínuas e decisões tributárias pertencem à outra frente ou a investigações específicas. Podem fornecer contexto futuro, mas não entram automaticamente no backlog deste software.

Layout organiza espaço, acessos, equipamentos e circulação. Planograma detalha exposição nos equipamentos e deve referenciar a mesma alternativa de layout. O código atual representa parte do layout, sem planograma detalhado.

O software representa uma estratégia fornecida pelo responsável; não calcula proporções comerciais universais. Intenção de iluminação não é cálculo luminotécnico. Desenho e DXF não certificam estrutura, acessibilidade, incêndio ou engenharia executiva.

## 2. Fontes e classificação

| Fonte | Conteúdo e condição |
| --- | --- |
| S01 — instruções do proponente neste chat, 09/10/2026 | Objetivo, fronteira, modo de trabalho e exigência de documentação/testes |
| S02 — PDF “dominio-problema-solucoes-inteligentes-varejo(1).pdf”, v0.1, 07/10/2026 | Seção 3.1: domínio, categorias candidatas, identidade dos equipamentos, alternativas, percurso e planograma; revisão humana pendente |
| S03 — baseline GitHub acima | Código, documentos, exemplo e testes inspecionados |
| S04 — auditoria local deste chat, 09/10/2026 | 23 testes passando e reproduções exploratórias descritas abaixo |
| S05 — relatos de Edson sintetizados em S01/S02 | Conhecimento comercial a validar com o consultor; não houve nova entrevista |

O PDF também descreve outro caso fictício, Mercado Horizonte, de 24 × 12 m. Não misturar esse cenário com o exemplo de 12 × 10 m do AI-CAD.

Para medidas e regras, distinguir informado, medido, inferido, hipótese e desconhecido. “Informado” não significa medição independente. Campos comerciais e dimensões do exemplo são dados simulados. Metas numéricas de qualidade comercial não estão aprovadas.

## 3. Estado comprovado

| Componente | Estado observado |
| --- | --- |
| Esquema RetailLayout | Prédio retangular; retângulos sem rotação; alturas, categorias, áreas livres e intenções |
| validate_layout | Verifica limites, colisões, invasão de zonas livres, largura dos retângulos, conexão declarada e altura na zona de visibilidade |
| POST /api/v1/retail/validate | Funcionou localmente com TestClient; escopo declarado: declared_geometry_only |
| POST /api/v1/retail/export.dxf | Funcionou localmente; DXF em metros, 9 polilinhas e zero erros na auditoria ezdxf |
| Prévia SVG | I0: gerada por CLI a partir do mesmo RetailLayout do DXF; sem percurso completo |
| POST /api/v1/retail/generate | Adaptador preparado; respostas simuladas testadas; sem inferência remota comprovada |
| Frontend | Não foi encontrada integração com endpoints de varejo; build não executado nesta auditoria |
| Planograma, versões e comparação | Não implementados no caminho de varejo inspecionado |
| Hugging Face | Space não criado/testado conforme registro disponível; sem GPU remota comprovada |

A rede de circulação não representa, por si, uma jornada comercial, fila, reposição ou rota de emergência. A verificação de altura numa região não calcula linhas de visão. O DXF contém polilinhas e textos; não contém cotas técnicas, portas/vãos ou paredes detalhadas.

## 4. Problemas reproduzidos e impacto

| ID | Evidência | Consequência |
| --- | --- | --- |
| DEF-01 | Comando src.retail.demo falha: módulo inexistente; documentação e tarefa VS Code o referenciam | Demonstração local não é reproduzível pelo caminho anunciado |
| DEF-02 | Entrada e saída com IDs diferentes e geometria idêntica são aceitas | Distinção nominal não assegura separação espacial |
| DEF-03 | Duas zonas internas de 2 × 2 m, em (2,2) e (3.99,3.99), são aceitas; conexão de 1 × 1 cm | Largura de cada retângulo não garante passagem suficiente entre eles |
| DEF-04 | Cliente simulado remove básicos, bazar e caixa; proposta com apenas hortifruti é aceita | Dimensões externas são preservadas, mas inventário e funções podem mudar silenciosamente |
| DIV-01 | Prompt exige preservar elementos fixos, mas esquema não registra condição de alteração | A obrigação textual não tem controle equivalente no código |
| DIV-02 | Prompt descreve correção com tentativas limitadas; adaptador executa uma chamada | Processo de recuperação descrito ainda não implementado |
| GAP-01 | Acessos são zonas internas; não há entidade de abertura no limite do prédio | Não é possível comprovar onde o cliente atravessa o limite físico |
| GAP-02 | Prévia e rede não modelam entrada → destinos → caixa → saída | Falta validar o problema de fluxo apontado pelo proponente |

DEF-04 demonstra ausência de proteção; não significa que todos os equipamentos do exemplo já foram classificados como obrigatórios. Essa condição precisa ser explicitada.

## 5. Requisitos da próxima etapa

IDs estáveis. Estado da v0.2: RF-LAY-01 e RQ-LAY-01 implementados e testados localmente; RQ-LAY-02 parcialmente implementado. Demais requisitos propostos e pendentes.
P0 = demonstração reproduzível; P1 = fidelidade e circulação; P2 = percepção do percurso.

| ID / tipo | Obrigação | Prioridade / origem | Critério verificável |
| --- | --- | --- | --- |
| RF-LAY-01 | O sistema deve validar e exportar o exemplo por comando local documentado | P0 / S01,S03,S04; DEF-01 | Em ambiente com dependências documentadas, o comando gera DXF e SVG sem credencial nem chamada externa |
| RQ-LAY-01 | As exportações DXF e SVG devem representar as mesmas coordenadas métricas da alternativa | P0 / S01,S03 | Comparar limites e posições/dimensões dos equipamentos nas duas saídas; DXF declara metros |
| RF-LAY-02 | O sistema deve representar acessos físicos com função e posição no limite do espaço | P1 / S01,S02; GAP-01 | Acesso válido no limite é aceito; acesso sem ligação ao limite é rejeitado ou explicitamente marcado como dado incompleto, sem aprovação completa |
| RF-LAY-03 | O sistema deve rejeitar sobreposição dos acessos de entrada e saída no cenário de teste que exige separação | P1 / S01; DEF-02 | Geometria coincidente ou sobreposta é rejeitada com motivo; conexões entre corredores internos continuam permitidas |
| RF-LAY-04 | O sistema deve verificar a largura utilizável das conexões da rede de circulação | P1 / S01,S04; DEF-03 | Ligação de 1 cm e contato só por ponto são rejeitados; ligação com largura declarada e rede conectada é aceita |
| RD-LAY-01 | O sistema deve registrar a condição de alteração de cada equipamento | P1 / S02; DIV-01 | Distingue fixo, obrigatório reposicionável, substituível mediante decisão e condição desconhecida; desconhecido não autoriza alteração silenciosa |
| RF-LAY-05 | O sistema deve rejeitar proposta que remova equipamento obrigatório | P1 / S02,S04; DEF-04 | Provedor simulado remove obrigatório: proposta rejeitada com ID e motivo |
| RF-LAY-06 | O sistema deve rejeitar proposta que modifique geometria protegida de elemento fixo | P1 / S01,S02; DIV-01 | Simulações de deslocamento/redimensionamento de fixo são rejeitadas; reposicionamento permitido é aceito se válido |
| RF-LAY-07 | O sistema deve apresentar diferenças de inventário entre entrada e proposta | P1 / S02,S04 | Inclusão, remoção e mudança de dimensão são listadas; substituição permitida permanece alternativa explícita |
| RF-LAY-08 | O sistema deve representar percurso comercial proposto com entrada, destinos, caixa e saída | P2 / S01,S02; GAP-02 | Prévia identifica sequência; percurso bloqueado por equipamento é sinalizado; caminho válido não é apresentado como previsão de comportamento |
| RQ-LAY-02 | O resultado deve declarar quais verificações foram executadas e quais permanecem pendentes | P0–P2 / S01,S02 | “Geometria sem conflitos” não aparece como validação comercial/técnica completa; relatório distingue cálculo, intenção e dados desconhecidos |

**Restrições:** 1,5 m e limite de altura de 1,3 m pertencem ao exemplo atual; não são declaração de norma ou regra universal. Para DEF-03, usar largura informada pelo cenário. Uma solução para portas, tolerâncias ou circulação deve documentar convenções e limitações; não inferir um requisito legal.

A posição física dos acessos e as regras de mudança de inventário do exemplo serão configurações sintéticas explícitas, a confirmar pelo proponente. Não convertê-las em fatos de uma loja real.

## 6. Modelo mínimo candidato

| Conceito | Relação / distinção necessária |
| --- | --- |
| Loja | Contexto próprio e cenário: existente, nova ou expansão |
| Caracterização | Versão dos dados espaciais/comerciais usados por uma alternativa |
| Equipamento | ID estável, dimensões, altura, condição de alteração e fonte |
| Acesso | Função, geometria e ligação ao limite do espaço; não confundir com corredor |
| Alternativa | Arranjo ligado à caracterização e inventário; atual e proposta são distintos |
| Percurso | Jornada comercial declarada na alternativa; independente da rede de áreas livres |
| Planograma | Detalhamento de exposição ligado a equipamentos da alternativa correspondente |

Este modelo orienta evolução; não exige banco novo nem implementação de todas as entidades agora.
Modalidades futuras:
- Existente: preservar representação atual e comparar proposta.
- Expansão: separar estrutura existente e área adicional; registrar o que pode mudar.
- Nova: começar do espaço e necessidades; o esquema atual exige ao menos um equipamento, logo ainda não aceita uma planta vazia como entrada válida.
Nenhuma modalidade é declarada totalmente implementada.

## 7. Ordem de trabalho e conclusão de cada incremento

### I0 — reproduzir a demonstração local
Atender RF-LAY-01, RQ-LAY-01 e parte de RQ-LAY-02.
Reutilizar modelo/exportador; adicionar caminho local de SVG a partir dos mesmos dados.
Testar exemplo válido e geometria inválida. Erro não pode produzir artefato anunciado como aprovado.
Atualizar comandos em RETAIL_FOUNDATION.md e .vscode/tasks.json; conferir instalação em ambiente isolado.
Concluir quando alguém puder executar a demonstração sem HF, credenciais ou servidor remoto.

### I1 — proteger fidelidade e circulação
Atender RF-LAY-02 a RF-LAY-07 e RD-LAY-01.
Modelar configuração sintética explícita antes de introduzir obrigações no validador.
Acrescentar regressões para DEF-02/03/04 e mudanças de fixos, além de casos permitidos.
Documentar migração do JSON, compatibilidade e significado da aprovação parcial.
Concluir quando cenários inválidos forem rejeitados e mudanças permitidas continuarem possíveis.

### I2 — tornar o fluxo revisável visualmente
Atender RF-LAY-08 e completar RQ-LAY-02.
Mostrar acessos, percurso e alturas, legenda e dimensões; indicar fila/reposição como pendências enquanto não modeladas.
Concluir com revisão visual do proponente/consultor, registrada como pendente até ocorrer.

Depois: comparar atual/proposta e versões; definir nível inicial de planograma; integrar editor.
Não antecipar reconstrução por foto, 3D sofisticado ou otimização comercial para concluir I0/I1.

## 8. GitHub e Hugging Face

### GitHub
- Ler AGENTS.md e documentação atual antes de editar; não apagar histórico.
- Trabalhar em commits pequenos na branch de trabalho, ou branch derivada quando houver concorrência.
- Manter PR em rascunho enquanto os critérios não estiverem atendidos; não fazer merge automático.
- Atualizar especificação pertinente, este repasse e registro de testes no mesmo conjunto de mudanças.
- Incluir IDs no relato do commit/PR e associar requisito → arquivo → teste → commit quando implementado.
- Registrar conflito de intenção como proposta de mudança, com impacto e alternativas; não decidir silenciosamente uma regra comercial.

### Hugging Face
- ZeroGPU é experimento opcional, sem dependência para I0/I1/I2.
- Backend e proposta simulada permitem validar contrato e falhas sem inferência real.
- app.py carrega modelo em CUDA: não anunciar esse Space como alternativa local pronta.
- O registro anterior relata 403 no navegador e conector com leitura/metadados; ferramentas de escrita de Spaces e Jobs não estavam disponíveis. Isso não deve ser generalizado para futuras sessões: verificar capacidades reais antes de qualquer operação.
- Space, build, ID/URL, inferência e GPU continuam sem comprovação neste repasse.
- Não criar recursos pagos ou mover dados reais de loja como consequência automática deste documento.
- Credenciais só no mecanismo de segredos/ambiente apropriado; nunca em código, exemplos, logs ou documentos.
- Se houver teste remoto posterior: registrar provedor/modelo, revisão dos arquivos, tempo, saída, aceitação/rejeição local e consumo/custo disponível. Distinguir falha de transporte de falha de proposta.

Não é necessário pesquisar modelo novo antes de fechar os defeitos de validação.

## 9. Evidências de teste e pendências

Em 09/10/2026, na baseline auditada:
- Suíte backend: 23 passaram, 6 avisos de depreciação.
- API com TestClient: validação e exportação HTTP 200.
- DXF: leitura ezdxf, metros, 9 polilinhas e zero erros de auditoria estrutural.
- DEF-01/02/03/04: reproduzidos conforme seção 4.
- Gradio/IA: provedor simulado; nenhuma chamada remota.
- SVG versionado e páginas 14–15 do PDF: inspeção visual realizada.
- Build frontend, AutoCAD e GPU/inferência remota: não executados; fora da verificação local realizada.
- Parte dos testes CAD legados apenas executa/imprime operações; ampliar assertions ao modificar comportamento relevante.

Os resultados acima são da auditoria precedente. A implementação e os novos testes de I0 estão registrados abaixo; não comprovam I1/I2.

## 10. Contrato de retorno ao chat de requisitos

Chats separados não se comunicam automaticamente. Este arquivo e RETAIL_FOUNDATION.md são o contrato compartilhado. No fechamento de cada incremento, atualizar:
1. HEAD/branch/PR e data;
2. IDs atendidos, parcialmente atendidos e pendentes;
3. arquivos, comportamento e decisões alterados;
4. comandos e resultados de testes locais, simulados e remotos;
5. limitações e perguntas que realmente mudam o requisito;
6. próxima menor ação.

Questões a devolver: condição do inventário; convenção de linear (faces, módulos, níveis); quem aprova; dados indispensáveis para modalidades de loja; representação de fila e reposição; justificativas de estratégia do consultor. Não exigir todas as respostas para começar I0.

## 11. Mensagem inicial para o chat desenvolvedor/gestor

> Atue como desenvolvedor e gestor técnico do software de layout e planograma AI-CAD, usando desenvolvimento-orientado-a-requisitos e parceiro-critico. Leia AGENTS.md, docs/RETAIL_FOUNDATION.md e docs/RETAIL_HANDOFF.md na versão atual do GitHub; confira a branch feat/retail-foundation e a PR nº 1 antes de alterar código. Preserve trabalho existente e mantenha este escopo separado da inteligência operacional do varejo. Comece pelo incremento I0, implemente a demonstração local documentada e confira RF-LAY-01/RQ-LAY-01. Depois avance a I1 em mudanças pequenas e verificáveis, explicitando configuração sintética e regras de alteração dos equipamentos. Não dependa de ZeroGPU para avançar. Atualize especificação e handoff com cada mudança; associe IDs a arquivos, testes e commits. Relate apenas resultados observados. Devolva conflitos de intenção e novas necessidades como propostas ao chat de requisitos pelos artefatos compartilhados. Mantenha a PR em rascunho e não faça merge ou implantação como efeito automático do repasse.

## Registro desta versão

09/10/2026 — criação deste repasse e vínculo na referência principal.
Motivo: converter a auditoria em requisitos verificáveis e ordem de desenvolvimento, preservando separação de escopo.
Arquivos: docs/RETAIL_HANDOFF.md e docs/RETAIL_FOUNDATION.md.
Verificação desta mudança: revisão de consistência de IDs, prioridades, critérios, fontes e estado; git diff --check.
Testes funcionais novos: não executados, por se tratar apenas de documentação.


## Retorno do desenvolvimento — I0, 09/10/2026

- **Base efetivamente inspecionada:** `feat/retail-foundation`, HEAD `c00caff9d78c1510fa3c8f115d95fd82fbbf5f23`, árvore local limpa antes das alterações. PR nº 1 aberta em rascunho. Este conjunto de alterações tem mensagem de commit `feat(retail): implement I0 local demo (RF-LAY-01, RQ-LAY-01)`; seu SHA pode ser obtido no histórico, evitando referência circular no próprio commit.
- **Estado:** RF-LAY-01/RQ-LAY-01 implementados e testados; RQ-LAY-02 parcial; RF-LAY-02…08/RD-LAY-01 pendentes. DEF-01 corrigido; DEF-02/03/04 não alterados.
- **Rastreabilidade:** RF-LAY-01 → `backend/src/retail/demo.py` → `test_cli_exports_metric_equivalent_geometry`, `test_cli_failure_produces_no_exports`, `test_cli_preserves_existing_outputs`; RQ-LAY-01 → `backend/src/retail/preview.py` e exportador existente → teste de equivalência métrica; RQ-LAY-02 → `validation.json` produzido pelo CLI e legenda SVG → assertions de escopo/pendências no teste CLI.
- **Decisões:** preservar coordenadas métricas no SVG usando transformação vertical explícita; diretório novo/vazio evita sobrescrita e confusão com saídas anteriores; dados não são classificados automaticamente como medidos/sintéticos; relatório indica procedência não verificada e intenções declaradas.
- **Comandos observados:** instalação de `audit/requirements-audit.txt` em ambiente virtual novo Python 3.12.14; `PYTHONPATH=backend python -m src.retail.demo examples/retail-demo.json examples/generated` gerou DXF/SVG/relatório; `PYTHONPATH=backend python -m pytest backend/tests -q`: **30 passaram, 6 avisos**. Não houve cliente remoto ou GPU.
- **Limites:** Windows/VS Code não executados neste ambiente; tarefa conferida por inspeção. AutoCAD, build frontend e revisão do consultor pendentes. Aprovação continua limitada às verificações existentes.
- **Próxima ação:** I1, explicitar regras sintéticas de alteração do inventário e convenção de acessos/conexões antes de ampliar os validadores; registrar propostas em `mudancas.md` se revelarem conflito de intenção. Não há bloqueio de GPU para esse trabalho.

Verificação visual de I0: SVG renderizado com CairoSVG e inspecionado; corrigida altura explícita da imagem para preservar a proporção. CairoSVG/Black foram ferramentas de desenvolvimento locais, não dependências do CLI. `git diff --check` sem erros.
