# app_method_01

App Streamlit multipage para explorar o Metodo 01.

## Rodar

```powershell
streamlit run app_method_01/Home.py
```

Ou usando diretamente o Python da `.venv`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_method_01/Home.py
```

## Paginas

- `Home`: visao geral, status dos artefatos e diagrama.
- `Ingestao`: valida CSVs, gera JSONL e popula Chroma.
- `Grafo`: explora nos, arestas, proveniencia e diagrama Graphviz.
- `Documentos`: explora `documents.jsonl` e metadados.
- `Q&A`: executa pergunta com GraphRetriever + ChatOpenAI.

## Dependencias dos artefatos

- Para `Home`, `Grafo` e `Documentos`, rode pelo menos:

```powershell
python -m method_01.script_ingestion --skip-vector-store
```

- Para `Q&A`, rode a ingestao completa:

```powershell
python -m method_01.script_ingestion
```

Tambem e necessario configurar `OPENAI_API_KEY` no `.env`.
