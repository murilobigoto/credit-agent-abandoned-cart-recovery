"""Agente de renegociação de carrinho abandonado.

Este agente assume a conversa quando o `agente_geral` decide que o cliente
quer retomar uma negociação de dívida já simulada anteriormente (e não
contratada — daí "carrinho abandonado"). Ele é uma máquina de estados
simples com 3 passos:

1. Boas-vindas + pedir quanto o cliente consegue pagar por mês.
2. Consultar a API mock do PoneIU e apresentar as 2 ofertas mais próximas
   do valor informado.
3. Confirmar a escolha do cliente e "contratar" (simular) a oferta.

Nenhum valor financeiro é gerado pelo LLM: todos vêm da API mock
(`src/services/poneiu_api.py`). O LLM (quando configurado) só é usado para
dar um verniz de naturalidade à redação — nunca para calcular ou inventar
números.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.llm import gerar_texto_livre
from src.agents.prompts import PERSONA_RENEGOCIACAO
from src.agents.state import AgentState, Estagio
from src.domain.models import CarrinhoAbandonado, ConfirmacaoContrato, OfertaRenegociacao
from src.services.poneiu_api import PoneIUBankAPI
from src.utils import extrair_escolha_oferta, extrair_valor_monetario, format_brl

_api = PoneIUBankAPI()


def _mensagem_boas_vindas(carrinho: CarrinhoAbandonado) -> str:
    oferta_antiga = carrinho.oferta_simulada
    conteudo_base = (
        f"Oi, {carrinho.cliente_nome.split()[0]}! Vi que você tinha simulado, em "
        f"{oferta_antiga.data_simulacao}, uma renegociação do seu {carrinho.produto.rotulo} "
        f"({carrinho.dias_em_atraso} dias em atraso, saldo de {format_brl(carrinho.saldo_devedor)}) "
        f"em {oferta_antiga.parcelas}x de {format_brl(oferta_antiga.valor_parcela)}, mas não chegou "
        "a fechar. Sem problema, consigo te mostrar opções novas agora mesmo. "
        "Quanto você conseguiria pagar por mês?"
    )
    return gerar_texto_livre(PERSONA_RENEGOCIACAO, conteudo_base)


def _mensagem_apresentar_ofertas(
    carrinho: CarrinhoAbandonado, valor_pretendido: float, ofertas: list[OfertaRenegociacao]
) -> str:
    linhas_ofertas = "\n".join(
        f"{i + 1}. {oferta.formatar()}" for i, oferta in enumerate(ofertas)
    )
    conteudo_base = (
        f"Com base nos {format_brl(valor_pretendido)} que você disse conseguir pagar, "
        f"encontrei estas duas opções para o seu {carrinho.produto.rotulo}:\n\n"
        f"{linhas_ofertas}\n\n"
        "Qual das duas fica melhor pra você? Responda 1 ou 2."
    )
    return gerar_texto_livre(PERSONA_RENEGOCIACAO, conteudo_base)


def _mensagem_pedir_valor_novamente() -> str:
    return (
        "Não consegui identificar um valor em reais aí. Pode me dizer, mais ou menos, "
        "quanto você consegue pagar por mês? Por exemplo: R$ 300."
    )


def _mensagem_pedir_escolha_novamente(n_ofertas: int) -> str:
    opcoes = " ou ".join(str(i + 1) for i in range(n_ofertas))
    return f"Não entendi qual opção prefere. Pode responder só com o número: {opcoes}?"


def _mensagem_confirmacao(carrinho: CarrinhoAbandonado, confirmacao: ConfirmacaoContrato) -> str:
    oferta = confirmacao.oferta
    conteudo_base = (
        f"Perfeito! Fechamos a renegociação do seu {carrinho.produto.rotulo} em "
        f"{oferta.formatar()}. Protocolo: {confirmacao.protocolo}. A primeira parcela "
        "vai aparecer na sua fatura/conta no próximo vencimento. Obrigado por regularizar "
        "com o PoneIU!"
    )
    return gerar_texto_livre(PERSONA_RENEGOCIACAO, conteudo_base)


def _mensagem_ja_concluido(state: AgentState) -> str:
    protocolo = state.get("protocolo_confirmacao")
    return (
        f"Essa renegociação já foi concluída com sucesso (protocolo {protocolo}). "
        "Se precisar de mais alguma coisa, é só me chamar!"
    )


def nodo_agente_renegociacao(state: AgentState) -> dict:
    carrinho_bruto = state.get("carrinho")
    if carrinho_bruto is None:
        raise ValueError("Estado inválido: 'carrinho' não foi definido antes de iniciar o agente de renegociação.")
    carrinho = CarrinhoAbandonado.from_dict(carrinho_bruto)

    estagio_bruto = state.get("estagio") or Estagio.INICIO.value
    estagio = Estagio(estagio_bruto) if estagio_bruto in {e.value for e in Estagio} else Estagio.INICIO

    if estagio == Estagio.CONCLUIDO:
        return {"messages": [AIMessage(content=_mensagem_ja_concluido(state))]}

    ultima_mensagem = state["messages"][-1]
    texto = ultima_mensagem.content if isinstance(ultima_mensagem, HumanMessage) else ""

    if estagio in (Estagio.INICIO, Estagio.ENCERRADO_HUMANO):
        return {
            "messages": [AIMessage(content=_mensagem_boas_vindas(carrinho))],
            "estagio": Estagio.AGUARDANDO_VALOR.value,
        }

    if estagio == Estagio.AGUARDANDO_VALOR:
        valor = extrair_valor_monetario(texto)
        if valor is None:
            return {
                "messages": [AIMessage(content=_mensagem_pedir_valor_novamente())],
                "estagio": Estagio.AGUARDANDO_VALOR.value,
            }

        ofertas = _api.simular_opcoes_mais_proximas(carrinho.cart_id, valor, max_opcoes=2)
        return {
            "messages": [AIMessage(content=_mensagem_apresentar_ofertas(carrinho, valor, ofertas))],
            "estagio": Estagio.AGUARDANDO_ESCOLHA.value,
            "valor_pretendido": valor,
            "ofertas_apresentadas": [oferta.to_dict() for oferta in ofertas],
        }

    if estagio == Estagio.AGUARDANDO_ESCOLHA:
        ofertas_brutas = state.get("ofertas_apresentadas") or []
        ofertas = [OfertaRenegociacao.from_dict(dado) for dado in ofertas_brutas]
        indice = extrair_escolha_oferta(texto, len(ofertas))
        if indice is None:
            return {
                "messages": [AIMessage(content=_mensagem_pedir_escolha_novamente(len(ofertas)))],
                "estagio": Estagio.AGUARDANDO_ESCOLHA.value,
            }

        oferta_escolhida = ofertas[indice]
        confirmacao = _api.confirmar_contratacao(carrinho.cart_id, oferta_escolhida)
        return {
            "messages": [AIMessage(content=_mensagem_confirmacao(carrinho, confirmacao))],
            "estagio": Estagio.CONCLUIDO.value,
            "oferta_escolhida": oferta_escolhida.to_dict(),
            "protocolo_confirmacao": confirmacao.protocolo,
        }

    raise AssertionError(f"estágio inesperado no agente de renegociação: {estagio}")
