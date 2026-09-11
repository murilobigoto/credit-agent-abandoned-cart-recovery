import pytest

from src.utils import extrair_escolha_oferta, extrair_valor_monetario, format_brl


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("consigo pagar 300 reais", 300.0),
        ("R$ 1.200,50 por mes", 1200.50),
        ("uns 450 por mes", 450.0),
        ("não consigo pagar nada esse mês", None),
        ("", None),
    ],
)
def test_extrair_valor_monetario(texto, esperado):
    assert extrair_valor_monetario(texto) == esperado


def test_format_brl():
    assert format_brl(1234.5) == "R$ 1.234,50"
    assert format_brl(90) == "R$ 90,00"


@pytest.mark.parametrize(
    "texto,n_ofertas,esperado",
    [
        ("quero a 1", 2, 0),
        ("prefiro a segunda opção", 2, 1),
        ("opção 2 por favor", 2, 1),
        ("não sei ainda", 2, None),
    ],
)
def test_extrair_escolha_oferta(texto, n_ofertas, esperado):
    assert extrair_escolha_oferta(texto, n_ofertas) == esperado
