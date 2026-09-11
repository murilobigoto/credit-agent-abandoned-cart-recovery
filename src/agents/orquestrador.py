"""Fachada usada pela interface Streamlit para conversar com o grafo.

Isola a UI dos detalhes de `thread_id`, `checkpointer` e formato de estado
do LangGraph — a camada de apresentação só conhece estas duas funções.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.agents.graph import obter_grafo
from src.agents.state import AgentState, Estagio
from src.domain.models import CarrinhoAbandonado

MENSAGEM_ABERTURA = "Quero retomar minha renegociação."


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def iniciar_conversa(carrinho: CarrinhoAbandonado) -> AgentState:
    """Abre a "janelinha" de chat para um carrinho abandonado específico.

    O clique do cliente no item da lista (na tela de soluções de dívidas)
    já É a manifestação de intenção de retomar a renegociação — por isso a
    primeira mensagem enviada ao grafo é sintética, equivalente a o cliente
    ter digitado "quero retomar". Isso mantém o `agente_geral` como porta de
    entrada única do grafo, sem precisar de um caminho especial na UI.

    Idempotente: se essa thread (cart_id) já tem histórico no checkpointer —
    por exemplo, o cliente fechou e reabriu a janelinha, ou o navegador deu
    reload — não reenvia a saudação, só devolve o estado já existente. Sem
    isso, cada reabertura duplicaria a mensagem de boas-vindas.
    """

    estado_existente = obter_estado(carrinho.cart_id)
    if estado_existente and estado_existente.get("messages"):
        return estado_existente

    grafo = obter_grafo()
    entrada: AgentState = {
        "messages": [HumanMessage(content=MENSAGEM_ABERTURA)],
        "estagio": Estagio.INICIO.value,
        "carrinho": carrinho.to_dict(),
        "valor_pretendido": None,
        "ofertas_apresentadas": [],
        "oferta_escolhida": None,
        "protocolo_confirmacao": None,
    }
    return grafo.invoke(entrada, config=_config(carrinho.cart_id))


def enviar_mensagem(cart_id: str, texto_cliente: str) -> AgentState:
    """Envia uma nova mensagem do cliente para uma conversa já iniciada."""

    grafo = obter_grafo()
    entrada = {"messages": [HumanMessage(content=texto_cliente)]}
    return grafo.invoke(entrada, config=_config(cart_id))


def obter_estado(cart_id: str) -> AgentState | None:
    """Recupera o estado atual (para redesenhar a UI após um rerun)."""

    grafo = obter_grafo()
    snapshot = grafo.get_state(_config(cart_id))
    return snapshot.values if snapshot else None
