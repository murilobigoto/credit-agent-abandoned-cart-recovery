"""Pequenos utilitários compartilhados entre domínio, agentes e UI."""

from __future__ import annotations

import re
from datetime import datetime


def format_brl(valor: float) -> str:
    """Formata um float como moeda brasileira: 1234.5 -> "R$ 1.234,50"."""

    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"R$ {texto}"


def formatar_data_relativa(data_str: str, referencia: datetime | None = None) -> str:
    """Converte "dd/mm/aaaa" em um texto relativo curto ("hoje", "ontem", "há N dias").

    Usado na lista de carrinhos abandonados para reforçar o senso de tempo
    sem esconder a data exata (que continua exibida ao lado).
    """

    referencia = referencia or datetime.now()
    data = datetime.strptime(data_str, "%d/%m/%Y")
    dias = (referencia.date() - data.date()).days
    if dias <= 0:
        return "hoje"
    if dias == 1:
        return "ontem"
    return f"há {dias} dias"


_VALOR_REGEX = re.compile(
    r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)


def extrair_valor_monetario(texto: str) -> float | None:
    """Tenta extrair um valor em reais de uma frase livre do cliente.

    Aceita formatos como "300", "R$ 300,00", "mil e duzentos", "1.200,50".
    Não tenta ser um parser de linguagem natural completo — é um extrator
    pragmático o suficiente para o fluxo de coleta de valor no chat.
    """

    texto_normalizado = texto.strip().lower()
    if not texto_normalizado:
        return None

    match = _VALOR_REGEX.search(texto_normalizado)
    if not match:
        return None

    bruto = match.group(1)
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    else:
        # "1.200" (separador de milhar) vs "12.50" (decimal) — se houver mais
        # de 3 dígitos após o ponto ou mais de um ponto, trata como milhar.
        partes = bruto.split(".")
        if len(partes) > 1 and len(partes[-1]) == 3:
            bruto = bruto.replace(".", "")

    try:
        valor = float(bruto)
    except ValueError:
        return None

    return valor if valor > 0 else None


_SINAIS_DE_DESISTENCIA_MEIO_FLUXO = (
    "perdi o emprego",
    "perdi meu emprego",
    "desemprega",
    "fui demitid",
    "não aguento",
    "nao aguento",
    "sem dinheiro nenhum",
    "não tenho como pagar nada",
    "nao tenho como pagar nada",
    "não consigo pagar nada",
    "nao consigo pagar nada",
    "não sei o que fazer da vida",
    "nao sei o que fazer da vida",
    "quero cancelar",
    "falar com atendente",
    "atendente humano",
    "outro assunto",
    "esquece isso",
    "deixa pra lá",
    "deixa pra la",
    "não quero mais",
    "nao quero mais",
)


def contem_sinal_de_desistencia(texto: str) -> bool:
    """Detecta sinais claros de desabafo/desistência durante um fluxo já em
    andamento (ex.: o cliente já estava respondendo "quanto pode pagar" e de
    repente fala de desemprego).

    Usado como um filtro deliberadamente mais permissivo que o classificador
    de intenção da entrada da conversa: uma resposta apenas ambígua ou
    incompleta ("não sei", "sei lá") a uma pergunta do fluxo NÃO deve
    encerrar a conversa — só sinais explícitos de desistência devem.
    """

    texto_normalizado = texto.strip().lower()
    return any(sinal in texto_normalizado for sinal in _SINAIS_DE_DESISTENCIA_MEIO_FLUXO)


_ESCOLHA_ORDINAIS = {
    "primeira": 0,
    "1a": 0,
    "1ª": 0,
    "segunda": 1,
    "2a": 1,
    "2ª": 1,
}


def extrair_escolha_oferta(texto: str, n_ofertas: int) -> int | None:
    """Interpreta a escolha do cliente entre as ofertas apresentadas (0-based).

    Aceita "1"/"2", "opção 1"/"opção 2", "primeira"/"segunda", ou frases como
    "quero a 2", "aceito a primeira", "fecho com a opção 1".
    """

    if n_ofertas <= 0:
        return None

    texto_normalizado = texto.strip().lower()
    if not texto_normalizado:
        return None

    for palavra, indice in _ESCOLHA_ORDINAIS.items():
        if palavra in texto_normalizado and indice < n_ofertas:
            return indice

    match = re.search(r"\b([1-9])\b", texto_normalizado)
    if match:
        indice = int(match.group(1)) - 1
        if 0 <= indice < n_ofertas:
            return indice

    return None
