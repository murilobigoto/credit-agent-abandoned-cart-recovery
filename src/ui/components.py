"""Componentes visuais da tela "Solução de dívidas" do PoneIU.

Reproduz a estrutura da referência de design fornecida (tela real de um
banco): barra superior, selo + título, card de destaque ("Desenrola") e a
seção "Formas de reorganizar" com a lista de carrinhos abandonados que o
cliente pode retomar.
"""

from __future__ import annotations

import streamlit as st
from langchain_core.messages import AIMessage

from src.agents import orquestrador
from src.agents.state import Estagio
from src.config import BANCO_NOME, BANCO_PROGRAMA_DESTAQUE, BANCO_SLOGAN
from src.domain.models import CarrinhoAbandonado, Produto
from src.utils import format_brl

_ICONE_PRODUTO = {
    Produto.CARTAO: "💳",
    Produto.LIC: "💵",
    Produto.PRONAMPE: "🏢",
}


def render_header() -> None:
    st.markdown(
        """
        <div class="poneiu-topbar">
            <span title="Voltar">‹</span>
            <span style="font-weight:700; font-size:1rem; letter-spacing:0.04em;">PONEIU</span>
            <span title="Ajuda">❓</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <div style="font-size:2.2rem;">🤝</div>
        <div class="poneiu-eyebrow">Solução de dívidas</div>
        <div class="poneiu-hero-title">{BANCO_SLOGAN}</div>
        """,
        unsafe_allow_html=True,
    )


def render_desenrola_card() -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.9rem;">
                <div style="font-size:1.8rem;">🟢</div>
                <div>
                    <div class="poneiu-card-title">{BANCO_PROGRAMA_DESTAQUE}</div>
                    <div class="poneiu-card-desc">Entenda como funciona e quem pode participar.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)


def render_formas_reorganizar(carrinhos: list[CarrinhoAbandonado]) -> None:
    st.markdown('<div class="poneiu-section-title">Formas de reorganizar</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            """
            <span class="poneiu-badge-novo">Novo</span>
            <div class="poneiu-card-title">Parcelar faturas</div>
            <div class="poneiu-card-desc">
                Antecipe ou parcele as faturas do seu cartão e tenha um alívio no mês.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

        for indice, carrinho in enumerate(carrinhos):
            if indice > 0:
                st.markdown('<div class="poneiu-divider"></div>', unsafe_allow_html=True)

            icone = _ICONE_PRODUTO.get(carrinho.produto, "📄")
            rotulo = f"{icone}  {carrinho.titulo_lista}"
            if st.button(rotulo, key=f"abrir_chat_{carrinho.cart_id}", use_container_width=True):
                st.session_state["carrinho_ativo_id"] = carrinho.cart_id
            st.caption(
                f"Simulado em {carrinho.oferta_simulada.data_simulacao} · "
                f"saldo de {format_brl(carrinho.saldo_devedor)} · "
                f"{carrinho.dias_em_atraso} dias em atraso — não finalizado"
            )


def _renderizar_historico(mensagens: list) -> None:
    for mensagem in mensagens:
        eh_ia = isinstance(mensagem, AIMessage)
        # A mensagem sintética de abertura ("Quero retomar minha renegociação.")
        # é um artifício de orquestração (ver src/agents/orquestrador.py) e não
        # deve aparecer como se o cliente a tivesse digitado.
        if not eh_ia and mensagem.content == orquestrador.MENSAGEM_ABERTURA:
            continue
        papel = "assistant" if eh_ia else "user"
        avatar = "🏦" if eh_ia else "🧑"
        with st.chat_message(papel, avatar=avatar):
            # Escapa "$" antes de renderizar: o Markdown do Streamlit trata
            # pares de "$" como delimitadores de LaTeX, e nossas mensagens
            # citam valores em reais ("R$ 1.234,56") repetidas vezes — sem o
            # escape, o trecho entre dois "R$" vira uma fórmula quebrada.
            st.write(str(mensagem.content).replace("$", "\\$"))


def abrir_chat_dialog(carrinho: CarrinhoAbandonado) -> None:
    """Abre a "janelinha" conversacional ligada ao agente de renegociação.

    Usa `st.session_state` para decidir se a conversa deste `cart_id` já foi
    iniciada no grafo (e, portanto, só precisamos ler o estado já
    persistido pelo checkpointer) ou se precisamos chamar
    `orquestrador.iniciar_conversa` pela primeira vez.
    """

    chave_iniciado = f"conversa_iniciada_{carrinho.cart_id}"

    @st.dialog(f"💬 Assistente {BANCO_NOME} · {carrinho.produto.rotulo}", width="large")
    def _dialog() -> None:
        if not st.session_state.get(chave_iniciado):
            orquestrador.iniciar_conversa(carrinho)
            st.session_state[chave_iniciado] = True

        estado = orquestrador.obter_estado(carrinho.cart_id) or {}
        mensagens = estado.get("messages", [])

        with st.container(height=420):
            _renderizar_historico(mensagens)

        estagio = estado.get("estagio")
        if estagio == Estagio.ENCERRADO_HUMANO.value:
            st.markdown(
                '<div class="poneiu-encerrado-banner">Conversa encerrada pelo assistente. '
                "Digite novamente se quiser retomar a renegociação.</div>",
                unsafe_allow_html=True,
            )
        elif estagio == Estagio.CONCLUIDO.value:
            protocolo = estado.get("protocolo_confirmacao")
            st.markdown(
                f'<div class="poneiu-concluido-banner">Renegociação concluída · '
                f"protocolo {protocolo}</div>",
                unsafe_allow_html=True,
            )

        texto = st.chat_input("Digite sua mensagem para o PoneIU...")
        if texto:
            orquestrador.enviar_mensagem(carrinho.cart_id, texto)
            st.rerun()

        if st.button("Fechar conversa", use_container_width=True, key=f"fechar_{carrinho.cart_id}"):
            st.session_state["carrinho_ativo_id"] = None
            st.session_state.pop(chave_iniciado, None)
            st.rerun()

    _dialog()
