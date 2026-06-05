# Arquitetura do Metodo 01

O Metodo 01 implementa um GraphRAG local e didatico com LangChain. A ideia e
separar claramente a construcao do grafo, a indexacao vetorial e a geracao de
respostas.

Materiais visuais:

- [infographic_pipeline_executive.svg](infographic_pipeline_executive.svg)
- [infographic_question_retrieval.svg](infographic_question_retrieval.svg)
- [graphrag_flow.svg](graphrag_flow.svg)

## Visao geral

```text
data/raw/*.csv
    |
    v
ontology.py --------+
                    |
                    v
graph_builder.py -> graph_nodes.jsonl
       |          -> graph_edges.jsonl
       |          -> documents.jsonl
       |
       v
vector_store.py -> Chroma local
       |
       v
script_ask.py -> GraphRetriever -> ChatOpenAI -> resposta com fontes

script_inspection.py le graph_nodes.jsonl, graph_edges.jsonl e documents.jsonl.
```

## Camadas

### 1. Dados brutos

Os arquivos em `data/raw` sao a fonte de verdade. Eles representam ativos,
falhas, pecas, estoque, fornecedores e ordens de servico.

### 2. Ontologia

`ontology.py` define quais entidades podem existir no grafo e quais
relacionamentos sao validos. Essa camada evita que a implementacao vire uma
colecao solta de joins.

### 3. Construcao do grafo

`graph_builder.py` le os CSVs, valida integridade e gera:

- nos;
- arestas confirmadas;
- arestas inferidas;
- documentos de recuperacao.

O grafo e salvo em JSONL para que possa ser auditado sem banco externo.

### 4. Vector storage

`vector_store.py` converte os documentos gerados em objetos `Document` do
LangChain e grava embeddings no Chroma local.

Nesta v1, o Chroma e o armazenamento vetorial. Ele nao substitui o grafo; ele
armazena documentos textuais com metadados que representam partes do grafo.

### 5. Graph retrieval

`script_ask.py` usa `GraphRetriever` para combinar:

- busca vetorial por similaridade;
- travessia por metadados compartilhados.

Os metadados usados como arestas de travessia sao:

- `asset_class`;
- `asset_id`;
- `failure_code`;
- `part_id`;
- `warehouse`.

### 6. Geracao

Depois da recuperacao, o contexto e enviado ao `ChatOpenAI`. O LLM nao consulta
os CSVs diretamente; ele responde apenas com o contexto recuperado.

## Por que esta abordagem e GraphRAG?

Um RAG comum buscaria documentos apenas por similaridade. Aqui, a busca inicial
por embeddings e expandida por relacoes estruturais derivadas do grafo.

Exemplo:

1. A pergunta menciona "queda de pressao no compressor".
2. A similaridade pode encontrar `F-QUEDA_PRESSAO` ou a ordem `WO-1003`.
3. A travessia por `failure_code`, `asset_id` e `asset_class` aproxima ativo,
   falha, ordem e pecas compativeis.
4. A resposta final usa esse contexto conectado.

## Limites da v1

- Nao usa Neo4j ou Cypher.
- Nao faz extracao de entidades com LLM.
- Nao infere relacoes complexas por linguagem natural.
- A unica aresta inferida e `CANDIDATE_PART`, baseada em classe de ativo
  compativel.

Esses limites sao intencionais para manter a primeira versao rastreavel.
