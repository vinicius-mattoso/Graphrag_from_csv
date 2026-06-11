"""Geracao Text2Cypher usando schema controlado e exemplos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from method_03.schema import build_examples_text, build_schema_text
from method_03.settings import get_method_03_chat_model_name
from method_03.validator import coerce_parameters


SYSTEM_PROMPT = """Voce converte perguntas de manutencao industrial em Cypher somente leitura.
Responda apenas com JSON valido, sem markdown e sem texto extra.
A query deve usar somente o schema fornecido, deve conter RETURN e LIMIT, e nunca pode alterar o banco.
Use parametros no campo "parameters" quando houver valores filtraveis."""


HUMAN_PROMPT = """Schema disponivel:
{schema}

Regras obrigatorias:
- Use apenas MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT e SKIP.
- Nao use CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, LOAD CSV, CALL, APOC, FOREACH ou USE.
- Nao use labels, relacionamentos ou propriedades fora do schema.
- Inclua LIMIT menor ou igual a {max_rows}.
- Para estoque, use propriedades da relacao STOCKED_AT.

Exemplos:
{examples}

Pergunta do usuario:
{question}

Retorne JSON neste formato:
{{
  "cypher": "MATCH ... RETURN ... LIMIT {max_rows}",
  "parameters": {{}},
  "reasoning_summary": "Resumo curto do caminho usado no grafo"
}}"""


@dataclass(frozen=True)
class CypherGeneration:
    cypher: str
    parameters: dict[str, Any]
    reasoning_summary: str
    raw_response: str


def generate_cypher(question: str, max_rows: int = 50) -> CypherGeneration:
    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencias ausentes: instale langchain-core e langchain-openai "
            "para gerar Text2Cypher."
        ) from exc

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )
    model = ChatOpenAI(model=get_method_03_chat_model_name(), temperature=0)
    chain = prompt | model | StrOutputParser()
    raw_response = chain.invoke(
        {
            "schema": build_schema_text(),
            "examples": build_examples_text(),
            "question": question,
            "max_rows": max_rows,
        }
    )
    payload = parse_generation_response(raw_response)
    return CypherGeneration(
        cypher=str(payload.get("cypher", "")).strip(),
        parameters=coerce_parameters(payload.get("parameters")),
        reasoning_summary=str(payload.get("reasoning_summary", "")).strip(),
        raw_response=raw_response,
    )


def parse_generation_response(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        text = _strip_code_fence(text)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError(f"Resposta Text2Cypher nao contem JSON valido: {raw_response}")
        payload = json.loads(text[start : end + 1])

    if not isinstance(payload, dict):
        raise RuntimeError("Resposta Text2Cypher deve ser um objeto JSON.")
    return payload


def _strip_code_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
