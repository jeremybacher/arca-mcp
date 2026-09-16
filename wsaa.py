import base64
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import zeep

WSAA_WSDL = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"


def _generar_tra(servicio: str) -> str:
    ahora = datetime.utcnow()
    generation_time = (ahora - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S-00:00")
    expiration_time = (ahora + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S-00:00")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>{int(ahora.timestamp())}</uniqueId>
    <generationTime>{generation_time}</generationTime>
    <expirationTime>{expiration_time}</expirationTime>
  </header>
  <service>{servicio}</service>
</loginTicketRequest>"""


def _firmar_tra(tra_xml: str, cert_path: str, key_path: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", delete=False) as tra_file:
        tra_file.write(tra_xml)
        tra_path = tra_file.name
    cms_path = tra_path + ".cms"

    try:
        subprocess.run(
            [
                "openssl", "smime", "-sign",
                "-signer", cert_path,
                "-inkey", key_path,
                "-outform", "DER",
                "-nodetach",
                "-in", tra_path,
                "-out", cms_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(cms_path, "rb") as f:
            return f.read()
    finally:
        os.remove(tra_path)
        if os.path.exists(cms_path):
            os.remove(cms_path)


def login(servicio: str, cert_path: str, key_path: str) -> dict:
    """Autentica contra WSAA de ARCA (homologación) y devuelve token, sign y expiración."""
    tra_xml = _generar_tra(servicio)
    cms = _firmar_tra(tra_xml, cert_path, key_path)
    cms_b64 = base64.b64encode(cms).decode("ascii")

    cliente = zeep.Client(WSAA_WSDL)
    respuesta_xml = cliente.service.loginCms(cms_b64)

    raiz = ET.fromstring(respuesta_xml)
    return {
        "token": raiz.findtext(".//token"),
        "sign": raiz.findtext(".//sign"),
        "expiracion": raiz.findtext(".//expirationTime"),
    }
