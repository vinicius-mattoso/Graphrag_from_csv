# script_ask.py

Comando:

```powershell
python -m method_01.script_ask "quais pecas podem ajudar em queda de pressao no compressor?"
```

Com contexto recuperado:

```powershell
python -m method_01.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context
```

## Objetivo

Este script executa perguntas sobre os dados indexados. Ele combina busca
semantica, travessia por metadados e geracao final com LLM.

## Entrada

Recebe uma pergunta em linguagem natural.

Antes de responder, exige:

- `OPENAI_API_KEY` configurada;
- `documents.jsonl` existente;
- diretorio `chroma/` existente.

## Processamento

1. Inicializa LangSmith tracing com `configure_langsmith`.
2. Carrega o vector store local com `load_vector_store()`.
3. Cria um `GraphRetriever`.
4. Usa busca vetorial para encontrar documentos iniciais.
5. Usa travessia por metadados para expandir contexto relacionado.
6. Envia pergunta e contexto para `ChatOpenAI`.
7. Retorna resposta e fontes.

## Parametros principais

- `--k`: total de documentos finais retornados pelo retriever.
- `--start-k`: documentos iniciais por similaridade vetorial.
- `--max-depth`: profundidade maxima da travessia por metadados.
- `--show-context`: imprime o contexto recuperado antes da resposta.

## Papel na arquitetura GraphRAG

Este script corresponde a fase de consulta. Ele e onde o GraphRAG aparece em
tempo de pergunta:

- O RAG tradicional buscaria documentos apenas por similaridade vetorial.
- O GraphRAG primeiro encontra documentos semanticamente proximos e depois
  expande o conjunto por relacoes estruturais.

Na v1, essas relacoes estruturais sao metadados compartilhados:

- `asset_class`
- `asset_id`
- `failure_code`
- `part_id`
- `warehouse`

Assim, uma pergunta sobre compressor e queda de pressao pode recuperar nao so o
texto parecido, mas tambem documentos ligados ao mesmo ativo, falha, classe de
ativo e pecas candidatas.

## Saida

Mostra:

- resposta em portugues;
- fontes usadas, com `doc_id`, tipo de documento, IDs relevantes e arquivo CSV
  de origem.
