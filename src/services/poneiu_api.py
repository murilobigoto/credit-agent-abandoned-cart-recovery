"""Mock da API core-banking do PoneIU.

Em produção estas chamadas iriam para o "hub de renegociação" via HTTP/gRPC
de um sistema de cobrança real. Aqui simulamos o mesmo contrato em memória
para permitir rodar a demo inteira sem nenhuma dependência externa.

Ver docs/ARQUITETURA.md ("Camada de dados mock") para o racional das taxas
e prazos usados por produto.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from src.domain.models import (
    CarrinhoAbandonado,
    ConfirmacaoContrato,
    OfertaRenegociacao,
    OfertaSimuladaAnteriormente,
    Produto,
)

# Banda de taxa mensal (mín, máx) por produto. Reflete de forma simplificada
# o perfil de risco/subsídio real de cada linha:
# - Cartão: dívida rotativa já vencida -> taxas mais altas.
# - LIC: limite de crédito vinculado à conta, risco intermediário.
# - Pronampe: linha para PJ com funding subsidiado pelo governo -> taxas
#   mais baixas e prazos mais longos (fiel ao produto real).
_TAXAS_MENSAIS: dict[Produto, tuple[float, float]] = {
    Produto.CARTAO: (0.0189, 0.0249),
    Produto.LIC: (0.0129, 0.0179),
    Produto.PRONAMPE: (0.0065, 0.0099),
}

_PRAZOS_DISPONIVEIS: dict[Produto, list[int]] = {
    Produto.CARTAO: [3, 6, 9, 12, 18],
    Produto.LIC: [6, 12, 18, 24, 36],
    Produto.PRONAMPE: [12, 24, 36, 48, 60],
}


def _seed_carteira() -> dict[str, CarrinhoAbandonado]:
    hoje = datetime.now()
    return {
        "cart-cartao-001": CarrinhoAbandonado(
            cart_id="cart-cartao-001",
            cliente_nome="Murilo",
            produto=Produto.CARTAO,
            saldo_devedor=4830.42,
            dias_em_atraso=76,
            oferta_simulada=OfertaSimuladaAnteriormente(
                parcelas=12,
                taxa_mensal=0.0229,
                valor_parcela=498.30,
                data_simulacao=(hoje - timedelta(days=9)).strftime("%d/%m/%Y"),
            ),
        ),
        "cart-lic-001": CarrinhoAbandonado(
            cart_id="cart-lic-001",
            cliente_nome="Murilo",
            produto=Produto.LIC,
            saldo_devedor=12500.00,
            dias_em_atraso=41,
            oferta_simulada=OfertaSimuladaAnteriormente(
                parcelas=24,
                taxa_mensal=0.0159,
                valor_parcela=698.10,
                data_simulacao=(hoje - timedelta(days=4)).strftime("%d/%m/%Y"),
            ),
        ),
        "cart-pronampe-001": CarrinhoAbandonado(
            cart_id="cart-pronampe-001",
            cliente_nome="Murilo Comércio ME",
            produto=Produto.PRONAMPE,
            saldo_devedor=38700.00,
            dias_em_atraso=58,
            oferta_simulada=OfertaSimuladaAnteriormente(
                parcelas=36,
                taxa_mensal=0.0089,
                valor_parcela=1387.55,
                data_simulacao=(hoje - timedelta(days=15)).strftime("%d/%m/%Y"),
            ),
        ),
    }


def _price_pmt(principal: float, taxa_mensal: float, parcelas: int) -> float:
    """Valor de parcela pela Tabela Price (amortização francesa)."""

    if taxa_mensal == 0:
        return principal / parcelas
    fator = (1 + taxa_mensal) ** parcelas
    return principal * (taxa_mensal * fator) / (fator - 1)


class PoneIUBankAPI:
    """Cliente mock da API de renegociação de dívidas do PoneIU.

    A "aleatoriedade" usa uma seed derivada do cart_id para que a demo seja
    determinística e reprodutível entre execuções — importante para testar
    o fluxo dos agentes sem resultados diferentes a cada vez.
    """

    def __init__(self) -> None:
        self._carteira = _seed_carteira()

    # ------------------------------------------------------------------
    # Consulta de carrinho abandonado
    # ------------------------------------------------------------------
    def listar_carrinhos_abandonados(self) -> list[CarrinhoAbandonado]:
        return list(self._carteira.values())

    def obter_carrinho(self, cart_id: str) -> CarrinhoAbandonado | None:
        return self._carteira.get(cart_id)

    # ------------------------------------------------------------------
    # Simulação de novas opções de renegociação
    # ------------------------------------------------------------------
    def gerar_cardapio_completo(self, cart_id: str) -> list[OfertaRenegociacao]:
        """Gera todas as combinações de prazo disponíveis para o produto."""

        carrinho = self.obter_carrinho(cart_id)
        if carrinho is None:
            raise ValueError(f"carrinho '{cart_id}' não encontrado")

        rng = random.Random(cart_id)
        produto = carrinho.produto
        taxa_min, taxa_max = _TAXAS_MENSAIS[produto]
        prazos = _PRAZOS_DISPONIVEIS[produto]

        cardapio: list[OfertaRenegociacao] = []
        for indice, parcelas in enumerate(prazos):
            # Quanto mais parcelas, maior a taxa mensal cobrada (risco de
            # prazo), variando suavemente dentro da banda taxa_min..taxa_max.
            progresso = indice / max(len(prazos) - 1, 1)
            taxa_mensal = round(taxa_min + (taxa_max - taxa_min) * progresso, 4)
            # Desconto de encargos maior para prazos curtos (quitação rápida
            # é incentivada, como em campanhas reais de renegociação).
            desconto_percentual = round(max(0.0, 30 - progresso * 30), 1)

            saldo_com_desconto = carrinho.saldo_devedor * (1 - desconto_percentual / 100 * 0.3)
            valor_parcela = _price_pmt(saldo_com_desconto, taxa_mensal, parcelas)
            valor_parcela = round(valor_parcela + rng.uniform(-1.5, 1.5), 2)
            valor_total = round(valor_parcela * parcelas, 2)

            cardapio.append(
                OfertaRenegociacao(
                    id=f"{cart_id}-{parcelas}x",
                    produto=produto,
                    parcelas=parcelas,
                    taxa_mensal=taxa_mensal,
                    valor_parcela=valor_parcela,
                    valor_total=valor_total,
                    desconto_percentual=desconto_percentual,
                )
            )
        return cardapio

    def simular_opcoes_mais_proximas(
        self,
        cart_id: str,
        valor_pretendido: float,
        max_opcoes: int = 2,
    ) -> list[OfertaRenegociacao]:
        """Devolve as `max_opcoes` ofertas cuja parcela mensal fica mais
        próxima do valor que o cliente disse conseguir pagar.
        """

        cardapio = self.gerar_cardapio_completo(cart_id)
        cardapio_ordenado = sorted(
            cardapio, key=lambda oferta: abs(oferta.valor_parcela - valor_pretendido)
        )
        return cardapio_ordenado[:max_opcoes]

    # ------------------------------------------------------------------
    # Confirmação (contratação simulada)
    # ------------------------------------------------------------------
    def confirmar_contratacao(self, cart_id: str, oferta: OfertaRenegociacao) -> ConfirmacaoContrato:
        protocolo = f"PONEIU-{uuid.uuid4().hex[:10].upper()}"
        return ConfirmacaoContrato(protocolo=protocolo, cart_id=cart_id, oferta=oferta)
