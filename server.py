import logging
import os
import sys
import threading
import traceback

import padron
import wsaa
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from mcp.server.mcpserver import MCPServer

load_dotenv()

logging.getLogger("werkzeug").disabled = True
os.environ["WERKZEUG_RUN_MAIN"] = "true"

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
SERVICIO = "ws_sr_padron_a13"

CUIT_REPRESENTADA = os.environ.get("ARCA_CUIT")
CERT_PATH = os.environ.get("ARCA_CERT_PATH")
KEY_PATH = os.environ.get("ARCA_KEY_PATH")

mcp = MCPServer("ArcaMCP")
app = Flask(__name__)

ULTIMA_CONSULTA = {"cuit": None, "resultado": None}

CAMPOS_PUBLICOS = ("nombre", "apellido", "razonSocial", "estadoClave", "descripcionActividadPrincipal", "tipoPersona")


def log(mensaje: str) -> None:
    # stderr, nunca stdout: mcp.run() usa stdout para el protocolo stdio.
    print(mensaje, file=sys.stderr, flush=True)


def _datos_minimos(persona: dict) -> dict:
    # No exponemos DNI, fecha de nacimiento ni domicilio: son más datos
    # personales de los que hace falta mostrar en una demo grabada.
    return {campo: persona[campo] for campo in CAMPOS_PUBLICOS if persona.get(campo) is not None}


@mcp.tool()
def consultar_cuit(cuit: str) -> dict:
    """Consulta los datos de un contribuyente en el Padrón de ARCA a partir de su CUIT."""
    cuit = cuit.strip().replace("-", "")
    log(f"consultar_cuit: recibida consulta para {cuit}")

    if len(cuit) != 11 or not cuit.isdigit():
        log(f"consultar_cuit: '{cuit}' no es un CUIT válido")
        return {"error": f"'{cuit}' no es un CUIT válido: debe tener 11 dígitos."}

    try:
        log("consultar_cuit: autenticando contra WSAA...")
        credenciales = wsaa.login(SERVICIO, CERT_PATH, KEY_PATH)
        log("consultar_cuit: token obtenido, consultando el Padrón...")
        resultado = padron.consultar_persona(
            CUIT_REPRESENTADA, cuit, credenciales["token"], credenciales["sign"]
        )
        resultado = {"persona": _datos_minimos(resultado.get("persona", {}))}
        log(f"consultar_cuit: consulta de {cuit} completada")
    except Exception as exc:
        log(f"consultar_cuit: fallo consultando {cuit} -> {exc}")
        log(traceback.format_exc())
        return {"error": f"Fallo al consultar ARCA: {exc}"}

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
