# Graphrag_from_csv

Repositorio de aprendizado para construir GraphRAG a partir de arquivos CSV.

O primeiro caminho de implementacao sera com LangChain. Antes de criar o
grafo, a base bruta em `data/raw` foi revisada para confirmar chaves,
relacionamentos e possiveis pontas soltas.

## Estrutura inicial

- `data/raw`: arquivos CSV originais.
- `data/processed`: espaco reservado para artefatos derivados.
- `method_01`: espaco reservado para a abordagem com LangChain.
- `method_02`: abordagem com Neo4j, Cypher e vector index.

## Revisao dos dados

A revisao inicial dos CSVs esta em [data/DATA_REVIEW.md](data/DATA_REVIEW.md).

## Metodo 01: LangChain local

A primeira implementacao esta em [method_01](method_01/README.md).

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Gere os artefatos do grafo sem chamar OpenAI:

```powershell
python -m method_01.script_ingestion --skip-vector-store
```

Gere o indice completo com Chroma e embeddings:

```powershell
python -m method_01.script_ingestion
```

Inspecione o grafo:

```powershell
python -m method_01.script_inspection
```

Pergunte ao GraphRAG:

```powershell
python -m method_01.script_ask "quais pecas podem ajudar em queda de pressao no compressor?"
```

Explore pelo app Streamlit:

```powershell
streamlit run app_method_01/Home.py
```

## Metodo 02: Neo4j + Cypher + Vector Index

A segunda implementacao esta em [method_02](method_02/README.md).

Ela persiste o grafo no Neo4j e combina Neo4j Vector Index com consultas Cypher
controladas para recuperar subgrafos antes da resposta da LLM.

```powershell
python -m method_02.script_ingestion --reset
python -m method_02.script_inspection
python -m method_02.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context
```
