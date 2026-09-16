# ARCA MCP

Servidor MCP que consulta datos de un contribuyente (razón social, estado,
domicilio fiscal, actividades) en el Padrón de **ARCA** (la Agencia de
Recaudación y Control Aduanero, antes AFIP) a partir de su CUIT, autenticando
contra el Web Service de Autenticación y Autorización (WSAA) y llamando al
servicio de Consulta a Padrón (Alcance 13). Incluye un dashboard web que
muestra la última consulta en tiempo real.

> Nota: ARCA sigue usando la infraestructura técnica heredada de AFIP (los
> dominios de los web services y el portal de Clave Fiscal todavía son
> `afip.gob.ar`), así que las URLs de este proyecto apuntan ahí.

Corre contra el entorno de **producción** de ARCA: el certificado se gestiona
desde "Administración de Certificados Digitales" (no desde WSASS, que es
específico para el entorno de homologación/testing y quedó en desuso para
este flujo). Como `consultar_cuit` solo lee datos públicos del padrón, el
riesgo de usar producción es bajo, pero tené presente que las consultas son
reales.

## Requisitos previos

- Python 3.10 o superior
- OpenSSL (viene instalado en macOS/Linux)
- Un CUIT propio con Clave Fiscal nivel 3

## 1. Cómo iniciar sesión en ARCA (Clave Fiscal)

1. Entrá a **https://www.afip.gob.ar** (el organismo se renombró a ARCA, pero
   el dominio y el sistema de Clave Fiscal siguen siendo los mismos).
2. Click en **"Ingresar"**.
3. Ingresá tu **CUIT** y tu **Clave Fiscal** (la contraseña que gestionás en
   ese mismo portal). Para administrar certificados de webservices necesitás
   **nivel de seguridad 3** — si tenés un nivel menor, se sube desde el mismo
   sitio con un trámite adicional (token de seguridad / verificación).
4. Ya logueado, vas a ver el listado de "Servicios habilitados" asociados a
   tu Clave Fiscal.

## 2. Generar el certificado

Ningún web service de ARCA es público: hace falta un certificado digital
propio asociado a tu CUIT.

```bash
mkdir -p certs
openssl genrsa -out certs/clave_privada.key 2048
openssl req -new -key certs/clave_privada.key \
  -subj "/C=AR/O=TuNombre/CN=arca-mcp-local/serialNumber=CUIT 20XXXXXXXXX" \
  -out certs/solicitud.csr
```

Reemplazá `TuNombre` y `20XXXXXXXXX` por tu nombre y tu CUIT sin guiones
(respetando el espacio entre `CUIT` y el número).

Con la sesión iniciada (paso 1):

1. En el buscador de servicios/trámites escribí **"webser"** y entrá a
   **"Administración de Certificados Digitales"**.
2. Click en **"Agregar alias"**. Completá un alias (ej. `arca-mcp-local`) y
   subí `certs/solicitud.csr` con "Choose File".
3. Confirmá y descargá el `.crt` generado; guardalo como
   `certs/certificado.crt`.
4. Andá a **"Administrador de Relaciones de Clave Fiscal"** → **"Nueva
   Relación"**:
   - "Representado": tu propio CUIT (debería salir preseleccionado).
   - Primer botón "Buscar" → **ARCA → Web Services** → elegí
     **`ws_sr_padron_a13`**.
   - Segundo botón "Buscar" → seleccioná el certificado/alias que generaste.
   - Confirmá dos veces.

### Cómo revocar la relación (desasociar el certificado)

Si en algún momento querés desasociar el certificado de `ws_sr_padron_a13`
(por ejemplo, al terminar el parcial):

1. Volvé a **"Administrador de Relaciones de Clave Fiscal"**.
2. Click en **"CONSULTAR"** (el tercer botón del panel principal).
3. Buscá entre **"Representantes"** la relación con tu alias (ej.
   `arca-mcp-local`) y el servicio `ws_sr_padron_a13`.
4. Seleccionala y usá la opción para **revocarla/darla de baja**.

Esto no borra el certificado en sí (eso se gestiona aparte, desde
"Administración de Certificados Digitales"), solo quita su autorización para
usar ese web service puntual.

Ni la clave privada ni el certificado se suben al repositorio (están en
`.gitignore`).

## 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Completá `.env` con tu CUIT y las rutas a los archivos generados en el paso 2.

## 4. Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Verificar la conexión

Antes de conectar el MCP, probá la autenticación y la consulta por separado:

```bash
python3 verificar_conexion.py
```

Si imprime un token y los datos de tu propio CUIT, la configuración es
correcta.

## 6. Ejecutar el servidor

```bash
python3 server.py
```

Levanta el servidor MCP (por stdio) y el dashboard en
`http://127.0.0.1:5050`.

## Configuración del MCP

El archivo `.mcp.json` en la raíz registra el servidor para que el editor lo
detecte automáticamente al abrir esta carpeta. No contiene credenciales: las
lee `server.py` desde `.env` en tiempo de ejecución.

## Cómo usarlo (con Claude Code)

Con el servidor conectado (Claude Code detecta `.mcp.json` al abrir esta
carpeta) y el dashboard abierto en `http://127.0.0.1:5050`, simplemente
pedile en el chat que use la herramienta, por ejemplo:

> "Consultá el CUIT 20XXXXXXXXX en el padrón de ARCA."

Claude va a llamar a `consultar_cuit`, y en el dashboard vas a ver reflejada
la última consulta en tiempo real.

## Herramientas expuestas por el MCP

| Herramienta | Descripción |
|---|---|
| `consultar_cuit(cuit)` | Autentica contra WSAA y consulta los datos del CUIT en el Padrón de ARCA. |

## Estructura del proyecto

```
arca_mcp/
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
