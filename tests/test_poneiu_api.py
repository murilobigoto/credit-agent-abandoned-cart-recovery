import pytest

from src.domain.models import Produto
from src.services.poneiu_api import PoneIUBankAPI


def test_lista_tres_carrinhos_abandonados():
    api = PoneIUBankAPI()
    carrinhos = api.listar_carrinhos_abandonados()
    assert len(carrinhos) == 3
    assert {c.produto for c in carrinhos} == {Produto.CARTAO, Produto.LIC, Produto.PRONAMPE}


def test_cardapio_e_deterministico_por_cart_id():
    api = PoneIUBankAPI()
    primeira = api.gerar_cardapio_completo("cart-cartao-001")
    segunda = api.gerar_cardapio_completo("cart-cartao-001")
    assert [o.valor_parcela for o in primeira] == [o.valor_parcela for o in segunda]


def test_simular_opcoes_mais_proximas_retorna_as_duas_mais_proximas():
    api = PoneIUBankAPI()
    cardapio = api.gerar_cardapio_completo("cart-lic-001")
    escolhidas = api.simular_opcoes_mais_proximas("cart-lic-001", valor_pretendido=600, max_opcoes=2)

    assert len(escolhidas) == 2
    diffs_escolhidas = sorted(abs(o.valor_parcela - 600) for o in escolhidas)
    diffs_todas = sorted(abs(o.valor_parcela - 600) for o in cardapio)
    assert diffs_escolhidas == diffs_todas[:2]


def test_confirmar_contratacao_gera_protocolo_poneiu():
    api = PoneIUBankAPI()
    oferta = api.gerar_cardapio_completo("cart-pronampe-001")[0]
    confirmacao = api.confirmar_contratacao("cart-pronampe-001", oferta)

    assert confirmacao.protocolo.startswith("PONEIU-")
    assert confirmacao.status == "CONTRATADO"
    assert confirmacao.oferta is oferta


def test_carrinho_inexistente_leva_a_erro():
    api = PoneIUBankAPI()
    with pytest.raises(ValueError):
        api.gerar_cardapio_completo("nao-existe")
