"""Montagem do grafo LangGraph do ecossistema PoneIU.

Topologia (ver docs/ARQUITETURA.md para o diagrama e a discussão teórica):

    START -> agente_geral --(retomar_renegociacao)--> agente_renegociacao -> END
                          \\--(outro / off-topic)-----------------------> END

O `agente_geral` funciona como um supervisor/gatekeeper leve: ele decide, a
cada turno, se a conversa segue para o especialista de renegociação ou se
encerra com uma resposta humanizada. O checkpointer (`MemorySaver`) faz o
grafo se comportar como um chatbot com memória de conversa por `thread_id`
— cada carrinho abandonado usa seu próprio thread, isolando o estado de
diferentes produtos/conversas.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.agente_geral import nodo_agente_geral, rotear_apos_triagem
from src.agents.agente_renegociacao import nodo_agente_renegociacao
from src.agents.state import AgentState


def construir_grafo():
    builder = StateGraph(AgentState)

    builder.add_node("agente_geral", nodo_agente_geral)
    builder.add_node("agente_renegociacao", nodo_agente_renegociacao)

    builder.add_edge(START, "agente_geral")
    builder.add_conditional_edges(
        "agente_geral",
        rotear_apos_triagem,
        {"renegociacao": "agente_renegociacao", "fim": END},
    )
    builder.add_edge("agente_renegociacao", END)

    return builder.compile(checkpointer=MemorySaver())


@lru_cache(maxsize=1)
def obter_grafo():
    """Compila o grafo uma única vez por processo (cache simples).

    Em Streamlit isso é chamado a cada rerun do script; o `lru_cache` evita
    recompilar e, principalmente, evita recriar o `MemorySaver` (que perderia
    o histórico de conversas em memória a cada interação do usuário).
    """

    return construir_grafo()
