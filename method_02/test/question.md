python -m method_02.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context


Resposta:

As peças que podem ajudar a resolver a queda de pressão no compressor são:

1. **Filtro coalescente 1pol** (ID: P-003)
   - Categoria: Filtragem
   - Criticidade: Alta
   - Lead time: 21 dias
   - Custo unitário: 320.00
   - Estoque: 1 no Almoxarifado Utilidades, mínimo 3, ponto de reposição 5.

2. **Válvula de retenção DN50** (ID: P-006)
   - Categoria: Válvula
   - Criticidade: Alta
   - Lead time: 25 dias
   - Custo unitário: 780.00
   - Estoque: 0 no Almoxarifado Utilidades, mínimo 2, ponto de reposição 4.

Essas peças são recomendadas devido à causa raiz da falha, que é um filtro saturado e uma válvula desgastada ou vazamento. A ação recomendada é substituir o filtro e verificar as vedações.

Contexto Neo4j:
Vector results:
- part:P-006:COMPRESSOR_AR score=0.7675 type=Part text=Peca P-006 - Valvula retencao DN50. Categoria Valvula. Compativel com a classe COMPRESSOR_AR. Criticidade Alta. Lead time 25 dias. Custo unitario 780.00. Estoque 0 no Almoxarifado Utilidades, minimo 2, ponto de reposicao 4. Fornecedores: Fornecedor Omega preferencial=false entrega_media=24 dias confiabilidade=0.69.
- failure:F-QUEDA_PRESSAO score=0.7560 type=Failure text=Falha F-QUEDA_PRESSAO - Queda de pressao. Sintoma: Pressao de saida abaixo do limite. Causa raiz: Filtro saturado valvula desgastada ou vazamento. Acao recomendada: Substituir filtro e verificar vedacoes. Severidade: Alta.
- part:P-001:BOMBA_CENTRIFUGA score=0.7498 type=Part text=Peca P-001 - Selo mecanico 32mm. Categoria Vedacao. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 14 dias. Custo unitario 650.00. Estoque 3 no Almoxarifado Central, minimo 5, ponto de reposicao 8. Fornecedores: Fornecedor Alpha preferencial=true entrega_media=12 dias confiabilidade=0.92.
- part:P-005:BOMBA_CENTRIFUGA score=0.7493 type=Part text=Peca P-005 - Jogo de juntas EPDM. Categoria Vedacao. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 18 dias. Custo unitario 480.00. Estoque 4 no Almoxarifado Central, minimo 4, ponto de reposicao 6. Fornecedores: Fornecedor Alpha preferencial=true entrega_media=15 dias confiabilidade=0.92.
- part:P-003:COMPRESSOR_AR score=0.7490 type=Part text=Peca P-003 - Filtro coalescente 1pol. Categoria Filtragem. Compativel com a classe COMPRESSOR_AR. Criticidade Alta. Lead time 21 dias. Custo unitario 320.00. Estoque 1 no Almoxarifado Utilidades, minimo 3, ponto de reposicao 5. Fornecedores: Fornecedor Gamma preferencial=true entrega_media=18 dias confiabilidade=0.81.
- asset_class:COMPRESSOR_AR score=0.7458 type=AssetClass text=Classe de ativo COMPRESSOR_AR. Esta classe conecta ativos industriais a pecas compativeis para manutencao.
- part:P-002:BOMBA_CENTRIFUGA score=0.7414 type=Part text=Peca P-002 - Rolamento 6312. Categoria Rolamento. Compativel com a classe BOMBA_CENTRIFUGA. Criticidade Alta. Lead time 10 dias. Custo unitario 210.00. Estoque 12 no Almoxarifado Central, minimo 6, ponto de reposicao 10. Fornecedores: Fornecedor Beta preferencial=true entrega_media=8 dias confiabilidade=0.88.
- work_order:WO-1003 score=0.7397 type=WorkOrder text=Ordem de servico WO-1003 para o ativo A-200 - Compressor de ar 01, classe COMPRESSOR_AR, local Utilidades / Sala 3. Tipo de manutencao Corretiva. Status Fechada. Aberta em 2025-06-03 e fechada em 2025-06-04. Falha F-QUEDA_PRESSAO - Queda de pressao. Descricao: Queda de pressao com filtro saturado e valvula com desgaste. Downtime: 12.0 horas.

Subgraph rows:
- work_order_id=WO-1001, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-SUPERAQUECIMENTO, failure_name=Superaquecimento, root_cause=Lubrificacao insuficiente ou atrito excessivo, recommended_action=Inspecionar lubrificacao alinhamento e componentes de vedacao, part_id=P-001, part_name=Selo mecanico 32mm, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1001, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-SUPERAQUECIMENTO, failure_name=Superaquecimento, root_cause=Lubrificacao insuficiente ou atrito excessivo, recommended_action=Inspecionar lubrificacao alinhamento e componentes de vedacao, part_id=P-002, part_name=Rolamento 6312, part_category=Rolamento, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1001, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-SUPERAQUECIMENTO, failure_name=Superaquecimento, root_cause=Lubrificacao insuficiente ou atrito excessivo, recommended_action=Inspecionar lubrificacao alinhamento e componentes de vedacao, part_id=P-005, part_name=Jogo de juntas EPDM, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1001, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-SUPERAQUECIMENTO, failure_name=Superaquecimento, root_cause=Lubrificacao insuficiente ou atrito excessivo, recommended_action=Inspecionar lubrificacao alinhamento e componentes de vedacao, part_id=P-006, part_name=Valvula retencao DN50, part_category=Valvula, part_criticality=Alta, warehouse=Almoxarifado Utilidades
- work_order_id=WO-1002, asset_id=A-101, asset_name=Bomba centrifuga 02, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-001, part_name=Selo mecanico 32mm, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1002, asset_id=A-101, asset_name=Bomba centrifuga 02, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-002, part_name=Rolamento 6312, part_category=Rolamento, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1002, asset_id=A-101, asset_name=Bomba centrifuga 02, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-005, part_name=Jogo de juntas EPDM, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1002, asset_id=A-101, asset_name=Bomba centrifuga 02, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-006, part_name=Valvula retencao DN50, part_category=Valvula, part_criticality=Alta, warehouse=Almoxarifado Utilidades
- work_order_id=WO-1003, asset_id=A-200, asset_name=Compressor de ar 01, asset_class=COMPRESSOR_AR, failure_code=F-QUEDA_PRESSAO, failure_name=Queda de pressao, root_cause=Filtro saturado valvula desgastada ou vazamento, recommended_action=Substituir filtro e verificar vedacoes, part_id=P-003, part_name=Filtro coalescente 1pol, part_category=Filtragem, part_criticality=Alta, warehouse=Almoxarifado Utilidades, supplier_name=Fornecedor Gamma
- work_order_id=WO-1003, asset_id=A-200, asset_name=Compressor de ar 01, asset_class=COMPRESSOR_AR, failure_code=F-QUEDA_PRESSAO, failure_name=Queda de pressao, root_cause=Filtro saturado valvula desgastada ou vazamento, recommended_action=Substituir filtro e verificar vedacoes, part_id=P-006, part_name=Valvula retencao DN50, part_category=Valvula, part_criticality=Alta, warehouse=Almoxarifado Utilidades, supplier_name=Fornecedor Omega
- work_order_id=WO-1004, asset_id=A-300, asset_name=Transportador de correia 01, asset_class=TRANSPORTADOR_CORREIA, failure_code=F-RUIDO_ROLAMENTO, failure_name=Ruido em rolamento, root_cause=Rolamento contaminado ou fim de vida, recommended_action=Substituir rolamento e limpar alojamento, part_id=P-002, part_name=Rolamento 6312, part_category=Rolamento, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1004, asset_id=A-300, asset_name=Transportador de correia 01, asset_class=TRANSPORTADOR_CORREIA, failure_code=F-RUIDO_ROLAMENTO, failure_name=Ruido em rolamento, root_cause=Rolamento contaminado ou fim de vida, recommended_action=Substituir rolamento e limpar alojamento, part_id=P-004, part_name=Correia transportadora 800mm, part_category=Transmissao, part_criticality=Media, warehouse=Almoxarifado Expedicao
- work_order_id=WO-1005, asset_id=A-400, asset_name=Trocador de calor 01, asset_class=TROCADOR_CALOR, failure_code=F-TROCA_TERMICA_BAIXA, failure_name=Baixa troca termica, root_cause=Incrustacao ou obstrucao interna, recommended_action=Programar limpeza quimica e verificar vazao, part_id=P-005, part_name=Jogo de juntas EPDM, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1006, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-001, part_name=Selo mecanico 32mm, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1006, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-002, part_name=Rolamento 6312, part_category=Rolamento, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1006, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-005, part_name=Jogo de juntas EPDM, part_category=Vedacao, part_criticality=Alta, warehouse=Almoxarifado Central
- work_order_id=WO-1006, asset_id=A-100, asset_name=Bomba centrifuga 01, asset_class=BOMBA_CENTRIFUGA, failure_code=F-VIBRACAO, failure_name=Vibracao elevada, root_cause=Desalinhamento desgaste ou folga mecanica, recommended_action=Verificar alinhamento rolamentos e base de fixacao, part_id=P-006, part_name=Valvula retencao DN50, part_category=Valvula, part_criticality=Alta, warehouse=Almoxarifado Utilidades





Inspeção:

Resumo Neo4j Method 02
- Neo4j: neo4j+s://c699a04d.databases.neo4j.io database=c699a04d
- Documentos: 41
- Nos:
  - ['GraphNode', 'Asset']: 5
  - ['GraphNode', 'AssetClass']: 4
  - ['GraphNode', 'Failure']: 5
  - ['GraphNode', 'Part']: 6
  - ['GraphNode', 'Supplier']: 5
  - ['GraphNode', 'Warehouse']: 3
  - ['GraphNode', 'WorkOrder']: 6
- Relacionamentos:
  - CANDIDATE_PART: 17
  - COMPATIBLE_WITH: 9
  - DESCRIBES: 41
  - FOR_ASSET: 6
  - HAS_CLASS: 5
  - HAS_FAILURE: 6
  - MENTIONS_CLASS: 9
  - MENTIONS_PART: 12
  - STOCKED_AT: 6
  - SUPPLIES: 6