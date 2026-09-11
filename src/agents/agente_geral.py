"""Agente geral: porteiro/orquestrador do ecossistema PoneIU.

Regra de negócio central deste nó (pedida explicitamente no escopo do
projeto): qualquer mensagem do cliente que NÃO seja um pedido para retomar
a renegociação de dívida recebe uma resposta humana e empática, e a
conversa é encerrada. Só quando o cliente demonstra intenção clara de
continuar a negociação (ou está respondendo diretamente a uma pergunta do
fluxo de renegociação, como o valor que pode pagar) é que o grafo segue
para o `agente_renegociacao`.

Ver docs/ARQUITETURA.md ("Padrão supervisor/gatekeeper") para a discussão
de por que a validação de "resposta direta" tem prioridade sobre a
reclassificação de intenção a cada turno.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.llm import classificar_intencao, gerar_resposta_humanizada
from src.agents.prompts import PERSONA_GERAL
from src.agents.state import AgentState, Estagio
from src.utils import contem_sinal_de_desistencia, extrair_escolha_oferta, extrair_valor_monetario

_ESTAGIOS_VALIDOS = {estagio.value for estagio in Estagio}


def _estagio_atual(state: AgentState) -> Estagio:
    bruto = state.get("estagio") or Estagio.INICIO.value
    return Estagio(bruto) if bruto in _ESTAGIOS_VALIDOS else Estagio.INICIO


def nodo_agente_geral(state: AgentState) -> dict:
    mensagens = state["messages"]
    ultima_mensagem = mensagens[-1]
    texto = ultima_mensagem.content if isinstance(ultima_mensagem, HumanMessage) else ""
    estagio = _estagio_atual(state)

    # Renegociação já concluída: não reclassifica, apenas repassa para o
    # especialista, que sabe responder com o status final (evita duplicar
    # a mensagem de encerramento em dois nós diferentes).
    if estagio == Estagio.CONCLUIDO:
        return {"estagio": estagio.value}

    # Um encerramento humano anterior pode ser reaberto se o cliente agora
    # manifestar intenção clara de retomar — por isso tratamos como um novo
    # início de triagem, e não como um estado terminal permanente.
    if estagio == Estagio.ENCERRADO_HUMANO:
        estagio = Estagio.INICIO

    # Se estamos no meio do fluxo aguardando um dado específico (valor em
    # reais ou escolha de oferta) e a mensagem atual é reconhecível como
    # essa resposta, pulamos a reclassificação de intenção: isso evita que
    # o classificador confunda "300" ou "quero a segunda opção" com algo
    # fora de contexto.
    if estagio in (Estagio.AGUARDANDO_VALOR, Estagio.AGUARDANDO_ESCOLHA):
        n_ofertas = len(state.get("ofertas_apresentadas") or [])
        eh_resposta_direta = (
            extrair_valor_monetario(texto) is not None
            if estagio == Estagio.AGUARDANDO_VALOR
            else extrair_escolha_oferta(texto, n_ofertas) is not None
        )
        if eh_resposta_direta:
            return {"estagio": estagio.value}

        # A mensagem não é uma resposta direta reconhecível, mas isso por si
        # só não deve encerrar a conversa: uma resposta apenas incerta
        # ("não sei", "sei lá") faz parte do fluxo normal e cabe ao
        # especialista reperguntar com naturalidade. Só encerramos aqui
        # diante de um sinal explícito de desistência/desabafo.
        if contem_sinal_de_desistencia(texto):
            resposta = gerar_resposta_humanizada(texto, mensagens[:-1], PERSONA_GERAL)
            return {
                "messages": [AIMessage(content=resposta)],
                "estagio": Estagio.ENCERRADO_HUMANO.value,
            }
        return {"estagio": estagio.value}

    classificacao = classificar_intencao(texto, mensagens[:-1])
    if classificacao.intencao == "retomar_renegociacao":
        return {"estagio": estagio.value}

    resposta = gerar_resposta_humanizada(texto, mensagens[:-1], PERSONA_GERAL)
    return {
        "messages": [AIMessage(content=resposta)],
        "estagio": Estagio.ENCERRADO_HUMANO.value,
    }


def rotear_apos_triagem(state: AgentState) -> str:
    """Aresta condicional: decide se o grafo segue para o especialista."""

    if _estagio_atual(state) == Estagio.ENCERRADO_HUMANO:
        return "fim"
    return "renegociacao"
