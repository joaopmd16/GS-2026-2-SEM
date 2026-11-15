"""API CitizenTech (FastAPI). Rodar dentro de backend/: uvicorn app.main:app --port 8000"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers.api import router

log = logging.getLogger("citizentech")
app = FastAPI(title="CitizenTech — Zeladoria Urbana Acessível", version="1.0")

# CORS restritivo: só as origens listadas em CORS_ORIGINS (nunca "*").
origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
           if o.strip() and o.strip() != "*"]
app.add_middleware(CORSMiddleware, allow_origins=origens,
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])


@app.exception_handler(Exception)
async def erro_generico(_: Request, exc: Exception):
    log.exception("erro não tratado", exc_info=exc)  # detalhe técnico só no log do servidor
    return JSONResponse(status_code=500, content={"detail": "Erro interno. Tente novamente."})


app.include_router(router)
