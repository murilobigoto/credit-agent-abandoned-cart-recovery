"""Modelos de domínio compartilhados entre a API mock e os agentes.

Mantidos deliberadamente simples (dataclasses) porque este é um projeto de
demonstração: em um banco real esses tipos viriam de um contrato de API
(OpenAPI/protobuf) versionado entre times.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.utils import format_brl


class Produto(str, Enum):
    """Produtos de crédito elegíveis para renegociação no ecossistema PoneIU."""

    CARTAO = "cartao"
    LIC = "lic"
    PRONAMPE = "pronampe"

    @property
    def rotulo(self) -> str:
        return {
            Produto.CARTAO: "Cartão PoneIU Personnalité",
            Produto.LIC: "LIC PoneIU (Linha de Crédito Individual)",
            Produto.PRONAMPE: "Pronampe PoneIU (crédito para PJ)",
        }[self]

    @property
    def descricao_curta(self) -> str:
        return {
            Produto.CARTAO: "Fatura de cartão de crédito em atraso",
            Produto.LIC: "Linha de crédito pessoal pré-aprovada",
            Produto.PRONAMPE: "Capital de giro para micro e pequenas empresas",
        }[self]


@dataclass
class OfertaSimuladaAnteriormente:
    """Snapshot da simulação que o cliente fez e não contratou (carrinho)."""

    parcelas: int
    taxa_mensal: float
    valor_parcela: float
    data_simulacao: str

    def to_dict(self) -> dict:
        return {
            "parcelas": self.parcelas,
            "taxa_mensal": self.taxa_mensal,
            "valor_parcela": self.valor_parcela,
            "data_simulacao": self.data_simulacao,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OfertaSimuladaAnteriormente":
        return cls(**data)


@dataclass
class CarrinhoAbandonado:
    """Representa uma simulação de renegociação iniciada e não concluída."""

    cart_id: str
    cliente_nome: str
    produto: Produto
    saldo_devedor: float
    dias_em_atraso: int
    oferta_simulada: OfertaSimuladaAnteriormente

    @property
    def titulo_lista(self) -> str:
        return self.produto.rotulo.upper()

    def to_dict(self) -> dict:
        """Representação 100% serializável (str/float/int/dict), usada como
        fronteira antes de guardar o carrinho no estado do LangGraph — o
        checkpointer serializa via msgpack e não deveria depender de
        dataclasses/enums Python específicos deste projeto.
        """

        return {
            "cart_id": self.cart_id,
            "cliente_nome": self.cliente_nome,
            "produto": self.produto.value,
            "saldo_devedor": self.saldo_devedor,
            "dias_em_atraso": self.dias_em_atraso,
            "oferta_simulada": self.oferta_simulada.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CarrinhoAbandonado":
        return cls(
            cart_id=data["cart_id"],
            cliente_nome=data["cliente_nome"],
            produto=Produto(data["produto"]),
            saldo_devedor=data["saldo_devedor"],
            dias_em_atraso=data["dias_em_atraso"],
            oferta_simulada=OfertaSimuladaAnteriormente.from_dict(data["oferta_simulada"]),
        )


@dataclass
class OfertaRenegociacao:
    """Uma opção de renegociação retornada pela API mock do PoneIU."""

    id: str
    produto: Produto
    parcelas: int
    taxa_mensal: float
    valor_parcela: float
    valor_total: float
    desconto_percentual: float

    def formatar(self) -> str:
        taxa_pct = self.taxa_mensal * 100
        desconto = (
            f" (com {self.desconto_percentual:.0f}% de desconto sobre encargos)"
            if self.desconto_percentual > 0
            else ""
        )
        return (
            f"{self.parcelas}x de {format_brl(self.valor_parcela)} "
            f"(taxa de {taxa_pct:.2f}% a.m., total {format_brl(self.valor_total)}){desconto}"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "produto": self.produto.value,
            "parcelas": self.parcelas,
            "taxa_mensal": self.taxa_mensal,
            "valor_parcela": self.valor_parcela,
            "valor_total": self.valor_total,
            "desconto_percentual": self.desconto_percentual,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OfertaRenegociacao":
        return cls(
            id=data["id"],
            produto=Produto(data["produto"]),
            parcelas=data["parcelas"],
            taxa_mensal=data["taxa_mensal"],
            valor_parcela=data["valor_parcela"],
            valor_total=data["valor_total"],
            desconto_percentual=data["desconto_percentual"],
        )


@dataclass
class ConfirmacaoContrato:
    """Retorno simulado da "contratação" de uma oferta."""

    protocolo: str
    cart_id: str
    oferta: OfertaRenegociacao
    status: str = "CONTRATADO"
