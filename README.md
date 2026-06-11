# Graphrag_from_csv

Repositorio de aprendizado para construir GraphRAG a partir de arquivos CSV.

O primeiro caminho de implementacao sera com LangChain. Antes de criar o
grafo, a base bruta em `data/raw` foi revisada para confirmar chaves,
relacionamentos e possiveis pontas soltas.

## Estrutura inicial

- `data/raw`: arquivos CSV originais.
- `data/processed`: espaco reservado para artefatos derivados.
- `method_01`: espaco reservado para a abordagem com LangChain.
- `method_03`: abordagem com Neo4j e Text2Cypher validado.

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

## Metodo 03: Neo4j + Text2Cypher validado

A terceira implementacao esta em [method_03](method_03/README.md).

Ela carrega o grafo no Neo4j e usa uma LLM para propor Cypher a partir da
pergunta do usuario. A query gerada passa por validacao antes de ser executada.

```powershell
python -m method_03.script_ingestion --reset
python -m method_03.script_inspection
python -m method_03.script_ask "quais pecas estao abaixo do estoque minimo?" --show-cypher --show-context
```

Versao monolitica e didatica do fluxo completo:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset
```
