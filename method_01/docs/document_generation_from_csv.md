# Como documentos sao gerados a partir dos CSVs

No Metodo 01, "documento" nao significa um arquivo Word, PDF ou CSV novo. Um
documento e uma unidade textual preparada para busca semantica no vector store.

Ele e a ponte entre:

```text
CSV estruturado -> grafo estruturado -> texto buscavel para RAG
```

## Por que gerar documentos?

Os CSVs sao bons para joins, chaves e validacao. Mas embeddings funcionam melhor
com texto natural.

Por isso, cada entidade relevante do grafo vira um texto curto, com metadados
que preservam os IDs e as conexoes do grafo.

O resultado fica em:

```text
data/processed/method_01/documents.jsonl
```

Cada linha desse arquivo tem esta forma:

```json
{
  "id": "failure:F-QUEDA_PRESSAO",
  "page_content": "Texto natural usado no embedding.",
  "metadata": {
    "doc_type": "Failure",
    "failure_code": "F-QUEDA_PRESSAO",
    "source_file": "failures.csv"
  }
}
```

## Exemplo 1: uma falha vira no e documento

Linha original em `failures.csv`:

```csv
failure_code,failure_name,symptom,root_cause,recommended_action,severity
F-QUEDA_PRESSAO,Queda de pressao,Pressao de saida abaixo do limite,Filtro saturado valvula desgastada ou vazamento,Substituir filtro e verificar vedacoes,Alta
```

A ontologia diz que essa linha representa um no `Failure`.

No grafo, ela vira:

```json
{
  "id": "Failure:F-QUEDA_PRESSAO",
  "type": "Failure",
  "key": "F-QUEDA_PRESSAO",
  "properties": {
    "failure_code": "F-QUEDA_PRESSAO",
    "failure_name": "Queda de pressao",
    "symptom": "Pressao de saida abaixo do limite",
    "root_cause": "Filtro saturado valvula desgastada ou vazamento",
    "recommended_action": "Substituir filtro e verificar vedacoes",
    "severity": "Alta"
  }
}
```

Para o RAG, essa mesma informacao vira um documento textual:

```json
{
  "id": "failure:F-QUEDA_PRESSAO",
  "page_content": "Falha F-QUEDA_PRESSAO - Queda de pressao. Sintoma: Pressao de saida abaixo do limite. Causa raiz: Filtro saturado valvula desgastada ou vazamento. Acao recomendada: Substituir filtro e verificar vedacoes. Severidade: Alta.",
  "metadata": {
    "doc_type": "Failure",
    "failure_code": "F-QUEDA_PRESSAO",
    "severity": "Alta",
    "source_file": "failures.csv"
  }
}
```

O texto ajuda a busca semantica. Os metadados ajudam a travessia pelo grafo.

## Exemplo 2: uma ordem de servico e enriquecida por joins

Linha original em `work_orders.csv`:

```csv
work_order_id,asset_id,opened_at,closed_at,maintenance_type,failure_code,status,downtime_hours,description
WO-1003,A-200,2025-06-03,2025-06-04,Corretiva,F-QUEDA_PRESSAO,Fechada,12.0,Queda de pressao com filtro saturado e valvula com desgaste
```

So essa linha ja informa:

- ordem: `WO-1003`;
- ativo: `A-200`;
- falha: `F-QUEDA_PRESSAO`;
- descricao: queda de pressao com filtro saturado e valvula desgastada.

Mas, com os joins do grafo, sabemos mais:

- `A-200` e o ativo `Compressor de ar 01`;
- `A-200` pertence a classe `COMPRESSOR_AR`;
- `F-QUEDA_PRESSAO` e a falha `Queda de pressao`.

Por isso, o documento da ordem fica enriquecido:

```json
{
  "id": "work_order:WO-1003",
  "page_content": "Ordem de servico WO-1003 para o ativo A-200 - Compressor de ar 01, classe COMPRESSOR_AR, local Utilidades / Sala 3. Tipo de manutencao Corretiva. Status Fechada. Aberta em 2025-06-03 e fechada em 2025-06-04. Falha F-QUEDA_PRESSAO - Queda de pressao. Descricao: Queda de pressao com filtro saturado e valvula com desgaste. Downtime: 12.0 horas.",
  "metadata": {
    "doc_type": "WorkOrder",
    "work_order_id": "WO-1003",
    "asset_id": "A-200",
    "asset_class": "COMPRESSOR_AR",
    "failure_code": "F-QUEDA_PRESSAO",
    "status": "Fechada",
    "maintenance_type": "Corretiva",
    "source_file": "work_orders.csv"
  }
}
```

Esse enriquecimento e importante porque a pergunta do usuario pode mencionar
"compressor", mesmo que a linha original da ordem so tenha `asset_id=A-200`.

## Exemplo 3: uma peca vira documento por classe compativel

Linha original em `parts.csv`:

```csv
part_id,part_name,category,compatible_asset_class,criticality,lead_time_days,unit_cost
P-006,Valvula retencao DN50,Valvula,COMPRESSOR_AR;BOMBA_CENTRIFUGA,Alta,25,780.00
```

Essa peca e compativel com duas classes:

- `COMPRESSOR_AR`;
- `BOMBA_CENTRIFUGA`.

Por isso, ela pode gerar documentos por classe compativel. Para compressor:

```json
{
  "id": "part:P-006:COMPRESSOR_AR",
  "page_content": "Peca P-006 - Valvula retencao DN50. Categoria Valvula. Compativel com a classe COMPRESSOR_AR. Criticidade Alta. Lead time 25 dias. Custo unitario 780.00. Estoque 0 no Almoxarifado Utilidades, minimo 2, ponto de reposicao 4. Fornecedores: Fornecedor Omega preferencial=false entrega_media=24 dias confiabilidade=0.69.",
  "metadata": {
    "doc_type": "Part",
    "part_id": "P-006",
    "asset_class": "COMPRESSOR_AR",
    "category": "Valvula",
    "criticality": "Alta",
    "source_file": "parts.csv"
  }
}
```

Repare que esse documento tambem inclui dados de estoque e fornecedor. Esses
dados nao estao todos em `parts.csv`; eles vieram dos joins com:

- `inventory.csv`;
- `suppliers.csv`.

## O que vai para texto e o que vai para metadata?

Regra pratica da v1:

- `page_content`: texto que ajuda o embedding a entender significado.
- `metadata`: IDs e campos que ajudam o GraphRetriever a conectar documentos.

Exemplo:

```text
page_content:
"Falha de queda de pressao causada por filtro saturado ou valvula desgastada"

metadata:
failure_code=F-QUEDA_PRESSAO
asset_class=COMPRESSOR_AR
part_id=P-006
```

O texto responde: "isso parece com a pergunta?"

Os metadados respondem: "isso se conecta com quais outros documentos?"

## Como isso aparece na pergunta

Pergunta:

```text
quais pecas podem ajudar em queda de pressao no compressor?
```

O processo fica:

```text
1. Busca semantica
   encontra documentos parecidos com "queda de pressao" e "compressor".

2. Travessia por metadados
   conecta failure_code=F-QUEDA_PRESSAO,
   asset_class=COMPRESSOR_AR,
   work_order_id=WO-1003,
   part_id=P-003 e part_id=P-006.

3. Contexto final
   junta falha, ordem, classe do ativo, pecas, estoque e fornecedor.

4. Resposta da LLM
   recomenda P-006 e P-003 com base nas fontes recuperadas.
```

## Resumo

Os tres artefatos tem papeis diferentes:

| Artefato | Papel |
| --- | --- |
| `graph_nodes.jsonl` | Guarda as entidades estruturadas do grafo. |
| `graph_edges.jsonl` | Guarda as relacoes entre entidades. |
| `documents.jsonl` | Guarda textos buscaveis com metadados conectados ao grafo. |

O documento e, portanto, a camada que permite que o grafo estruturado seja usado
por um RAG semantico.
