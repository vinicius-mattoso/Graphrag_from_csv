# ontology.py

`ontology.py` define o contrato semantico do grafo. Ele responde:

- quais tipos de nos existem;
- qual propriedade identifica cada no;
- quais relacionamentos sao permitidos;
- quais relacionamentos sao confirmados ou inferidos;
- quais colunas CSV sao obrigatorias.

## Tipos de nos

| Tipo | Chave | Origem | Papel no grafo |
| --- | --- | --- | --- |
| `WorkOrder` | `work_order_id` | `work_orders.csv` | Evento de manutencao consultavel. |
| `Asset` | `asset_id` | `assets.csv` | Equipamento mantido pela operacao. |
| `AssetClass` | `asset_class` | `assets.csv`, `parts.csv` | Ponte entre ativos e pecas. |
| `Failure` | `failure_code` | `failures.csv` | Falha, sintoma, causa e acao. |
| `Part` | `part_id` | `parts.csv` | Peca sobressalente candidata. |
| `Supplier` | `supplier_name` | `suppliers.csv` | Fornecedor deduplicado por nome. |
| `Warehouse` | `warehouse` | `inventory.csv` | Local de estoque. |

## Relacionamentos

| Relacionamento | Origem -> Destino | Proveniencia | Significado |
| --- | --- | --- | --- |
| `FOR_ASSET` | `WorkOrder` -> `Asset` | `confirmed` | Ordem executada para um ativo. |
| `HAS_FAILURE` | `WorkOrder` -> `Failure` | `confirmed` | Ordem associada a uma falha. |
| `HAS_CLASS` | `Asset` -> `AssetClass` | `confirmed` | Ativo pertence a uma classe. |
| `COMPATIBLE_WITH` | `Part` -> `AssetClass` | `confirmed` | Peca compativel com classe. |
| `SUPPLIES` | `Supplier` -> `Part` | `confirmed` | Fornecedor fornece peca. |
| `STOCKED_AT` | `Part` -> `Warehouse` | `confirmed` | Peca tem saldo em almoxarifado. |
| `CANDIDATE_PART` | `WorkOrder` -> `Part` | `inferred` | Peca candidata para uma ordem. |

## Confirmado vs inferido

Relacionamentos `confirmed` vem diretamente de chaves ou colunas dos CSVs.

Relacionamentos `inferred` sao derivados por uma regra. Na v1, a regra e:

```text
asset.asset_class in part.compatible_asset_class
```

Isso gera `CANDIDATE_PART` entre uma ordem de servico e pecas compativeis com a
classe do ativo daquela ordem.

## Relacao com GraphRAG

A ontologia define o "Graph" antes da etapa RAG. Sem ela, os documentos seriam
apenas textos soltos no vector store. Com ela, cada documento tem uma posicao
conceitual no grafo e metadados que permitem travessia.

## Por que manter a ontologia em codigo?

- Fica versionada junto do projeto.
- Pode ser testada automaticamente.
- Evita relacionamentos criados por acidente.
- Facilita migrar para Neo4j em uma proxima versao.
