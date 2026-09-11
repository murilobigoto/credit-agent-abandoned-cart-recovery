"""Camada de acesso ao modelo de linguagem, com fallback determinístico.

Design intencional: os NÚMEROS financeiros (parcela, taxa, total) nunca são
gerados pelo LLM — eles vêm sempre da API mock do PoneIU (`src/services`) e
são apenas *comunicados* pelo agente. O LLM é usado só onde há valor real em
linguagem natural: (a) classificar a intenção do cliente e (b) redigir
respostas humanizadas de acolhimento/encerramento. Isso elimina o risco de
alucinação de condições de crédito — um requisito não-negociável em qualquer
sistema bancário real.

Se `ANTHROPIC_API_KEY` não estiver configurada, tudo aqui cai para um modo
simulado 100% determinístico, para que o repositório rode "out of the box".
"""

from __future__ import annotations

import random
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src import config
from src.agents.prompts import CLASSIFICACAO_INSTRUCAO

IntencaoCliente = Literal["retomar_renegociacao", "outro"]

_PALAVRAS_RETOMADA = (
    "retomar",
    "continuar",
    "prosseguir",
    "seguir com a negocia",
    "seguir com a renegocia",
    "quero renegociar",
    "quero negociar",
    "voltar pra negocia",
    "voltar para negocia",
    "quero ver as opç",
    "quero ver as condi",
    "bora renegociar",
    "bora negociar",
    "vamos renegociar",
    "sim, quero",
    "sim quero",
)


class ClassificacaoIntencao(BaseModel):
    intencao: IntencaoCliente = Field(
        description="'retomar_renegociacao' se o cliente pede para continuar "
        "a negociação de dívida, 'outro' para qualquer outra coisa."
    )
    justificativa: str = Field(description="Uma frase curta explicando a decisão.")


def get_chat_model():
    """Retorna um `ChatAnthropic` configurado, ou None em modo simulado."""

    if not config.LLM_DISPONIVEL:
        return None

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        api_key=config.ANTHROPIC_API_KEY,
    )


def classificar_intencao(mensagem: str, historico: list[BaseMessage]) -> ClassificacaoIntencao:
    """Classifica a última mensagem do cliente.

    Usa primeiro uma heurística barata (cobre a grande maioria dos casos do
    fluxo de demonstração); só recorre ao LLM para desambiguar quando a
    heurística não encontra um sinal claro e há um modelo disponível.
    """

    texto = mensagem.lower()
    if any(gatilho in texto for gatilho in _PALAVRAS_RETOMADA):
        return ClassificacaoIntencao(
            intencao="retomar_renegociacao",
            justificativa="Heurística encontrou expressão de retomada explícita.",
        )

    llm = get_chat_model()
    if llm is None:
        return ClassificacaoIntencao(
            intencao="outro",
            justificativa="Modo simulado sem sinal claro de retomada; padrão conservador.",
        )

    classificador = llm.with_structured_output(ClassificacaoIntencao)
    mensagens = [SystemMessage(content=CLASSIFICACAO_INSTRUCAO), *historico[-6:], HumanMessage(content=mensagem)]
    resultado = classificador.invoke(mensagens)
    assert isinstance(resultado, ClassificacaoIntencao)
    return resultado


_RESPOSTAS_HUMANIZADAS_FALLBACK = [
    "Entendo, e sinto muito que esse momento esteja difícil pra você. "
    "Fico à disposição por aqui: quando quiser retomar a negociação da sua dívida, "
    "é só me chamar que eu já tenho as condições que você tinha simulado.",
    "Obrigada por compartilhar isso comigo. Sei que lidar com dívidas pesa bastante no dia a dia. "
    "Vou encerrar nossa conversa por aqui, mas assim que você quiser voltar a negociar, "
    "é só voltar nesta tela e me chamar.",
    "Poxa, entendo a situação. Esse canal aqui é focado em ajudar você a retomar a renegociação "
    "que você já tinha começado. Quando fizer sentido pra você, volte que eu te mostro as opções novamente.",
]


def gerar_resposta_humanizada(mensagem: str, historico: list[BaseMessage], persona: str) -> str:
    """Gera a resposta empática de encerramento do agente geral.

    Em modo real, usa o LLM com a persona configurada. Em modo simulado,
    usa uma resposta canônica variada o suficiente para não parecer um
    script único repetido sempre igual.
    """

    llm = get_chat_model()
    if llm is None:
        indice = abs(hash(mensagem)) % len(_RESPOSTAS_HUMANIZADAS_FALLBACK)
        return _RESPOSTAS_HUMANIZADAS_FALLBACK[indice]

    mensagens: list[BaseMessage] = [SystemMessage(content=persona), *historico[-8:], HumanMessage(content=mensagem)]
    resposta = llm.invoke(mensagens)
    conteudo = resposta.content if isinstance(resposta, AIMessage) else str(resposta)
    return str(conteudo).strip()


def gerar_texto_livre(system_prompt: str, prompt_usuario: str, historico: list[BaseMessage] | None = None) -> str:
    """Wrapper genérico para geração de texto livre com fallback simples.

    Usado pelo agente de renegociação apenas para dar um verniz de
    naturalidade a mensagens cujo conteúdo numérico já foi fixado
    externamente (o prompt inclui os números exatos a serem citados).
    """

    llm = get_chat_model()
    if llm is None:
        return prompt_usuario

    mensagens: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    if historico:
        mensagens.extend(historico[-6:])
    mensagens.append(HumanMessage(content=prompt_usuario))
    resposta = llm.invoke(mensagens)
    conteudo = resposta.content if isinstance(resposta, AIMessage) else str(resposta)
    return str(conteudo).strip()


def _sorteio_estavel(chave: str, opcoes: list[str]) -> str:
    """Escolhe uma variação de texto de forma estável por chave (sem LLM)."""

    rng = random.Random(chave)
    return rng.choice(opcoes)
