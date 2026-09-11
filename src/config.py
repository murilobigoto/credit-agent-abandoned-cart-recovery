"""Configuração central do ecossistema PoneIU.

Carrega variáveis de ambiente (.env) e concentra constantes de marca usadas
tanto pelos agentes quanto pela interface Streamlit, para que a "voz" do
banco fictício PoneIU fique consistente em todo o projeto.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
MODEL_NAME: str = os.getenv("PONEIU_MODEL_NAME", "claude-sonnet-5")
TEMPERATURE: float = float(os.getenv("PONEIU_TEMPERATURE", "0.4"))

# Quando não há chave de API configurada, o app cai automaticamente para o
# modo simulado (respostas humanizadas determinísticas). Isso permite clonar
# o repositório e rodar `streamlit run app.py` sem nenhuma credencial.
LLM_DISPONIVEL: bool = ANTHROPIC_API_KEY is not None

BANCO_NOME = "PoneIU"
BANCO_SLOGAN = "Reorganize suas contas em dia e evite apertos"
BANCO_PROGRAMA_DESTAQUE = "Novo Desenrola PoneIU"

# Paleta inspirada em apps bancários reais, mas com identidade própria.
COR_PRIMARIA = "#0B2A6B"      # azul-marinho PoneIU
COR_SECUNDARIA = "#F0F2F5"    # cinza claro de fundo
COR_DESTAQUE = "#FF7A1A"      # laranja de call-to-action / badges "Novo"
COR_TEXTO_MUTED = "#5B6472"
