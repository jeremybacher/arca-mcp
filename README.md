# ARCA MCP

> Este es un proyecto personal e independiente, sin ninguna afiliación,
> respaldo ni vínculo oficial con ARCA, AFIP ni el Estado argentino.

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

### Cómo revocar el acceso (por ejemplo, al terminar el parcial)

La forma más simple y acotada de cortar el acceso es revocar el
**certificado** en sí (no la relación): sin un certificado válido, WSAA
rechaza cualquier login sin importar qué relaciones existan, y la acción
queda limitada a ese certificado puntual sin tocar ningún otro servicio de tu
cuenta.

1. Entrá a **"Administración de Certificados Digitales"** (mismo lugar donde
   lo generaste).
2. Buscá el certificado con el alias que usaste (ej. `arca-mcp-local`) en el
   listado de **"Certificados"**.
3. Usá la opción para revocarlo/darlo de baja.

(La otra vía —buscar y revocar la relación puntual en "Administrador de
Relaciones de Clave Fiscal" → "Consultar"— también funciona, pero ahí la
relación puede no figurar con un nombre reconocible: puede aparecer con el
nombre general del servicio, por ejemplo "Sistema registral", mezclada entre
decenas de otras relaciones que sí necesitás conservar. Preferí revocar el
certificado.)

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

## Cómo usarlo

Una vez conectado el servidor MCP (con cualquiera de los clientes de abajo) y
el dashboard abierto en `http://127.0.0.1:5050`, simplemente pedile en el
chat que use la herramienta, por ejemplo:

> "Consultá el CUIT 20XXXXXXXXX en el padrón de ARCA."

El asistente va a llamar a `consultar_cuit`, y en el dashboard vas a ver
reflejada la última consulta en tiempo real.

### Claude Code

Al abrir esta carpeta como proyecto, Claude Code detecta automáticamente el
`.mcp.json` de la raíz y te va a pedir confirmación para habilitar el
servidor `arca-mcp`.

### Claude Desktop

Claude Desktop no lee `.mcp.json`: hay que registrar el servidor a mano en su
config global.

1. Abrí (o creá) el archivo de configuración:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Agregá una entrada con **rutas absolutas** (Claude Desktop no corre desde
   la carpeta del proyecto, así que las rutas relativas no funcionan):

   ```json
   {
     "mcpServers": {
       "arca-mcp": {
         "command": "/ruta/absoluta/a/arca-mcp/venv/bin/python3",
         "args": ["/ruta/absoluta/a/arca-mcp/server.py"]
       }
     }
   }
   ```

3. Reiniciá Claude Desktop. El servidor va a aparecer en el ícono de
   herramientas (🔨) del chat.

### Otros clientes MCP (Cursor, Windsurf, etc.)

Cualquier cliente que soporte el transporte estándar de MCP por stdio
funciona con el mismo patrón: apuntar `command` al Python del `venv` y
`args` a `server.py`, con rutas absolutas. Revisá la documentación propia de
cada cliente para saber dónde va ese JSON (suele ser un archivo de
configuración de MCP servers similar al de Claude Desktop).

## Herramientas expuestas por el MCP

| Herramienta | Descripción |
|---|---|
| `consultar_cuit(cuit)` | Autentica contra WSAA y consulta el CUIT en el Padrón de ARCA. Devuelve solo nombre, apellido, estado, actividad principal y tipo de persona — el resto (DNI, fecha de nacimiento, domicilio) se descarta a propósito antes de responder. Si el CUIT ya fue consultado antes, devuelve el resultado guardado en el historial local sin volver a llamar a ARCA. |
| `historial_consultas(limite=20)` | Lista las últimas consultas guardadas en el historial local (SQLite). |
| `buscar_en_historial(cuit)` | Busca si ya existe una consulta guardada para un CUIT, sin llamar a ARCA. |

## Historial de consultas

Cada consulta exitosa a `consultar_cuit` se guarda en `historial.db` (SQLite,
no se versiona). Las próximas consultas al mismo CUIT se responden desde ese
historial en vez de volver a autenticar y consultar el Padrón. El dashboard
web también expone este historial en `http://127.0.0.1:5050/historial`.

## Tests

```bash
pytest
```

## Estructura del proyecto

```
arca-mcp/
├── server.py             # MCP tools + servidor web embebido
├── wsaa.py                # Login contra WSAA (firma CMS + token/sign, con cache)
├── padron.py               # Consulta al Padrón (Alcance 13)
├── historia.py              # Historial de consultas (SQLite)
├── verificar_conexion.py    # Script manual para probar la conexión
├── index.html                # Dashboard con actualización en tiempo real
├── tests/                      # Suite de tests (pytest)
├── certs/                     # Certificado y clave privada (no se versionan)
├── historial.db                # Historial de consultas (se genera solo, no se versiona)
├── token_cache.json            # Cache del token de WSAA (se genera solo, no se versiona)
├── requirements.txt
├── pytest.ini
├── .env.example
├── .mcp.json
└── README.md
```
