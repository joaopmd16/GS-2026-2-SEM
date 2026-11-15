"""Tema 5 — E-mail automático: monta o chamado para o órgão responsável.

Modo padrão `arquivo`: grava cada e-mail como .eml em saida/outbox (seguro para demo,
nada sai da máquina). Modo `smtp`: envia via SMTP com credenciais lidas do .env
(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_REMETENTE) — nunca no código.
Falha de SMTP -> grava em outbox/falhas e segue (caminho seguro).
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from .privacidade import anonimizar
from .util import SAIDA, retry

log = logging.getLogger("robo")
OUTBOX = SAIDA / "outbox"


def montar(o: dict, destino: dict) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = os.getenv("EMAIL_REMETENTE", "robo@citizentech.exemplo")
    msg["To"] = destino["email"]
    msg["Subject"] = f"[CitizenTech][{o['prioridade'].upper()}] {o['tipo']} — {o['bairro']} ({o['id']})"
    msg.set_content(
        f"Prezada equipe {destino['orgao']},\n\n"
        f"Novo chamado de zeladoria gerado automaticamente pela Plataforma CitizenTech.\n\n"
        f"Protocolo: {o['id']}\nTipo: {o['tipo']} (confiança IA {o['confianca']:.2f})\n"
        f"Prioridade: {o['prioridade']}\nBairro: {o['bairro']}\n"
        f"Localização: {o['latitude']:.5f}, {o['longitude']:.5f}\n"
        f"Registrado em: {o['criado_em']}\nPrazo sugerido (dias úteis): {o['prazo']}\n\n"
        f"Descrição (dados pessoais mascarados):\n{anonimizar(o['descricao'])}\n\n"
        "Mensagem automática. Dúvidas: responder a este e-mail.\n")
    return msg


@retry(tentativas=3, espera=1.0, excecoes=(smtplib.SMTPException, OSError))
def _smtp(msg: EmailMessage) -> None:
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587")), timeout=10) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def enviar(o: dict, destino: dict, pasta: Path = OUTBOX) -> str:
    msg = montar(o, destino)
    modo = os.getenv("EMAIL_MODO", "arquivo")
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"{o['id']}.eml"
    if modo == "smtp":
        try:
            _smtp(msg)
            log.info("E-mail SMTP enviado: %s -> %s", o["id"], destino["email"])
        except Exception as e:
            (pasta / "falhas").mkdir(exist_ok=True)
            arq = pasta / "falhas" / f"{o['id']}.eml"
            arq.write_bytes(bytes(msg))
            log.error("SMTP falhou para %s (%s) — salvo para reenvio em %s", o["id"], e, arq)
            raise
    arq.write_bytes(bytes(msg))
    return str(arq.relative_to(pasta.parent))
