"""Gera a base de conhecimento e os 3 corpus para fine-tuning a partir de documentos.

Uso: python gerar_corpus.py [pasta_documentos] [pasta_saida]
Saída: texto_puro.jsonl, perguntas_respostas.jsonl, conversacional.jsonl, secoes.json
"""
import sys
from pathlib import Path

from assistente.kb import construir

raiz = Path(__file__).parent
docs = Path(sys.argv[1]) if len(sys.argv) > 1 else raiz / "base_conhecimento" / "documentos"
saida = Path(sys.argv[2]) if len(sys.argv) > 2 else raiz / "corpus"
secoes, corpus = construir(docs, saida)
print(f"{len(secoes)} seções extraídas de {docs}")
for nome, linhas in corpus.items():
    print(f"  {nome}.jsonl: {len(linhas)} exemplos")
