# Prompt para produzir uma proposta compatível com o protótipo

Use junto com o JSON Schema de `RetailLayout.model_json_schema()` e com a definição da loja. É um contrato de experimento para o esquema limitado atual.

Você recebe medidas em metros, equipamentos, elementos fixos e uma estratégia já decidida. Produza somente um objeto JSON conforme o schema fornecido. Não gere código, comandos, markdown ou campos adicionais.

Preserve as medidas do prédio e os elementos fixos. Não invente viabilidade estrutural. Represente os equipamentos como retângulos alinhados aos eixos; se a entrada exigir rotação ou geometria que o schema não comporte, informe a incompatibilidade ao operador antes da etapa de geração.

Defina áreas de circulação livres, IDs únicos para entrada e saída e a área de visibilidade da entrada. Preserve a largura mínima indicada pelo cenário. Não ocupe essas áreas com produtos ou equipamentos. Organize o acesso para que o cliente veja a oferta de destaque e avance pela loja. Os básicos e os caixas devem respeitar a estratégia recebida.

Explicite o ponto forte em commercial_strength e a intenção de iluminação em lighting_intent. As alturas dos equipamentos são obrigatórias. Não confunda intenção de iluminação com cálculo luminotécnico. Não invente vendas, margem ou proporções ideais.

A aplicação deve validar o JSON e a geometria antes de aceitar a proposta. Se houver erros, devolva-os ao modelo junto com a proposta, limitando as tentativas; se persistirem, mantenha o resultado como rejeitado para revisão humana. Nunca anuncie sucesso apenas porque o JSON ou DXF é sintaticamente válido.


Para teste remoto, passe o JSON completo ao endpoint Gradio. O prompt final da chamada acrescenta o JSON atual e as instruções, pedindo um objeto completo. A API local executa validação estrutural e geométrica depois da resposta; uma saída do modelo nunca deve ser exportada sem essa etapa.
