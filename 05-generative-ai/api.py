"""API HTTP mínima (só biblioteca padrão) para o front-end chamar o assistente.

    python api.py            # sobe em http://127.0.0.1:8005
    POST /chat   {"pergunta": "...", "historico": [{"papel": "usuario", "texto": "..."}]}
    GET  /health

No Streamlit/Gradio também dá para importar direto:
    import sys; sys.path.insert(0, "05-generative-ai")
    from assistente import responder
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from assistente import responder


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(204, {})

    def do_GET(self):
        self._json(200, {"status": "ok"} if self.path == "/health" else {"erro": "use POST /chat"})

    def do_POST(self):
        if self.path != "/chat":
            return self._json(404, {"erro": "rota inexistente"})
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 20000)
            dados = json.loads(self.rfile.read(n) or b"{}")
            out = responder(str(dados.get("pergunta", "")), dados.get("historico") or None)
            out.pop("resposta_bruta", None)  # não expor saída bruta ao cliente
            self._json(200, out)
        except Exception as e:  # nunca devolve stack trace
            self._json(400, {"erro": f"requisição inválida ({type(e).__name__})"})

    def log_message(self, fmt, *args):  # não loga corpo (pode conter dado pessoal)
        pass


if __name__ == "__main__":
    porta = int(os.environ.get("PORTA", 8005))
    print(f"Assistente CitizenTech em http://127.0.0.1:{porta}/chat")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()
