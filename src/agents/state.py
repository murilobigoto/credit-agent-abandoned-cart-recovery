"""Estado compartilhado do grafo LangGraph e definição dos estágios da
conversa de renegociação.

O grafo é invocado uma vez por mensagem do cliente (padrão "chatbot
turn-by-turn" do LangGraph). O `Estagio` é o que permite que o nó do agente
de renegociação saiba, a cada nova chamada, em qual ponto da conversa ele
parou — sem isso, cada invocação seria "amnésica".
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Estagio(str, Enum):
    """Máquina de estados da conversa dentro do agente de renegociação."""

    INICIO = "inicio"
    AGUARDANDO_VALOR = "aguardando_valor"
    AGUARDANDO_ESCOLHA = "aguardando_escolha"
    CONCLUIDO = "concluido"
    ENCERRADO_HUMANO = "encerrado_humano"


class AgentState(TypedDict, total=False):
    """Estado persistido pelo checkpointer do LangGraph (por thread_id)."""

    # `add_messages` faz o merge incremental do histórico a cada invocação,
    # em vez de sobrescrever a lista inteira — é o reducer padrão do
    # LangGraph para conversas.
    messages: Annotated[list[BaseMessage], add_messages]

    estagio: str

    # Os campos abaixo guardam dicts simples (via `.to_dict()` dos modelos em
    # `src/domain/models.py`), nunca dataclasses/enums diretamente — o
    # checkpointer do LangGraph serializa o estado via msgpack, então tudo
    # que cruza essa fronteira precisa ser um tipo nativo serializável.
    carrinho: dict | None
    valor_pretendido: float | None
    ofertas_apresentadas: list[dict]
    oferta_escolhida: dict | None
    protocolo_confirmacao: str | None
