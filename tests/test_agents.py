"""Testes de integração do grafo LangGraph (roda em modo simulado, sem LLM).

Cada teste limpa o cache do grafo antes e depois de rodar (`obter_grafo` é
`lru_cache`d por processo) para garantir que o `MemorySaver` — e portanto o
histórico de conversa — não vaze de um teste para o outro mesmo quando dois
testes usam o mesmo `cart_id` de demonstração.
"""

from __future__ import annotations

import pytest

from src.agents import orquestrador
from src.agents.graph import obter_grafo
from src.agents.state import Estagio
from src.domain.models import CarrinhoAbandonado
from src.services.poneiu_api import PoneIUBankAPI


@pytest.fixture(autouse=True)
def _grafo_isolado_por_teste():
    obter_grafo.cache_clear()
    yield
    obter_grafo.cache_clear()


def _carrinho(cart_id: str) -> CarrinhoAbandonado:
    carrinho = PoneIUBankAPI().obter_carrinho(cart_id)
    assert carrinho is not None
    return carrinho


def test_fluxo_feliz_completo():
    carrinho = _carrinho("cart-cartao-001")

    estado = orquestrador.iniciar_conversa(carrinho)
    assert estado["estagio"] == Estagio.AGUARDANDO_VALOR.value

    estado = orquestrador.enviar_mensagem(carrinho.cart_id, "consigo pagar uns 300 reais por mes")
    assert estado["estagio"] == Estagio.AGUARDANDO_ESCOLHA.value
    assert len(estado["ofertas_apresentadas"]) == 2

    estado = orquestrador.enviar_mensagem(carrinho.cart_id, "quero a opção 2")
    assert estado["estagio"] == Estagio.CONCLUIDO.value
    assert estado["protocolo_confirmacao"].startswith("PONEIU-")


def test_valor_nao_reconhecido_repete_a_pergunta_sem_travar():
    carrinho = _carrinho("cart-lic-001")
    orquestrador.iniciar_conversa(carrinho)

    estado = orquestrador.enviar_mensagem(carrinho.cart_id, "não faço ideia, sei lá")
    assert estado["estagio"] == Estagio.AGUARDANDO_VALOR.value


def test_iniciar_conversa_e_idempotente():
    carrinho = _carrinho("cart-lic-001")
    primeiro = orquestrador.iniciar_conversa(carrinho)
    segundo = orquestrador.iniciar_conversa(carrinho)
    assert len(segundo["messages"]) == len(primeiro["messages"])


def test_gatekeeper_encerra_mensagem_fora_de_topico():
    carrinho = _carrinho("cart-pronampe-001")
    orquestrador.iniciar_conversa(carrinho)

    estado = orquestrador.enviar_mensagem(
        carrinho.cart_id, "perdi meu emprego, não aguento mais nada, não sei o que fazer"
    )
    assert estado["estagio"] == Estagio.ENCERRADO_HUMANO.value


def test_gatekeeper_permite_reabrir_apos_encerramento():
    carrinho = _carrinho("cart-cartao-001")
    orquestrador.iniciar_conversa(carrinho)
    orquestrador.enviar_mensagem(carrinho.cart_id, "só queria desabafar, sem condições de pagar nada")

    estado = orquestrador.enviar_mensagem(carrinho.cart_id, "quero retomar a negociação")
    assert estado["estagio"] == Estagio.AGUARDANDO_VALOR.value
