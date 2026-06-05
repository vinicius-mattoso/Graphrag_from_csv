# python -m method_01.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context

## Contexto recuperado:
[1] metadata={'_depth': 0, '_similarity_score': np.float64(0.5350226862595612), 'category': 'Valvula', 'part_id': 'P-006', 'doc_type': 'Part', 'criticality': 'Alta', 'asset_class': 'COMPRESSOR_AR', 'source_file': 'parts.csv', 'doc_id': 'part:P-006:COMPRESSOR_AR'}
conteudo=Peca P-006 - Valvula retencao DN50. Categoria Valvula. Compativel com a classe COMPRESSOR_AR. Criticidade Alta. Lead time 25 dias. Custo unitario 780.00. Estoque 0 no Almoxarifado Utilidades, minimo 2, ponto de reposicao 4. Fornecedores: Fornecedor Omega preferencial=false entrega_media=24 dias confiabilidade=0.69.

[2] metadata={'_depth': 0, '_similarity_score': np.float64(0.5119032620446521), 'doc_type': 'Failure', 'severity': 'Alta', 'source_file': 'failures.csv', 'failure_code': 'F-QUEDA_PRESSAO', 'doc_id': 'failure:F-QUEDA_PRESSAO'}
conteudo=Falha F-QUEDA_PRESSAO - Queda de pressao. Sintoma: Pressao de saida abaixo do limite. Causa raiz: Filtro saturado valvula desgastada ou vazamento. Acao recomendada: Substituir filtro e verificar vedacoes. Severidade: Alta.

[3] metadata={'_depth': 0, '_similarity_score': np.float64(0.49957127123154443), 'asset_class': 'BOMBA_CENTRIFUGA', 'category': 'Vedacao', 'source_file': 'parts.csv', 'doc_type': 'Part', 'criticality': 'Alta', 'part_id': 'P-001', 'doc_id': 'part:P-001:BOMBA_CENTRIFUGA'}
conteudo=Peca P-001 - Selo mecanico 32mm. Categoria Vedacao. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 14 dias. Custo unitario 650.00. Estoque 3 no Almoxarifado Central, minimo 5, ponto de reposicao 8. Fornecedores: Fornecedor Alpha preferencial=true entrega_media=12 dias confiabilidade=0.92.

[4] metadata={'_depth': 0, '_similarity_score': np.float64(0.4985266493164333), 'source_file': 'parts.csv', 'category': 'Vedacao', 'part_id': 'P-005', 'doc_type': 'Part', 'asset_class': 'BOMBA_CENTRIFUGA', 'criticality': 'Alta', 'doc_id': 'part:P-005:BOMBA_CENTRIFUGA'}
conteudo=Peca P-005 - Jogo de juntas EPDM. Categoria Vedacao. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 18 dias. Custo unitario 480.00. Estoque 4 no Almoxarifado Central, minimo 4, ponto de reposicao 6. Fornecedores: Fornecedor Alpha preferencial=true entrega_media=15 dias confiabilidade=0.92.

[5] metadata={'_depth': 1, '_similarity_score': np.float64(0.4979765292155689), 'doc_type': 'Part', 'part_id': 'P-003', 'asset_class': 'COMPRESSOR_AR', 'doc_id': 'part:P-003:COMPRESSOR_AR', 'criticality': 'Alta', 'category': 'Filtragem', 'source_file': 'parts.csv'}
conteudo=Peca P-003 - Filtro coalescente 1pol. Categoria Filtragem. Compativel com a classe COMPRESSOR_AR. Criticidade Alta. Lead time 21 dias. Custo unitario 320.00. Estoque 1 no Almoxarifado Utilidades, minimo 3, ponto de reposicao 5. Fornecedores: Fornecedor Gamma preferencial=true entrega_media=18 dias confiabilidade=0.81.

[6] metadata={'_depth': 1, '_similarity_score': np.float64(0.4915903363464697), 'doc_type': 'AssetClass', 'asset_class': 'COMPRESSOR_AR', 'doc_id': 'asset_class:COMPRESSOR_AR', 'source_file': 'assets.csv;parts.csv'}
conteudo=Classe de ativo COMPRESSOR_AR. Esta classe conecta ativos industriais a pecas compativeis para manutencao.

[7] metadata={'_depth': 1, '_similarity_score': np.float64(0.4828851254603042), 'asset_class': 'BOMBA_CENTRIFUGA', 'doc_id': 'part:P-002:BOMBA_CENTRIFUGA', 'doc_type': 'Part', 'part_id': 'P-002', 'criticality': 'Alta', 'category': 'Rolamento', 'source_file': 'parts.csv'}
conteudo=Peca P-002 - Rolamento 6312. Categoria Rolamento. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 10 dias. Custo unitario 210.00. Estoque 12 no Almoxarifado Central, minimo 6, ponto de reposicao 10. Fornecedores: Fornecedor Beta preferencial=true entrega_media=8 dias confiabilidade=0.88.

[8] metadata={'_depth': 1, '_similarity_score': np.float64(0.4793509288665852), 'work_order_id': 'WO-1003', 'maintenance_type': 'Corretiva', 'failure_code': 'F-QUEDA_PRESSAO', 'doc_id': 'work_order:WO-1003', 'asset_id': 'A-200', 'doc_type': 'WorkOrder', 'asset_class': 'COMPRESSOR_AR', 'status': 'Fechada', 'source_file': 'work_orders.csv'}
conteudo=Ordem de servico WO-1003 para o ativo A-200 - Compressor de ar 01, classe COMPRESSOR_AR, local Utilidades / Sala 3. Tipo de manutencao Corretiva. Status Fechada. Aberta em 2025-06-03 e fechada em 2025-06-04. Falha F-QUEDA_PRESSAO - Queda de pressao. Descricao: Queda de pressao com filtro saturado e valvula com desgaste. Downtime: 12.0 horas.

As peças que podem ajudar a resolver a queda de pressão no compressor são:

1. **Válvula de retenção DN50 (P-006)**
   - Categoria: Válvula
   - Classe: COMPRESSOR_AR
   - Criticidade: Alta
   - Custo unitário: 780.00
   - Estoque: 0 (mínimo 2, ponto de reposição 4)

2. **Filtro coalescente 1pol (P-003)**
   - Categoria: Filtragem
   - Classe: COMPRESSOR_AR
   - Criticidade: Alta
   - Custo unitário: 320.00
   - Estoque: 1 (mínimo 3, ponto de reposição 5)

Essas peças são relevantes para a manutenção do compressor e podem ajudar a mitigar a falha de queda de pressão, que é causada por um filtro saturado ou uma válvula desgastada, conforme indicado na falha F-QUEDA_PRESSAO.

Fontes:
- part:P-006:COMPRESSOR_AR (Part; P-006; parts.csv)
- failure:F-QUEDA_PRESSAO (Failure; F-QUEDA_PRESSAO; failures.csv)
- part:P-001:BOMBA_CENTRIFUGA (Part; P-001; parts.csv)
- part:P-005:BOMBA_CENTRIFUGA (Part; P-005; parts.csv)
- part:P-003:COMPRESSOR_AR (Part; P-003; parts.csv)
- asset_class:COMPRESSOR_AR (AssetClass; assets.csv;parts.csv)
- part:P-002:BOMBA_CENTRIFUGA (Part; P-002; parts.csv)
- work_order:WO-1003 (WorkOrder; WO-1003, A-200, F-QUEDA_PRESSAO; work_orders.csv)