"""Ponto de entrada da simulação PoneIU.

Execute com:

    streamlit run app.py

Ver README.md para instruções completas de instalação e docs/ARQUITETURA.md
para o racional de design do ecossistema de agentes por trás desta tela.
"""

from __future__ import annotations

import streamlit as st

from src.config import BANCO_NOME
from src.services.poneiu_api import PoneIUBankAPI
from src.ui import components
from src.ui.styles import CSS

st.set_page_config(
    page_title=f"{BANCO_NOME} | Soluções de dívidas",
    page_icon="🤝",
    layout="centered",
)
st.markdown(CSS, unsafe_allow_html=True)

if "carrinho_ativo_id" not in st.session_state:
    st.session_state["carrinho_ativo_id"] = None


@st.cache_resource
def _api() -> PoneIUBankAPI:
    return PoneIUBankAPI()


api = _api()

components.render_header()
components.render_hero()
components.render_desenrola_card()
components.render_formas_reorganizar(api.listar_carrinhos_abandonados())

carrinho_ativo_id = st.session_state.get("carrinho_ativo_id")
if carrinho_ativo_id:
    carrinho_ativo = api.obter_carrinho(carrinho_ativo_id)
    if carrinho_ativo is not None:
        components.abrir_chat_dialog(carrinho_ativo)
