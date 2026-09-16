# Consulta Padrón AFIP MCP

Servidor MCP que consulta datos de un contribuyente (razón social, estado,
domicilio fiscal, actividades) en el Padrón de AFIP/ARCA a partir de su CUIT,
autenticando contra el Web Service de Autenticación y Autorización (WSAA) y
llamando al servicio de Consulta a Padrón (Alcance 13). Incluye un dashboard
web que muestra la última consulta en tiempo real.

Corre contra el entorno de **homologación** (testing) de AFIP, no producción.

## Requisitos previos

- Python 3.10 o superior
- OpenSSL (viene instalado en macOS/Linux)
- Un CUIT propio con Clave Fiscal nivel 3

## 1. Generar el certificado de homologación

AFIP no expone ningún servicio sin autenticación: hace falta un certificado
digital asociado a tu CUIT.

```bash
mkdir -p certs
openssl genrsa -out certs/clave_privada.key 2048
openssl req -new -key certs/clave_privada.key \
  -subj "/C=AR/O=NombrePropio/CN=NombreDelCertificado/serialNumber=CUIT 20XXXXXXXXX" \
  -out certs/solicitud.csr
```

Reemplazá `20XXXXXXXXX` por tu CUIT sin guiones (respetando el espacio entre
`CUIT` y el número).

Después, en el sitio de AFIP:

1. Entrá con tu Clave Fiscal a **www.afip.gob.ar**.
2. Buscá el servicio **"WSASS - Autogestión Certificados Homologación"** (si
   no aparece en tu lista de servicios, agregalo desde "Administrador de
   Relaciones de Clave Fiscal").
3. Elegí **"Nuevo Certificado"** y pegá el contenido de `certs/solicitud.csr`.
4. Descargá el `.crt` generado y guardalo como `certs/certificado.crt`.
5. En **"Administrador de Relaciones de Clave Fiscal"**, asociá ese
   certificado al servicio **`ws_sr_padron_a13`**.

Ni la clave privada ni el certificado se suben al repositorio (están en
`.gitignore`).

## 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Completá `.env` con tu CUIT y las rutas a los archivos generados en el paso 1.

## 3. Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Verificar la conexión

Antes de conectar el MCP, probá la autenticación y la consulta por separado:

```bash
python3 verificar_conexion.py
```

Si imprime un token y los datos de tu propio CUIT, la configuración es
correcta.

## 5. Ejecutar el servidor

```bash
python3 server.py
```

Levanta el servidor MCP (por stdio) y el dashboard en
`http://127.0.0.1:5050`.

## Configuración del MCP

El archivo `.mcp.json` en la raíz registra el servidor para que el editor lo
detecte automáticamente al abrir esta carpeta. No contiene credenciales: las
lee `server.py` desde `.env` en tiempo de ejecución.

## Herramientas expuestas por el MCP

| Herramienta | Descripción |
|---|---|
| `consultar_cuit(cuit)` | Autentica contra WSAA y consulta los datos del CUIT en el Padrón de AFIP. |

## Estructura del proyecto

```
afip_padron_mcp/
├── server.py             # MCP tool + servidor web embebido
├── wsaa.py                # Login contra WSAA (firma CMS + token/sign)
├── padron.py               # Consulta al Padrón (Alcance 13)
├── verificar_conexion.py    # Script manual para probar la conexión
├── index.html                # Dashboard con actualización en tiempo real
├── certs/                     # Certificado y clave privada (no se versionan)
├── requirements.txt
├── .env.example
├── .mcp.json
└── README.md
```
