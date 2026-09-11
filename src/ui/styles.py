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

/* ---- colunas nativas do Streamlit usadas em alguns trechos (linha do
   carrinho, sugestões de valor): alinha verticalmente quando renderizadas
   lado a lado (telas largas o suficiente para não empilhar) ---- */
div[data-testid="stHorizontalBlock"] {{
    align-items: center;
}}

/* ---- saudação + selo de confiança no hero ---- */
.poneiu-greeting {{
    color: {COR_TEXTO_MUTED};
    font-size: 0.95rem;
    margin-top: 0.9rem;
}}

.poneiu-trust-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.9rem;
    color: {COR_TEXTO_MUTED};
    font-size: 0.78rem;
    margin: -0.4rem 0 1.3rem 0;
}}

/* ---- resumo (stat tiles) ---- */
.poneiu-stat-row {{
    display: flex;
    gap: 0.7rem;
    margin-bottom: 1.4rem;
}}

.poneiu-stat-tile {{
    flex: 1;
    background: {COR_SECUNDARIA};
    border-radius: 14px;
    padding: 0.75rem 0.6rem;
    text-align: center;
}}

.poneiu-stat-tile-destaque {{
    background: #FFF4E9;
}}

.poneiu-stat-value {{
    font-size: 1.15rem;
    font-weight: 800;
    color: #10152B;
    line-height: 1.2;
}}

.poneiu-stat-tile-destaque .poneiu-stat-value {{
    color: {COR_DESTAQUE};
}}

.poneiu-stat-label {{
    font-size: 0.72rem;
    color: {COR_TEXTO_MUTED};
    margin-top: 0.15rem;
    line-height: 1.25;
}}

/* ---- expander "saiba mais" com a mesma linguagem visual dos cards ---- */
div[data-testid="stExpander"] {{
    border-radius: 14px !important;
    border: 1px solid #E7EAEF !important;
}}
div[data-testid="stExpander"] summary {{
    font-size: 0.9rem;
    font-weight: 600;
    color: {COR_PRIMARIA};
}}

/* ---- chips de urgência na lista de carrinhos ---- */
.poneiu-chip-cell {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
    min-height: 2.6rem;
}}

.poneiu-chip {{
    display: inline-block;
    white-space: nowrap;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid transparent;
}}

.poneiu-chip-critico {{
    background: #FDECEC;
    border-color: #D03B3B;
    color: #8A2323;
}}

.poneiu-chip-urgente {{
    background: #FFF4E9;
    border-color: {COR_DESTAQUE};
    color: #7A3E00;
}}

.poneiu-chip-atencao {{
    background: #FFF9E6;
    border-color: #EDA100;
    color: #7A5C00;
}}

/* ---- stepper de progresso dentro do chat ---- */
.poneiu-stepper {{
    display: flex;
    margin: 0.2rem 0 0.9rem 0;
}}

.poneiu-step {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
}}

.poneiu-step::before {{
    content: "";
    position: absolute;
    top: 0.75rem;
    left: -50%;
    width: 100%;
    height: 2px;
    background: #E7EAEF;
    z-index: 0;
}}

.poneiu-step:first-child::before {{
    content: none;
}}

.poneiu-step-done::before {{
    background: {COR_PRIMARIA};
}}

.poneiu-step-circle {{
    position: relative;
    z-index: 1;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    background: #E7EAEF;
    color: {COR_TEXTO_MUTED};
}}

.poneiu-step-done .poneiu-step-circle {{
    background: {COR_PRIMARIA};
    color: white;
}}

.poneiu-step-active .poneiu-step-circle {{
    background: white;
    color: {COR_PRIMARIA};
    border: 2px solid {COR_PRIMARIA};
}}

.poneiu-step-label {{
    font-size: 0.68rem;
    color: {COR_TEXTO_MUTED};
    margin-top: 0.3rem;
    line-height: 1.2;
}}

.poneiu-step-active .poneiu-step-label, .poneiu-step-done .poneiu-step-label {{
    color: #10152B;
    font-weight: 600;
}}

/* ---- cartões de oferta selecionáveis no chat ---- */
.poneiu-offer-badge {{
    display: inline-block;
    background: {COR_DESTAQUE};
    color: white;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 999px;
    margin-bottom: 0.4rem;
}}

.poneiu-offer-parcela {{
    font-size: 1.05rem;
    font-weight: 800;
    color: #10152B;
}}

.poneiu-offer-detail {{
    font-size: 0.82rem;
    color: {COR_TEXTO_MUTED};
    margin-top: 0.1rem;
}}

/* ---- comprovante de confirmação ---- */
.poneiu-receipt {{
    background: #E9F7EF;
    border: 1px solid #1F9D55;
    border-radius: 14px;
    padding: 0.9rem 1rem;
    margin-top: 0.5rem;
}}

.poneiu-receipt-titulo {{
    font-weight: 700;
    color: #12602F;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}}

.poneiu-receipt-row {{
    display: flex;
    justify-content: space-between;
    font-size: 0.83rem;
    color: #12602F;
    padding: 0.18rem 0;
    border-top: 1px solid rgba(31, 157, 85, 0.2);
}}

.poneiu-receipt-row:first-of-type {{
    border-top: none;
}}

.poneiu-receipt-row span:first-child {{
    color: #3B6E52;
}}

.poneiu-receipt-row span:last-child {{
    font-weight: 700;
}}

/* ---- rodapé de confiança ---- */
.poneiu-footer-trust {{
    text-align: center;
    color: {COR_TEXTO_MUTED};
    font-size: 0.72rem;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #EEF0F3;
}}
</style>
"""
