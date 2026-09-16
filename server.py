import os
import sys
import threading
import logging
from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

import wsaa
import padron

load_dotenv()

logging.getLogger('werkzeug').disabled = True
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
SERVICIO = "ws_sr_padron_a13"

CUIT_REPRESENTADA = os.environ.get("ARCA_CUIT")
CERT_PATH = os.environ.get("ARCA_CERT_PATH")
KEY_PATH = os.environ.get("ARCA_KEY_PATH")

mcp = MCPServer("ArcaMCP")
app = Flask(__name__)

ULTIMA_CONSULTA = {"cuit": None, "resultado": None}


def log(mensaje: str) -> None:
    # stderr, nunca stdout: mcp.run() usa stdout para el protocolo stdio.
    print(mensaje, file=sys.stderr, flush=True)


@mcp.tool()
def consultar_cuit(cuit: str) -> dict:
    """Consulta los datos de un contribuyente en el Padrón de ARCA a partir de su CUIT."""
    cuit = cuit.strip().replace("-", "")
    log(f"consultar_cuit: recibida consulta para {cuit}")

    if len(cuit) != 11 or not cuit.isdigit():
        log(f"consultar_cuit: '{cuit}' no es un CUIT válido")
        return {"error": f"'{cuit}' no es un CUIT válido: debe tener 11 dígitos."}

    log("consultar_cuit: autenticando contra WSAA...")
    credenciales = wsaa.login(SERVICIO, CERT_PATH, KEY_PATH)
    log("consultar_cuit: token obtenido, consultando el Padrón...")
    resultado = padron.consultar_persona(CUIT_REPRESENTADA, cuit, credenciales["token"], credenciales["sign"])
    log(f"consultar_cuit: consulta de {cuit} completada")

    ULTIMA_CONSULTA["cuit"] = cuit
    ULTIMA_CONSULTA["resultado"] = resultado
    return resultado


@app.route("/")
def index():
    return send_from_directory(DIRECTORIO_ACTUAL, "index.html")


@app.route("/estado")
def consultar_estado():
    response = jsonify(ULTIMA_CONSULTA)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def ejecutar_web():
    from werkzeug.serving import make_server
    server = make_server("127.0.0.1", 5050, app)
    server.serve_forever()


if __name__ == "__main__":
    hilo_web = threading.Thread(target=ejecutar_web, daemon=True)
    hilo_web.start()
    log("Dashboard disponible en http://127.0.0.1:5050")
    log("Servidor MCP listo, esperando conexión por stdio...")
    mcp.run()
