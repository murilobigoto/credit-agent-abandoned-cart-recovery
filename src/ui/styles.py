"""CSS injetado na aplicação Streamlit para simular um app bancário real.

A ideia é reduzir a "cara de Streamlit" (esconder o menu padrão, limitar a
largura como uma tela de celular, transformar `st.button` em linhas de
lista com chevron) para que o layout fique próximo da referência de design
(a tela de "Solução de dívidas" fornecida pelo usuário).
"""

from __future__ import annotations

from src.config import COR_DESTAQUE, COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO_MUTED

CSS = f"""
<style>
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

.stApp {{
    background: {COR_SECUNDARIA};
}}

.block-container {{
    max-width: 460px;
    margin: 0 auto;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    background: #FFFFFF;
    min-height: 100vh;
    box-shadow: 0 0 40px rgba(20, 30, 60, 0.08);
}}

/* ---- topo: voltar / ajuda ---- */
.poneiu-topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.4rem;
    color: {COR_PRIMARIA};
    margin-bottom: 0.5rem;
}}

/* ---- selo "Solução de dívidas" + título ---- */
.poneiu-eyebrow {{
    color: {COR_TEXTO_MUTED};
    font-size: 0.95rem;
    margin-top: 0.75rem;
    margin-bottom: 0.15rem;
}}

.poneiu-hero-title {{
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.25;
    color: #10152B;
    margin-bottom: 1.1rem;
}}

.poneiu-section-title {{
    font-size: 1.55rem;
    font-weight: 700;
    color: #10152B;
    margin: 1.6rem 0 0.9rem 0;
}}

.poneiu-badge-novo {{
    display: inline-block;
    background: {COR_PRIMARIA};
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    padding: 3px 10px;
    border-radius: 999px;
    float: right;
}}

.poneiu-card-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #10152B;
    margin-bottom: 0.25rem;
}}

.poneiu-card-desc {{
    color: {COR_TEXTO_MUTED};
    font-size: 0.92rem;
    line-height: 1.4;
}}

.poneiu-muted {{
    color: {COR_TEXTO_MUTED};
    font-size: 0.85rem;
}}

/* ---- cards com borda nativa do Streamlit (st.container(border=True)) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 18px !important;
    border: 1px solid #E7EAEF !important;
    box-shadow: 0 6px 18px rgba(16, 21, 43, 0.06);
}}

/* ---- botões de lista (linhas clicáveis, ex.: produtos do carrinho) ---- */
div[data-testid="stButton"] button {{
    width: 100%;
    text-align: left !important;
    justify-content: flex-start !important;
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 0.85rem 1.6rem 0.85rem 0.6rem;
    color: #10152B;
    font-weight: 600;
    position: relative;
}}
div[data-testid="stButton"] button:hover {{
    background: #F3F5F8;
    color: {COR_PRIMARIA};
    border: none;
}}
div[data-testid="stButton"] button p {{
    font-size: 0.95rem;
}}
div[data-testid="stButton"] button::after {{
    content: "\\203A";
    position: absolute;
    right: 0.6rem;
    top: 50%;
    transform: translateY(-50%);
    color: #9AA1AC;
    font-size: 1.3rem;
    font-weight: 400;
}}

.poneiu-divider {{
    border-top: 1px solid #EEF0F3;
    margin: 0.1rem 0;
}}

.poneiu-chat-role-banco {{
    font-weight: 700;
    color: {COR_PRIMARIA};
}}

.poneiu-encerrado-banner {{
    background: #FFF4E9;
    border: 1px solid {COR_DESTAQUE};
    color: #7A3E00;
    padding: 0.6rem 0.9rem;
    border-radius: 10px;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}}

.poneiu-concluido-banner {{
    background: #E9F7EF;
    border: 1px solid #1F9D55;
    color: #12602F;
    padding: 0.6rem 0.9rem;
    border-radius: 10px;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}}
</style>
"""
