"""Acesso a dados de ocorrências.

Lê a base compartilhada `dados/ocorrencias.csv` (somente leitura) e grava novas
ocorrências/atualizações numa cópia de runtime (fora do git). Trocar por SQLite
(`dados/citizentech.db`) = nova classe com a mesma interface.
"""
from __future__ import annotations

import csv
import os
import threading
from datetime import datetime
from pathlib import Path

from ..schemas.ocorrencia import Ocorrencia

RAIZ = Path(__file__).resolve().parents[4]  # raiz do repositório
CAMPOS = list(Ocorrencia.model_fields)


class RepositorioCSV:
    def __init__(self, base: Path, runtime: Path):
        self.base, self.runtime = base, runtime
        self._lock = threading.Lock()
        runtime.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _ler(p: Path) -> list[Ocorrencia]:
        if not p.exists():
            return []
        itens = []
        with p.open(encoding="utf-8", newline="") as f:
            for linha in csv.DictReader(f):
                try:
                    itens.append(Ocorrencia(**linha))
                except ValueError:
                    continue  # linha inválida não derruba o painel
        return itens

    def listar(self) -> list[Ocorrencia]:
        por_id = {o.id: o for o in self._ler(self.base)}
        por_id.update({o.id: o for o in self._ler(self.runtime)})  # última versão vence
        return sorted(por_id.values(), key=lambda o: o.criado_em, reverse=True)

    def obter(self, id_: str) -> Ocorrencia | None:
        return next((o for o in self.listar() if o.id == id_), None)

    def proximo_id(self) -> str:
        nums = [int(o.id[3:]) for o in self.listar() if o.id[3:].isdigit()]
        return f"OC-{max(nums, default=0) + 1:04d}"

    def salvar(self, o: Ocorrencia) -> Ocorrencia:
        with self._lock:
            novo = not self.runtime.exists()
            with self.runtime.open("a", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=CAMPOS)
                if novo:
                    w.writeheader()
                d = o.model_dump()
                d["criado_em"] = o.criado_em.isoformat(timespec="seconds")
                w.writerow(d)
        return o

    def registrar_feedback(self, referencia: str, util: bool, comentario: str) -> None:
        p = self.runtime.with_name("feedback.csv")
        with self._lock, p.open("a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"),
                                    referencia, util, comentario])


_repo: RepositorioCSV | None = None


def obter_repositorio() -> RepositorioCSV:
    global _repo
    if _repo is None:
        base = Path(os.getenv("OCORRENCIAS_CSV", RAIZ / "dados" / "ocorrencias.csv"))
        runtime = Path(os.getenv("RUNTIME_CSV", RAIZ / "04-frontend" / ".runtime" / "ocorrencias.csv"))
        _repo = RepositorioCSV(base, runtime)
    return _repo
