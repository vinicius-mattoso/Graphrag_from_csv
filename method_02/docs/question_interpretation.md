# Interpretacao do teste de pergunta do Metodo 02

Este documento interpreta o arquivo `method_02/test/question.md`, que registra
uma execucao do Metodo 02 com Neo4j, vector index, Cypher controlado e LLM.

Imagem executiva do processo: [question_flow_executive.svg](question_flow_executive.svg).

Observacao: o arquivo de teste aparenta ter caracteres acentuados exibidos com
encoding incorreto. A interpretacao abaixo usa texto normalizado, sem acentos,
para facilitar a leitura.

## Resumo executivo

A pergunta testada foi:

```text
quais pecas podem ajudar em queda de pressao no compressor?
```

Em linguagem de negocio, a pergunta pede:

- identificar a falha operacional: queda de pressao;
- restringir o contexto ao tipo de ativo: compressor;
- encontrar pecas compativeis que ajudem a tratar a causa raiz;
- considerar estoque, criticidade e fornecedor quando existirem no grafo.

O resultado final recomendou duas pecas:

| Peca | ID | Motivo principal | Situacao de estoque |
| --- | --- | --- | --- |
| Filtro coalescente 1pol | `P-003` | A causa raiz menciona filtro saturado | Estoque 1, minimo 3 |
| Valvula retencao DN50 | `P-006` | A causa raiz menciona valvula desgastada ou vazamento | Estoque 0, minimo 2 |

A resposta faz sentido porque a falha `F-QUEDA_PRESSAO` aponta para a causa
raiz "filtro saturado, valvula desgastada ou vazamento", e o ativo envolvido
pertence a classe `COMPRESSOR_AR`.

## O que o comando executa

O teste roda:

```powershell
python -m method_02.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context
```

Esse comando faz duas coisas:

- gera uma resposta final em linguagem natural;
- imprime o contexto usado pela resposta, por causa do `--show-context`.

O contexto exibido tem duas partes:

- `Vector results`: documentos encontrados por similaridade semantica no Neo4j
  Vector Index.
- `Subgraph rows`: linhas estruturadas retornadas por uma consulta Cypher
  controlada sobre o grafo.

## Como o Metodo 02 interpreta a pergunta

A pergunta contem dois sinais fortes:

| Termo da pergunta | Interpretacao no grafo |
| --- | --- |
| `queda de pressao` | falha `F-QUEDA_PRESSAO` |
| `compressor` | classe de ativo `COMPRESSOR_AR` |
| `pecas` | busca por nos `Part` conectados ao contexto de manutencao |

Esses sinais viram sementes de recuperacao. A busca vetorial ajuda a encontrar
documentos semanticamente parecidos, enquanto o Cypher usa o grafo para
atravessar relacionamentos reais.

## Leitura dos vector results

Os resultados vetoriais mostram os documentos mais proximos da pergunta.
Os itens mais importantes para este caso sao:

| Documento | Por que importa |
| --- | --- |
| `failure:F-QUEDA_PRESSAO` | Confirma a falha de queda de pressao e sua causa raiz |
| `asset_class:COMPRESSOR_AR` | Confirma o recorte por compressor |
| `work_order:WO-1003` | Liga a falha ao ativo `A-200`, Compressor de ar 01 |
| `part:P-003:COMPRESSOR_AR` | Peca compativel com compressor e coerente com filtro saturado |
| `part:P-006:COMPRESSOR_AR` | Peca compativel com compressor e coerente com valvula/vazamento |

Tambem aparecem pecas de `BOMBA_CENTRIFUGA`, como `P-001`, `P-005` e `P-002`.
Isso acontece porque a busca vetorial mede proximidade textual, nao aplica
sozinha a regra final de negocio. Esses itens devem ser tratados como candidatos
brutos, nao como resposta final.

## Leitura do subgrafo

Para responder corretamente, o caminho relevante do grafo e:

```text
F-QUEDA_PRESSAO
  <- HAS_FAILURE -
WO-1003
  - FOR_ASSET ->
A-200
  - HAS_CLASS ->
COMPRESSOR_AR
  <- COMPATIBLE_WITH -
P-003 e P-006
```

Na saida do teste, as linhas mais importantes sao:

| Ordem | Ativo | Classe | Falha | Peca | Fornecedor |
| --- | --- | --- | --- | --- | --- |
| `WO-1003` | `A-200` Compressor de ar 01 | `COMPRESSOR_AR` | `F-QUEDA_PRESSAO` | `P-003` Filtro coalescente 1pol | Fornecedor Gamma |
| `WO-1003` | `A-200` Compressor de ar 01 | `COMPRESSOR_AR` | `F-QUEDA_PRESSAO` | `P-006` Valvula retencao DN50 | Fornecedor Omega |

Essas duas linhas sao as evidencias principais da resposta.

## Por que a resposta final escolhe P-003 e P-006

A resposta combina tres camadas de evidencia:

- A falha `F-QUEDA_PRESSAO` tem causa raiz relacionada a filtro, valvula e
  vazamento.
- A ordem `WO-1003` liga essa falha ao ativo `A-200`, que e um compressor.
- As pecas `P-003` e `P-006` sao compativeis com a classe `COMPRESSOR_AR`.

O resultado nao e apenas uma busca por palavra-chave. Ele depende da conexao
entre falha, ordem de servico, ativo, classe tecnica, peca, estoque e fornecedor.

## O que a inspecao confirma

A secao `Inspecao` no teste mostra que o Neo4j foi carregado com:

- 41 documentos `GraphDocument`;
- 34 nos de dominio;
- 6 ordens de servico;
- 6 pecas;
- 5 falhas;
- relacionamentos como `FOR_ASSET`, `HAS_FAILURE`, `HAS_CLASS`,
  `COMPATIBLE_WITH`, `STOCKED_AT`, `SUPPLIES` e `CANDIDATE_PART`.

Isso confirma que o Method 02 esta consultando um grafo persistido, nao apenas
um arquivo local ou uma lista de textos.

## Ponto de atencao

O contexto de `Subgraph rows` no teste tambem traz linhas de bombas,
transportador e trocador de calor. Para leitura executiva, essas linhas devem
ser vistas como ruido de contexto. O caminho relevante para a pergunta e apenas
o que combina:

```text
failure_code = F-QUEDA_PRESSAO
asset_class = COMPRESSOR_AR
```

Para uma versao de producao, vale refinar a consulta Cypher de recuperacao para
reduzir esse ruido antes de enviar o contexto para a LLM. Isso melhora custo,
precisao e auditabilidade da resposta.

## Conclusao

O teste demonstra o papel do GraphRAG no Metodo 02:

- a busca vetorial encontra documentos semanticamente proximos;
- o grafo organiza o raciocinio por relacionamentos reais;
- o Cypher recupera evidencias estruturadas;
- a LLM transforma essas evidencias em uma resposta operacional.

Neste exemplo, a resposta correta e recomendar `P-003` e `P-006` para queda de
pressao em compressor, com atencao especial ao baixo estoque das duas pecas.
