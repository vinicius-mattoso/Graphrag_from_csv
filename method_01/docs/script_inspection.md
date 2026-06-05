# script_inspection.py

Comando:

```powershell
python -m method_01.script_inspection
```

Com menos amostras:

```powershell
python -m method_01.script_inspection --samples 1
```

## Objetivo

Este script audita os artefatos gerados pelo processo de ingestao. Ele permite
verificar se o grafo foi criado como esperado antes de executar perguntas.

## Entrada

Le os arquivos em `data/processed/method_01`:

- `graph_nodes.jsonl`
- `graph_edges.jsonl`
- `documents.jsonl`

Tambem verifica se o diretorio `chroma/` existe.

## Processamento

1. Inicializa LangSmith tracing com `configure_langsmith`.
2. Confirma que os artefatos JSONL existem.
3. Conta nos por tipo.
4. Conta arestas por tipo.
5. Conta arestas por proveniencia.
6. Mostra amostras de nos, arestas e documentos.

## Papel na arquitetura GraphRAG

Este script e a camada de observabilidade local do grafo. Ele nao chama LLM e nao
faz embeddings, mas e importante porque mostra se a parte "Graph" esta correta.

Em GraphRAG, a qualidade da resposta depende da qualidade das relacoes que guiam
a recuperacao. Por isso, antes de confiar em `script_ask.py`, este script ajuda a
responder perguntas como:

- Quantos nos existem por tipo?
- Quantas arestas foram confirmadas pelos CSVs?
- Quantas arestas foram inferidas?
- Os documentos possuem metadados suficientes para travessia?
- O Chroma ja foi populado?

## Saida esperada nos CSVs atuais

Com os dados atuais, a inspecao deve mostrar:

- 34 nos;
- 55 arestas;
- 41 documentos;
- 38 arestas `confirmed`;
- 17 arestas `inferred`.
