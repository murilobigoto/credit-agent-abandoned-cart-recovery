"""Componentes visuais da tela "Solução de dívidas" do PoneIU.

Reproduz a estrutura da referência de design fornecida (tela real de um
banco): barra superior, selo + título, card de destaque ("Desenrola") e a
seção "Formas de reorganizar" com a lista de carrinhos abandonados que o
cliente pode retomar.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st
from langchain_core.messages import AIMessage

from src.agents import orquestrador
from src.agents.state import Estagio
from src.config import BANCO_NOME, BANCO_PROGRAMA_DESTAQUE, BANCO_SLOGAN
from src.domain.models import CarrinhoAbandonado, OfertaRenegociacao, Produto
from src.utils import format_brl, formatar_data_relativa

_ICONE_PRODUTO = {
    Produto.CARTAO: "💳",
    Produto.LIC: "💵",
    Produto.PRONAMPE: "🏢",
}

_PASSOS_RENEGOCIACAO = ["Valor mensal", "Escolher oferta", "Confirmação"]


def render_header() -> None:
    # Continua em HTML puro (sem st.columns): o `block-container` deste app é
    # deliberadamente estreito (tela de celular) e o layout de colunas nativo
    # do Streamlit empilha verticalmente abaixo de ~640px de viewport — o que
    # quebraria a barra superior em 3 linhas em vez de 1. A ajuda interativa
    # mora em `render_ajuda()`, um expander de largura total (imune a esse
    # problema).
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


def render_hero(carrinhos: list[CarrinhoAbandonado] | None = None) -> None:
    primeiro_nome = carrinhos[0].cliente_nome.split()[0] if carrinhos else None
    saudacao = f'<div class="poneiu-greeting">Olá, {primeiro_nome} 👋</div>' if primeiro_nome else ""
    st.markdown(
        f"""
        <div style="font-size:2.2rem;">🤝</div>
        {saudacao}
        <div class="poneiu-eyebrow">Solução de dívidas</div>
        <div class="poneiu-hero-title">{BANCO_SLOGAN}</div>
        <div class="poneiu-trust-row">
            <span>🔒 Ambiente seguro</span>
            <span>📵 Não afeta seu score</span>
            <span>⚡ Simulação em segundos</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ajuda() -> None:
    with st.expander("❓ Central de ajuda"):
        st.markdown(
            "- **Como funciona?** Toque em uma simulação não finalizada e continue de onde parou.\n"
            "- **Preciso pagar algo agora?** Não — aqui você só simula e confirma novas condições.\n"
            "- **Meus dados estão seguros?** Sim, o ambiente é protegido e nada é compartilhado "
            "com terceiros.\n"
            "- **Não estou conseguindo pagar nada.** Conte para o assistente — ele vai te ouvir "
            "com empatia."
        )


def render_resumo(carrinhos: list[CarrinhoAbandonado], maior_desconto_percentual: float) -> None:
    if not carrinhos:
        return

    total_pendente = sum(carrinho.saldo_devedor for carrinho in carrinhos)
    rotulo_qtd = "simulação" if len(carrinhos) == 1 else "simulações"

    st.markdown(
        f"""
        <div class="poneiu-stat-row">
            <div class="poneiu-stat-tile">
                <div class="poneiu-stat-value">{format_brl(total_pendente)}</div>
                <div class="poneiu-stat-label">Total em pendências</div>
            </div>
            <div class="poneiu-stat-tile">
                <div class="poneiu-stat-value">{len(carrinhos)}</div>
                <div class="poneiu-stat-label">{rotulo_qtd} em aberto</div>
            </div>
            <div class="poneiu-stat-tile poneiu-stat-tile-destaque">
                <div class="poneiu-stat-value">até {maior_desconto_percentual:.0f}%</div>
                <div class="poneiu-stat-label">de desconto disponível</div>
            </div>
        </div>
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
        with st.expander("Saiba mais"):
            st.markdown(
                "- Redução dos juros e encargos acumulados na dívida em atraso.\n"
                "- Parcelamento facilitado, sem burocracia e sem sair do app.\n"
                "- Sua simulação fica salva mesmo se você sair no meio — é só voltar aqui.\n"
                "- Atendimento humano disponível caso você prefira conversar com uma pessoa."
            )
    st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)


def _chip_urgencia(dias_em_atraso: int) -> str:
    if dias_em_atraso > 60:
        classe, icone, rotulo = "critico", "🔴", "Crítico"
    elif dias_em_atraso > 30:
        classe, icone, rotulo = "urgente", "🟠", "Urgente"
    else:
        classe, icone, rotulo = "atencao", "🟡", "Atenção"
    return f'<span class="poneiu-chip poneiu-chip-{classe}">{icone} {rotulo}</span>'


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
            col_botao, col_chip = st.columns([3, 1])
            with col_botao:
                if st.button(rotulo, key=f"abrir_chat_{carrinho.cart_id}", use_container_width=True):
                    st.session_state["carrinho_ativo_id"] = carrinho.cart_id
            with col_chip:
                st.markdown(
                    f'<div class="poneiu-chip-cell">{_chip_urgencia(carrinho.dias_em_atraso)}</div>',
                    unsafe_allow_html=True,
                )
            data_relativa = formatar_data_relativa(carrinho.oferta_simulada.data_simulacao)
            st.caption(
                f"Simulado em {carrinho.oferta_simulada.data_simulacao} ({data_relativa}) · "
                f"saldo de {format_brl(carrinho.saldo_devedor)} · "
                f"{carrinho.dias_em_atraso} dias em atraso — não finalizado"
            )


def render_footer() -> None:
    st.markdown(
        '<div class="poneiu-footer-trust">🔒 Seus dados estão protegidos · Simulação sem compromisso '
        "e sem consulta que afeta seu score</div>",
        unsafe_allow_html=True,
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


def _passo_atual(estagio: str | None) -> int:
    if estagio == Estagio.AGUARDANDO_ESCOLHA.value:
        return 2
    if estagio == Estagio.CONCLUIDO.value:
        return 3
    return 1


def _renderizar_stepper(estagio: str | None) -> None:
    """Mostra em que ponto do fluxo (valor → oferta → confirmação) a
    conversa está. Escondido quando o gatekeeper encerrou a conversa, já
    que o banner de encerramento conta essa história melhor do que um
    stepper "parado no meio".
    """

    if estagio == Estagio.ENCERRADO_HUMANO.value:
        return

    passo_atual = _passo_atual(estagio)
    itens = []
    for indice, nome in enumerate(_PASSOS_RENEGOCIACAO, start=1):
        if indice < passo_atual:
            estado_css, marcador = "done", "✓"
        elif indice == passo_atual:
            estado_css, marcador = "active", str(indice)
        else:
            estado_css, marcador = "pending", str(indice)
        itens.append(
            f'<div class="poneiu-step poneiu-step-{estado_css}">'
            f'<div class="poneiu-step-circle">{marcador}</div>'
            f'<div class="poneiu-step-label">{nome}</div>'
            "</div>"
        )
    st.markdown(f'<div class="poneiu-stepper">{"".join(itens)}</div>', unsafe_allow_html=True)


def _sugestoes_valor(carrinho: CarrinhoAbandonado) -> list[int]:
    """Sugere 3 valores mensais próximos da parcela que o cliente já tinha
    simulado antes, para permitir responder com um toque em vez de digitar.
    """

    base = carrinho.oferta_simulada.valor_parcela
    valores = {max(round(base * fator / 50) * 50, 50) for fator in (0.7, 1.0, 1.3)}
    return sorted(valores)


def _renderizar_sugestoes_valor(carrinho: CarrinhoAbandonado) -> None:
    valores = _sugestoes_valor(carrinho)
    st.markdown(
        '<div class="poneiu-muted" style="margin: 0.2rem 0 0.4rem;">Ou toque em um valor:</div>',
        unsafe_allow_html=True,
    )
    colunas = st.columns(len(valores))
    for coluna, valor in zip(colunas, valores):
        with coluna:
            with st.container(border=True):
                if st.button(
                    format_brl(valor),
                    key=f"valor_sugerido_{carrinho.cart_id}_{valor}",
                    use_container_width=True,
                ):
                    with st.spinner("Calculando as melhores opções..."):
                        orquestrador.enviar_mensagem(carrinho.cart_id, f"consigo pagar {valor} reais por mês")
                    st.rerun()


def _renderizar_ofertas_selecionaveis(cart_id: str, ofertas_brutas: list[dict]) -> None:
    """Cartões de oferta clicáveis, alternativa ao cliente digitar "1"/"2"."""

    if not ofertas_brutas:
        return

    ofertas = [OfertaRenegociacao.from_dict(dado) for dado in ofertas_brutas]
    indice_melhor = max(range(len(ofertas)), key=lambda i: ofertas[i].desconto_percentual)

    st.markdown(
        '<div class="poneiu-muted" style="margin: 0.2rem 0 0.4rem;">Ou escolha uma opção:</div>',
        unsafe_allow_html=True,
    )
    for indice, oferta in enumerate(ofertas):
        with st.container(border=True):
            if indice == indice_melhor and oferta.desconto_percentual > 0:
                st.markdown('<span class="poneiu-offer-badge">⭐ Melhor custo-benefício</span>', unsafe_allow_html=True)
            taxa_pct = oferta.taxa_mensal * 100
            detalhe_desconto = (
                f'<div class="poneiu-offer-detail" style="color:#12602F;">'
                f"💸 {oferta.desconto_percentual:.0f}% de desconto sobre encargos</div>"
                if oferta.desconto_percentual > 0
                else ""
            )
            st.markdown(
                f"""
                <div class="poneiu-offer-parcela">{oferta.parcelas}x de {format_brl(oferta.valor_parcela)}</div>
                <div class="poneiu-offer-detail">taxa {taxa_pct:.2f}% a.m. · total {format_brl(oferta.valor_total)}</div>
                {detalhe_desconto}
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            if st.button("Escolher esta opção", key=f"escolher_{cart_id}_{indice}", use_container_width=True):
                with st.spinner("Confirmando sua escolha..."):
                    orquestrador.enviar_mensagem(cart_id, f"quero a opção {indice + 1}")
                st.rerun()


def _texto_comprovante(carrinho: CarrinhoAbandonado, oferta: OfertaRenegociacao, protocolo: str) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    taxa_pct = oferta.taxa_mensal * 100
    return (
        "COMPROVANTE DE RENEGOCIAÇÃO — PONEIU\n"
        f"Emitido em: {agora}\n"
        f"Protocolo: {protocolo}\n\n"
        f"Cliente: {carrinho.cliente_nome}\n"
        f"Produto: {carrinho.produto.rotulo}\n"
        f"Saldo devedor original: {format_brl(carrinho.saldo_devedor)}\n\n"
        f"Condição contratada: {oferta.parcelas}x de {format_brl(oferta.valor_parcela)}\n"
        f"Taxa: {taxa_pct:.2f}% a.m.\n"
        f"Valor total: {format_brl(oferta.valor_total)}\n"
        f"Desconto aplicado: {oferta.desconto_percentual:.0f}%\n\n"
        "PoneIU é um banco fictício criado para fins de demonstração.\n"
        "Este comprovante não possui validade financeira real."
    )


def _renderizar_confirmacao(carrinho: CarrinhoAbandonado, estado: dict) -> None:
    protocolo = estado.get("protocolo_confirmacao")
    oferta_bruta = estado.get("oferta_escolhida")
    if not protocolo or not oferta_bruta:
        return

    oferta = OfertaRenegociacao.from_dict(oferta_bruta)
    taxa_pct = oferta.taxa_mensal * 100

    chave_balao = f"balao_exibido_{carrinho.cart_id}"
    if not st.session_state.get(chave_balao):
        st.balloons()
        st.session_state[chave_balao] = True

    st.markdown(
        f"""
        <div class="poneiu-receipt">
            <div class="poneiu-receipt-titulo">✅ Renegociação concluída</div>
            <div class="poneiu-receipt-row"><span>Produto</span><span>{carrinho.produto.rotulo}</span></div>
            <div class="poneiu-receipt-row"><span>Condição</span><span>{oferta.parcelas}x de {format_brl(oferta.valor_parcela)}</span></div>
            <div class="poneiu-receipt-row"><span>Taxa</span><span>{taxa_pct:.2f}% a.m.</span></div>
            <div class="poneiu-receipt-row"><span>Total</span><span>{format_brl(oferta.valor_total)}</span></div>
            <div class="poneiu-receipt-row"><span>Protocolo</span><span>{protocolo}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "⬇️ Baixar comprovante",
        data=_texto_comprovante(carrinho, oferta, protocolo),
        file_name=f"comprovante_{protocolo}.txt",
        use_container_width=True,
        key=f"download_{carrinho.cart_id}",
    )


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
        estagio = estado.get("estagio")

        _renderizar_stepper(estagio)

        with st.container(height=380):
            _renderizar_historico(mensagens)

        if estagio == Estagio.AGUARDANDO_VALOR.value:
            _renderizar_sugestoes_valor(carrinho)
        elif estagio == Estagio.AGUARDANDO_ESCOLHA.value:
            _renderizar_ofertas_selecionaveis(carrinho.cart_id, estado.get("ofertas_apresentadas") or [])
        elif estagio == Estagio.ENCERRADO_HUMANO.value:
            st.markdown(
                '<div class="poneiu-encerrado-banner">⏸️ Conversa encerrada pelo assistente. '
                "Digite novamente ou toque no botão abaixo se quiser retomar a renegociação.</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "🔄 Quero retomar a negociação", use_container_width=True, key=f"retomar_{carrinho.cart_id}"
            ):
                with st.spinner("Retomando sua negociação..."):
                    orquestrador.enviar_mensagem(carrinho.cart_id, "quero retomar a negociação")
                st.rerun()
        elif estagio == Estagio.CONCLUIDO.value:
            _renderizar_confirmacao(carrinho, estado)

        texto = st.chat_input("Digite sua mensagem para o PoneIU...")
        if texto:
            with st.spinner("Assistente PoneIU está respondendo..."):
                orquestrador.enviar_mensagem(carrinho.cart_id, texto)
            st.rerun()

        if st.button("Fechar conversa", use_container_width=True, key=f"fechar_{carrinho.cart_id}"):
            st.session_state["carrinho_ativo_id"] = None
            st.session_state.pop(chave_iniciado, None)
            st.session_state.pop(f"balao_exibido_{carrinho.cart_id}", None)
            st.rerun()

    _dialog()
