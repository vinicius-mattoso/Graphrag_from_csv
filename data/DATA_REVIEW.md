# Revisao dos CSVs brutos

Fonte: `data/raw`

Data da revisao: 2026-06-04

## Arquivos encontrados

| Arquivo | Linhas | Entidade principal | Chave candidata |
| --- | ---: | --- | --- |
| `assets.csv` | 5 | Ativos industriais | `asset_id` |
| `failures.csv` | 5 | Modos/codigos de falha | `failure_code` |
| `parts.csv` | 6 | Pecas sobressalentes | `part_id` |
| `inventory.csv` | 6 | Estoque por peca | `part_id` |
| `suppliers.csv` | 6 | Fornecedores por peca | `supplier_id` |
| `work_orders.csv` | 6 | Ordens de servico | `work_order_id` |

## Relacionamentos validados

| Relacionamento | Status | Observacao |
| --- | --- | --- |
| `work_orders.asset_id` -> `assets.asset_id` | OK | Todas as ordens apontam para ativos existentes. |
| `work_orders.failure_code` -> `failures.failure_code` | OK | Todas as ordens apontam para codigos de falha existentes. |
| `inventory.part_id` -> `parts.part_id` | OK | Todos os itens de estoque apontam para pecas existentes. |
| `suppliers.part_id` -> `parts.part_id` | OK | Todos os fornecedores apontam para pecas existentes. |
| `parts.compatible_asset_class` -> `assets.asset_class` | OK | Todas as classes compativeis existem em `assets.csv`. |

## Checagens de qualidade

- Nao foram encontrados IDs duplicados nas chaves candidatas.
- Nao foram encontrados valores ausentes nas chaves e referencias principais.
- Nao foram encontrados registros orfaos nas relacoes formais.
- A ordem `WO-1005` esta aberta e possui `closed_at` vazio, coerente com o status `Aberta`.
- As datas de fechamento das ordens fechadas nao antecedem as datas de abertura.
- Existem itens abaixo do estoque minimo: `P-001`, `P-003` e `P-006`.

## Leitura para GraphRAG

O conjunto esta conectado e e adequado para montar o primeiro grafo:

- `WorkOrder` conecta ocorrencias de manutencao a `Asset` e `Failure`.
- `Asset` conecta o historico operacional a uma classe de ativo.
- `Part` conecta sobressalentes a classes de ativos por `compatible_asset_class`.
- `Inventory` e `Supplier` enriquecem cada peca com disponibilidade, lead time, custo e confiabilidade.

Nao ha uma relacao explicita entre `work_orders` e `parts`. Essa ligacao deve ser
tratada como inferida ou semantica, usando:

- classe do ativo da ordem de servico;
- descricao textual da ordem;
- sintomas, causas-raiz e acoes recomendadas da falha;
- compatibilidade declarada das pecas.

Para o grafo, convem separar arestas confirmadas de arestas inferidas. Exemplo:

- `(:WorkOrder)-[:FOR_ASSET]->(:Asset)`
- `(:WorkOrder)-[:HAS_FAILURE]->(:Failure)`
- `(:Asset)-[:HAS_CLASS]->(:AssetClass)`
- `(:Part)-[:COMPATIBLE_WITH]->(:AssetClass)`
- `(:Supplier)-[:SUPPLIES]->(:Part)`
- `(:Part)-[:STOCKED_AT]->(:Warehouse)`
- `(:WorkOrder)-[:CANDIDATE_PART]->(:Part)` apenas quando inferida pela etapa LangChain/GraphRAG.

## Conclusao

Nao ha pontas soltas de integridade referencial nos CSVs atuais. O principal ponto
de modelagem para o GraphRAG e explicitar que a relacao entre ordem de servico e
pecas nao vem pronta no CSV: ela sera derivada por regras e/ou recuperacao
semantica.
