import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import base64
import hmac
import hashlib
from datetime import datetime, date, time, timedelta
import time as time_lib
import urllib.parse
from io import BytesIO

# Importación segura de ReportLab para evitar caída del servidor
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False

st.set_page_config(
    page_title="Control de Horas",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
/* Escala fija al 80% */
html {
    zoom: 80% !important;
}

/* Ocultar UI nativa de Streamlit */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
footer { visibility: hidden !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* Scroll vertical natural */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: auto !important;
    min-height: 100% !important;
}

.block-container { 
    max-width: 96% !important; 
    padding: 1.2rem !important; 
    padding-right: 28px !important; 
    padding-bottom: 25rem !important; 
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

/* ==========================================================
   FILA SUPERIOR: NAVEGADOR + TUERCA
   ========================================================== */
div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    margin-bottom: 1rem !important;
    padding-right: 14px !important;
}

@media (max-width: 9999px) {
    div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) > div[data-testid="column"] {
        min-width: 0 !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) > div[data-testid="column"]:first-child {
        flex: 1 1 auto !important;
        width: calc(100% - 48px) !important;
        max-width: calc(100% - 48px) !important;
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) > div[data-testid="column"]:last-child {
        flex: 0 0 40px !important;
        width: 40px !important;
        max-width: 40px !important;
        min-width: 40px !important;
        display: flex !important;
        justify-content: flex-end !important;
        position: relative !important;
    }
}

div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) [data-testid="stPopover"] {
    width: 100% !important;
    display: flex !important;
    justify-content: flex-end !important;
    position: relative !important;
}

div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]) [data-testid="stPopover"] > button {
    width: 100% !important;
    min-height: 36px !important;
    height: 36px !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 8px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stPopoverBody"] {
    right: 0px !important;
    left: auto !important;
    transform: translateY(50px) !important;
    box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.7) !important;
}

/* ==========================================================
   FORZAR ELEMENTOS LADO A LADO EN PANEL ADMINISTRADOR
   ========================================================== */
div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-end !important;
    gap: 8px !important;
    width: 100% !important;
}

@media (max-width: 9999px) {
    div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) > div[data-testid="column"] {
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) > div[data-testid="column"]:nth-child(1) {
        flex: 1 1 54% !important;
        width: 54% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) > div[data-testid="column"]:nth-child(2) {
        flex: 1 1 23% !important;
        width: 23% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) > div[data-testid="column"]:nth-child(3) {
        flex: 1 1 23% !important;
        width: 23% !important;
    }
}

div[data-testid="stHorizontalBlock"]:has(.admin-ciclo-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 10px !important;
    width: 100% !important;
}

@media (max-width: 9999px) {
    div[data-testid="stHorizontalBlock"]:has(.admin-ciclo-marker) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.admin-ciclo-marker) > div[data-testid="column"] {
        flex: 1 1 50% !important;
        width: 50% !important;
        min-width: 0 !important;
    }
}

div[data-testid="stHorizontalBlock"]:has(.admin-sim-marker) button {
    height: 40px !important;
    min-height: 40px !important;
    padding: 0 4px !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}

/* ==========================================================
   NAVEGADOR SEGMENTADO SUPERIOR (50/50)
   ========================================================== */
div[data-testid="stSegmentedControl"],
div[data-testid="stPills"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    gap: 6px !important;
}

div[data-testid="stSegmentedControl"] > div,
div[data-testid="stPills"] > div {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    gap: 6px !important;
}

div[data-testid="stSegmentedControl"] button,
div[data-testid="stPills"] button {
    flex: 1 1 50% !important;
    width: 50% !important;
    min-width: 0 !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: clamp(0.68rem, 1.9vw, 0.80rem) !important;
    padding: 0.55rem 0.2rem !important;
    border-radius: 0.5rem !important;
    text-align: center !important;
    box-sizing: border-box !important;
}

div[data-testid="stSegmentedControl"] button[aria-selected="true"],
div[data-testid="stPills"] button[aria-selected="true"] {
    background-color: #ff4b4b !important;
    border: 1px solid #ff4b4b !important;
    color: #ffffff !important;
}

/* ==========================================================
   ESTRUCTURA CSS GRID DE 6 COLUMNAS
   ========================================================== */
.contenedor-tabla-6 {
    display: grid !important;
    grid-template-columns: 7% 12% 10% 13.5% 14.5% 43% !important;
    width: 100% !important;
    align-items: center !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    background-color: #1a1e29 !important;
    border: 1px solid #353b4d !important;
    border-top: none !important;
}

.es-encabezado-6 { 
    font-weight: 700 !important; 
    color: #a3adc2 !important; 
    font-size: 0.65rem !important; 
    background-color: #222634 !important;
    border: 1px solid #353b4d !important;
    border-radius: 4px 4px 0 0;
    padding: 10px 8px !important;
    margin-bottom: -1px !important;
}

.es-datos-6 { 
    color: #ffffff !important; 
    font-size: 0.78rem !important; 
    padding: 6px 8px !important;
    margin-bottom: -1px !important;
}

.contenedor-tabla-6 > div {
    border-right: 1px solid #353b4d !important;
    padding: 0 6px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    height: 100% !important;
}
.contenedor-tabla-6 > div:last-child { 
    border-right: none !important; 
}

div[data-testid="stMarkdownContainer"] p { 
    margin: 0 !important; 
    padding: 0 !important; 
    line-height: 1.1 !important; 
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
    margin-top: -8px !important;
    margin-bottom: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) > div:first-child {
    min-width: 0 !important;
    flex: 1 1 93% !important;
    width: 93% !important;
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) > div:last-child {
    min-width: 34px !important;
    flex: 0 0 7% !important;
    width: 7% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) > div:last-child button {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 0 !important;
    margin: 0 auto !important;
    min-height: 0 !important;
    height: auto !important;
    width: auto !important;
    cursor: pointer !important;
    transform: translateY(6px) !important;
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) > div:last-child button p {
    font-size: 0.85rem !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla-6) > div:last-child button:hover {
    background: transparent !important;
    opacity: 0.6 !important;
}

div[data-testid="stDownloadButton"] > button {
    width: 100% !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    padding: 0.65rem !important;
    border-radius: 0.5rem !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    background-color: #242938 !important;
    border-color: #ff4b4b !important;
    color: #ffffff !important;
}

div[data-testid="stForm"] {
    background-color: #161922 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 6px !important;
    padding: 14px 18px !important;
    margin: 6px 0 !important;
}

div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    gap: 14px !important;
}

div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div {
    flex: 1 1 50% !important;
    width: 50% !important;
    min-width: 0 !important;
}

div[data-testid="stForm"] label p {
    font-size: 0.78rem !important;
    color: #a3adc2 !important;
    font-weight: 600 !important;
}
</style>""", unsafe_allow_html=True)

SECRET_KEY = "control_de_horas_firmado_token_2026"

def firmar_correo(correo: str) -> str:
    msg = correo.encode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{correo}|{sig}".encode("utf-8")).decode("utf-8")

def verificar_token(token: str):
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        correo, sig = decoded.split("|")
        esperada = hmac.new(SECRET_KEY.encode("utf-8"), correo.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, esperada):
            return correo
    except Exception:
        return None
    return None

@st.cache_resource(ttl=300)
def conectar_libro():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    for intento in range(4):
        try:
            if "gcp_service_account" in st.secrets:
                cred_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
            else:
                creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
                
            client = gspread.authorize(creds)
            return client.open("APP DE HORAS")
        except Exception as e:
            if intento == 3:
                raise e
            time_lib.sleep(1.5)

def obtener_hoja_trabajador(nombre_trabajador: str):
    clave = f"hoja_{nombre_trabajador}"
    if clave in st.session_state:
        return st.session_state[clave]
    try:
        libro = conectar_libro()
        hoja = libro.worksheet(nombre_trabajador)
    except Exception:
        conectar_libro.clear()
        libro = conectar_libro()
        hoja = libro.worksheet(nombre_trabajador)
    st.session_state[clave] = hoja
    return hoja

@st.cache_data(ttl=600)
def cargar_trabajadores():
    try:
        libro = conectar_libro()
        hoja_t = libro.worksheet("TRABAJADORES")
        filas = hoja_t.get_all_values()[1:]
        usuarios = {}
        for r in filas:
            if len(r) >= 2 and r[0].strip() and r[1].strip():
                nombre = r[0].strip()
                correo = r[1].strip().lower()
                rol_txt = r[3].strip().lower() if len(r) > 3 and r[3].strip() else ""
                if rol_txt == "admin" or "manuel" in nombre.lower():
                    rol = "admin"
                else:
                    rol = "trabajador"
                usuarios[correo] = {"nombre": nombre, "rol": rol}
        return usuarios
    except Exception:
        return {}

@st.cache_data(ttl=600)
def cargar_obras():
    try:
        libro = conectar_libro()
        hoja_o = libro.worksheet("OBRAS")
        filas = hoja_o.get_all_values()[1:]
        obras_brutas = [r[1].strip() for r in filas if len(r) > 1 and r[1].strip()]
        
        obras_unicas = []
        vistas = set()
        for o in obras_brutas:
            if o.upper() not in vistas:
                vistas.add(o.upper())
                obras_unicas.append(o)
                
        lista_final = obras_unicas if obras_unicas else ["LOTE 1", "LOTE 4", "LOTE 11", "MONTESSORI"]
        for opc_especial in ["PERMISO", "NO TRABAJA"]:
            if not any(o.upper() == opc_especial for o in lista_final):
                lista_final.append(opc_especial)
                
        return lista_final
    except Exception:
        return ["LOTE 1", "LOTE 4", "LOTE 11", "MONTESSORI", "PERMISO", "NO TRABAJA"]

FERIADOS = ["2026-09-18", "2026-09-19", "2026-09-20"]
DIAS_MAP = {
    0: "LUNES", 1: "MARTES", 2: "MIÉRCOLES", 3: "JUEVES",
    4: "VIERNES", 5: "SÁBADO", 6: "DOMINGO"
}

def minutos_a_hora_str(total_minutos: int) -> str:
    h = int(total_minutos // 60)
    m = int(total_minutos % 60)
    return f"{h:02d}:{m:02d} hrs"

def fila_segun_dia(dia: int) -> int:
    if dia == 31:
        return 2
    return 2 + dia

def str_a_time(texto: str):
    if not texto or texto in ["-", "None", ""]:
        return None
    try:
        t = str(texto).strip()
        if ":" in t:
            partes = t.split(":")
            return time(int(partes[0]), int(partes[1]))
        val = int(float(t.replace(",", ".")))
        return time(val, 0)
    except Exception:
        return None

def validar_usuario(correo_ingresado, password_ingresada):
    try:
        libro = conectar_libro()
        hoja_t = libro.worksheet("TRABAJADORES")
        registros = hoja_t.get_all_values()[1:]
        
        for fila in registros:
            if len(fila) < 3:
                continue
            nombre = fila[0].strip()
            correo_db = fila[1].strip()
            password_db = fila[2].strip()
            rol_txt = fila[3].strip().lower() if len(fila) > 3 and fila[3].strip() else ""
            
            if rol_txt == "admin" or "manuel" in nombre.lower():
                rol = "admin"
            else:
                rol = "trabajador"
            
            if correo_ingresado.lower() == correo_db.lower() and password_ingresada == password_db:
                return True, nombre, rol
                
        return False, None, None
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return False, None, None

def generar_pdf_horas(nombre_t, reg_tabla, tot_hn_str, tot_hr_str):
    if not REPORTLAB_DISPONIBLE:
        return None
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    elementos = []
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'TituloPDF',
        parent=estilos['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1a1e29")
    )
    estilo_sub = ParagraphStyle(
        'SubtituloPDF',
        parent=estilos['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4a5568")
    )
    estilo_totales = ParagraphStyle(
        'TotalesPDF',
        parent=estilos['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#ff4b4b")
    )

    elementos.append(Paragraph("REPORTE MENSUAL DE HORAS TRABAJADAS", estilo_titulo))
    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph(f"<b>Trabajador:</b> {nombre_t} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Período:</b> SEPTIEMBRE 2026", estilo_sub))
    elementos.append(Spacer(1, 4))
    elementos.append(Paragraph(f"<b>Total Horas Extras:</b> {tot_hn_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Horas Recargo:</b> {tot_hr_str}", estilo_totales))
    elementos.append(Spacer(1, 14))

    data_tabla = [["DÍA", "ENTRADA", "SALIDA", "H.NORMAL", "H.RECARGO", "OBRA"]]
    
    for r in reg_tabla:
        data_tabla.append([
            str(r["DÍA"]),
            str(r["ENTRADA"]),
            str(r["SALIDA"]),
            str(r["HORA EXTRA"]),
            str(r["HORA RECARGO"]),
            str(r["OBRA"])
        ])

    t = Table(data_tabla, colWidths=[40, 65, 65, 80, 80, 210])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a1e29")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
    ]))

    elementos.append(t)
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

# --- PERSISTENCIA AUTOMÁTICA (LOCALSTORAGE) ---
if not st.session_state.get("autenticado") and "session" not in st.query_params:
    st.components.v1.html("""
        <script>
            const tokenGuardado = localStorage.getItem('control_horas_token');
            if (tokenGuardado && !window.location.search.includes('session=')) {
                window.location.search = '?session=' + tokenGuardado;
            }
        </script>
    """, height=0)

query_params = st.query_params
if "session" in query_params and not st.session_state.get("autenticado"):
    correo_token = verificar_token(query_params["session"])
    if correo_token:
        usuarios_map = cargar_trabajadores()
        if correo_token.lower() in usuarios_map:
            st.session_state["autenticado"] = True
            st.session_state["user_email"] = correo_token.lower()
            st.session_state["nombre_usuario"] = usuarios_map[correo_token.lower()]["nombre"]
            st.session_state["rol_usuario"] = usuarios_map[correo_token.lower()]["rol"]

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = "trabajador"
if "cambiando_password" not in st.session_state:
    st.session_state.cambiando_password = False
if "modo_admin_activo" not in st.session_state:
    st.session_state.modo_admin_activo = False

# Fecha simulada global para Administrador (None usa la fecha real del sistema)
if "fecha_admin_simulada" not in st.session_state:
    st.session_state["fecha_admin_simulada"] = None

# Fechas del ciclo activo
inicio_mes = date(2026, 8, 31)
fin_mes = date(2026, 9, 30)
delta_dias = (fin_mes - inicio_mes).days + 1
fechas_periodo = [inicio_mes + timedelta(days=i) for i in range(delta_dias)]

if not st.session_state.autenticado:
    st.title("🔐 Acceso a APP DE HORAS")
    st.write("Por favor, ingresa tu correo electrónico y contraseña para continuar.")
    
    with st.form("form_login"):
        correo_input = st.text_input("Correo Electrónico")
        password_input = st.text_input("Contraseña (Número de Teléfono)", type="password")
        submit_button = st.form_submit_button("Iniciar Sesión")
        
        if submit_button:
            valido, nombre, rol = validar_usuario(correo_input, password_input)
            if valido:
                st.session_state["autenticado"] = True
                st.session_state["nombre_usuario"] = nombre
                st.session_state["user_email"] = correo_input.lower()
                st.session_state["rol_usuario"] = rol
                token_firmado = firmar_correo(correo_input.lower())
                st.query_params["session"] = token_firmado
                
                st.components.v1.html(f"""
                    <script>
                        localStorage.setItem('control_horas_token', '{token_firmado}');
                    </script>
                """, height=0)

                st.success(f"¡Bienvenido, {nombre}!")
                st.rerun()
            else:
                st.error("Correo o contraseña incorrectos. Verifica tus datos.")

else:
    correo_google = st.session_state["user_email"]
    usuarios_autorizados = cargar_trabajadores()
    lista_obras = cargar_obras()
    nombre_trabajador = st.session_state.nombre_usuario
    es_admin = st.session_state.get("rol_usuario", "trabajador") == "admin"
    hoja_usuario = obtener_hoja_trabajador(nombre_trabajador)

    # Determinación centralizada de la fecha activa del sistema
    if es_admin and st.session_state.get("fecha_admin_simulada") is not None:
        hoy = st.session_state["fecha_admin_simulada"]
    else:
        hoy = date.today()

    if st.session_state.get("cambiando_password", False):
        st.subheader("🔑 Cambiar Contraseña")
        with st.form("form_cambiar_pass"):
            pass_actual = st.text_input("Contraseña Actual", type="password")
            pass_nueva = st.text_input("Nueva Contraseña", type="password")
            pass_confirmar = st.text_input("Confirmar Nueva Contraseña", type="password")
            btn_guardar_pass = st.form_submit_button("Actualizar Contraseña")
            
            if btn_guardar_pass:
                if pass_nueva != pass_confirmar:
                    st.warning("⚠️ Las nuevas contraseñas no coinciden.")
                elif not pass_actual or not pass_nueva:
                    st.warning("⚠️ Todos los campos son obligatorios.")
                else:
                    try:
                        libro = conectar_libro()
                        hoja_t = libro.worksheet("TRABAJADORES")
                        celdas = hoja_t.findall(correo_google)
                        encontrado = False
                        for celda in celdas:
                            fila_idx = celda.row
                            correo_en_tabla = hoja_t.cell(fila_idx, 2).value
                            pass_en_tabla = hoja_t.cell(fila_idx, 3).value
                            if correo_en_tabla and correo_en_tabla.strip().lower() == correo_google.lower():
                                if pass_en_tabla.strip() == pass_actual.strip():
                                    hoja_t.update_cell(fila_idx, 3, pass_nueva.strip())
                                    encontrado = True
                                    break
                        if encontrado:
                            st.success("✔ ¡Contraseña actualizada con éxito!")
                            st.session_state.cambiando_password = False
                            st.rerun()
                        else:
                            st.error("❌ Contraseña actual incorrecta.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    elif st.session_state.get("modo_admin_activo", False) and es_admin:
        # ==========================================================
        # VISTA: PANEL ADMINISTRADOR ULTRA COMPACTO
        # ==========================================================
        c_head1, c_head2 = st.columns([75, 25])
        with c_head1:
            st.markdown("### 🛠️ PANEL DE ADMINISTRADOR")
        with c_head2:
            if st.button("⬅️ Volver", use_container_width=True):
                st.session_state["modo_admin_activo"] = False
                st.rerun()

        st.caption("Control global de personal, ciclo activo y simulación de fechas.")

        # --- SECCIÓN 1: SIMULACIÓN DE FECHA (TOTALMENTE LADO A LADO) ---
        with st.container(border=True):
            st.markdown("**🕒 Simulación de Fecha del Sistema**")
            st.markdown('<span class="admin-sim-marker"></span>', unsafe_allow_html=True)
            
            c_s1, c_s2, c_s3 = st.columns([54, 23, 23])
            with c_s1:
                fecha_input_admin = st.date_input(
                    "Fecha simulación",
                    value=st.session_state["fecha_admin_simulada"] or date.today(),
                    label_visibility="collapsed"
                )
            with c_s2:
                if st.button("⚡ Activar", use_container_width=True):
                    st.session_state["fecha_admin_simulada"] = fecha_input_admin
                    st.rerun()
            with c_s3:
                if st.button("🔄 Reset", use_container_width=True):
                    st.session_state["fecha_admin_simulada"] = None
                    st.rerun()

            if st.session_state["fecha_admin_simulada"] is not None:
                st.warning(f"⚠️ Simulando: **{st.session_state['fecha_admin_simulada'].strftime('%d/%m/%Y')}**")

        # --- SECCIÓN 2: FECHA DE CICLO (LADO A LADO 50/50) ---
        with st.container(border=True):
            st.markdown("**📅 Rango de Fechas del Ciclo**")
            st.markdown('<span class="admin-ciclo-marker"></span>', unsafe_allow_html=True)
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                nuevo_inicio = st.date_input("Inicio del Ciclo", value=inicio_mes)
            with c_f2:
                nuevo_fin = st.date_input("Término del Ciclo", value=fin_mes)

        # --- SECCIÓN 3: LISTADO GENERAL ABIERTO AL 100% (SIN CORREO, DÍAS PENDIENTES) ---
        st.markdown("**👥 Resumen General del Personal**")
        try:
            libro_admin = conectar_libro()
            
            # LÓGICA DE DÍAS EXIGIBLES:
            # - Días de lunes a viernes y feriados pasados
            # - Sábado: SOLO es exigible si hoy es LUNES (o posterior) en la misma semana
            dias_exigibles = []
            for f in fechas_periodo:
                if f <= hoy:
                    es_domingo = (f.weekday() == 6)
                    es_feriado = (f.strftime("%Y-%m-%d") in FERIADOS)
                    
                    if es_domingo or es_feriado:
                        continue
                    
                    # Si es sábado: solo se exige si ya llegó el lunes siguiente
                    if f.weekday() == 5:
                        lunes_siguiente = f + timedelta(days=2)
                        if hoy < lunes_siguiente:
                            continue
                    
                    dias_exigibles.append(f.day)

            filas_html = []
            for correo_w, info_w in usuarios_autorizados.items():
                nom = info_w["nombre"]
                try:
                    h_w = libro_admin.worksheet(nom)
                    vals = h_w.get("A2:G32")
                    dias_con_datos = set()
                    for idx, r in enumerate(vals):
                        n_dia = int(r[1]) if len(r) > 1 and r[1].isdigit() else (idx + 1)
                        c_ent = r[2].strip() if len(r) > 2 else ""
                        c_obr = r[6].strip() if len(r) > 6 else ""
                        if c_ent or c_obr:
                            dias_con_datos.add(n_dia)
                    
                    faltan = sum(1 for d in dias_exigibles if d not in dias_con_datos)
                except Exception:
                    faltan = len(dias_exigibles)

                if faltan == 0:
                    badge = '<span style="color: #4ade80; font-weight: 700;">Al día ✔</span>'
                else:
                    badge = f'<span style="color: #f87171; font-weight: 700;">{faltan} días pendientes</span>'

                filas_html.append(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid #2e3547;background-color:#1a1e29;font-size:0.82rem;"><div style="color:#ffffff;font-weight:600;">{nom}</div><div>{badge}</div></div>')

            filas_str = "".join(filas_html)
            tabla_html = f'<div style="width:100%;border:1px solid #2e3547;border-radius:8px;overflow:hidden;margin-top:6px;box-sizing:border-box;"><div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background-color:#222634;border-bottom:1px solid #2e3547;font-size:0.72rem;font-weight:700;color:#a3adc2;"><div>TRABAJADOR</div><div>ESTADO DE REGISTRO</div></div>{filas_str}</div>'

            st.markdown(tabla_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"No se pudo cargar el resumen global: {e}")

    else:
        # Indicador informativo si el admin está simulando fecha en su vista de usuario
        if es_admin and st.session_state.get("fecha_admin_simulada") is not None:
            st.info(f"🕒 Modo simulación activo: **{hoy.strftime('%d/%m/%Y')}** (Configurado desde Panel Administrador)")

        # --- FILA SUPERIOR: NAVEGADOR Y TUERCA (POPOVER LIBRE DEBAJO) ---
        c_nav, c_gear = st.columns([88, 12])

        with c_nav:
            opciones_nav = ["📅 SEPTIEMBRE 2026", "📊 RESUMEN DEL MES"]
            if "vista_actual" not in st.session_state:
                st.session_state["vista_actual"] = "SEPTIEMBRE"

            val_default = "📅 SEPTIEMBRE 2026" if st.session_state["vista_actual"] == "SEPTIEMBRE" else "📊 RESUMEN DEL MES"

            seleccion = st.pills(
                "",
                options=opciones_nav,
                default=val_default,
                label_visibility="collapsed",
                key="pills_navegacion"
            )

            nueva_vista = "SEPTIEMBRE" if seleccion == "📅 SEPTIEMBRE 2026" else "RESUMEN"
            if nueva_vista != st.session_state["vista_actual"]:
                st.session_state["vista_actual"] = nueva_vista
                if nueva_vista == "SEPTIEMBRE":
                    st.session_state["dia_en_edicion"] = None
                st.rerun()

        with c_gear:
            with st.popover("⚙️"):
                st.markdown(f"**👤 {nombre_trabajador}**")
                if es_admin:
                    st.markdown("🔑 *Rol: Administrador*")
                st.markdown("---")
                
                if es_admin:
                    if st.button("🛠️ Panel Administrador", use_container_width=True):
                        st.session_state["modo_admin_activo"] = True
                        st.session_state["cambiando_password"] = False
                        st.rerun()

                if st.button("🔑 Cambiar Contraseña", use_container_width=True):
                    st.session_state["cambiando_password"] = True
                    st.session_state["modo_admin_activo"] = False
                    st.rerun()

                if st.button("🚪 Cerrar Sesión", use_container_width=True):
                    st.components.v1.html("""
                        <script>
                            localStorage.removeItem('control_horas_token');
                        </script>
                    """, height=0)
                    st.query_params.clear()
                    st.session_state.autenticado = False
                    st.session_state.nombre_usuario = ""
                    st.session_state.user_email = ""
                    st.session_state.rol_usuario = "trabajador"
                    st.session_state.cambiando_password = False
                    st.session_state.modo_admin_activo = False
                    st.rerun()

        st.markdown("---")

        if "filas_planilla" not in st.session_state:
            try:
                st.session_state["filas_planilla"] = hoja_usuario.get("A2:G32")
            except Exception:
                st.session_state["filas_planilla"] = []

        filas_planilla = st.session_state["filas_planilla"]
        dict_por_dia = {}
        registros_tabla = []
        total_hn = 0
        total_hr = 0

        for idx, r in enumerate(filas_planilla):
            num_dia = int(r[1]) if len(r) > 1 and r[1].isdigit() else (idx + 1)
            entrada = r[2] if len(r) > 2 else ""
            salida = r[3] if len(r) > 3 else ""
            hn_val = r[4] if len(r) > 4 else ""
            hr_val = r[5] if len(r) > 5 else ""
            obra_val = r[6] if len(r) > 6 else ""

            dict_por_dia[num_dia] = {
                "entrada": entrada, "salida": salida,
                "hn": hn_val, "hr": hr_val, "obra": obra_val
            }

            def a_minutos(txt):
                if not txt: return 0
                t = str(txt).strip()
                if ":" in t:
                    p = t.split(":")
                    return int(float(p[0])) * 60 + int(float(p[1]))
                return int(round(float(t.replace(",", ".")) * 60))

            try: total_hn += a_minutos(hn_val)
            except Exception: pass
            try: total_hr += a_minutos(hr_val)
            except Exception: pass

            try:
                f_fila = date(2026, 8, 31) if num_dia == 31 else date(2026, 9, num_dia)
            except Exception:
                f_fila = None

            es_domingo_o_feriado = False
            if f_fila:
                es_domingo_o_feriado = (f_fila.weekday() == 6) or (f_fila.strftime("%Y-%m-%d") in FERIADOS)

            # LÓGICA SÁBADO NO TRABAJADO (AUTOMÁTICA EL LUNES):
            es_sabado_pasado_sin_trabajar = False
            if f_fila and f_fila.weekday() == 5 and f_fila < hoy:
                lunes_despues = f_fila + timedelta(days=2)
                if hoy >= lunes_despues and not (entrada or salida or obra_val):
                    es_sabado_pasado_sin_trabajar = True

            if entrada or salida or obra_val:
                registros_tabla.append({
                    "DÍA": num_dia, "ENTRADA": entrada, "SALIDA": salida,
                    "HORA EXTRA": hn_val, "HORA RECARGO": hr_val, "OBRA": obra_val
                })
            elif (es_domingo_o_feriado and f_fila and f_fila < hoy) or es_sabado_pasado_sin_trabajar:
                registros_tabla.append({
                    "DÍA": num_dia, "ENTRADA": "", "SALIDA": "",
                    "HORA EXTRA": "", "HORA RECARGO": "", "OBRA": ""
                })

        registros_tabla = sorted(registros_tabla, key=lambda x: (0 if x["DÍA"] == 31 else x["DÍA"]))

        # --- VISTA 1: SEPTIEMBRE (REGISTRO DIARIO) ---
        if st.session_state["vista_actual"] == "SEPTIEMBRE":
            st.subheader("SEPTIEMBRE 2026")
            
            val_hn_str = minutos_a_hora_str(total_hn)
            val_hr_str = minutos_a_hora_str(total_hr)
            
            st.markdown(f'''
            <div style="display: flex; gap: 10px; width: 100%; margin-bottom: 1rem;">
                <div style="flex: 1; min-width: 0; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px; font-weight: 500; white-space: nowrap;">Total Horas Extras (Mes)</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff; white-space: nowrap;">{val_hn_str}</div>
                </div>
                <div style="flex: 1; min-width: 0; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px; font-weight: 500; white-space: nowrap;">Total Horas Recargo (Mes)</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff; white-space: nowrap;">{val_hr_str}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown("---")

            dias_pendientes = []
            for f in fechas_periodo:
                num_dia = f.day
                fecha_iso = f.strftime("%Y-%m-%d")
                es_domingo_o_feriado = (f.weekday() == 6) or (fecha_iso in FERIADOS)

                if es_domingo_o_feriado and f < hoy:
                    continue

                # Si es sábado que ya pasó y hoy es lunes o posterior, y no tiene datos, se omite
                if f.weekday() == 5 and f < hoy:
                    lunes_despues = f + timedelta(days=2)
                    if hoy >= lunes_despues:
                        guardado_sab = dict_por_dia.get(num_dia, {})
                        if not (guardado_sab.get("entrada") or guardado_sab.get("salida") or guardado_sab.get("obra")):
                            continue

                guardado = dict_por_dia.get(num_dia, {})
                if not (guardado.get("entrada") or guardado.get("salida") or guardado.get("obra")):
                    dias_pendientes.append(f)

            if not dias_pendientes:
                st.success("🎉 ¡Todos los días del mes ya han sido completados!")
            else:
                for f in dias_pendientes:
                    nom_dia = DIAS_MAP[f.weekday()]
                    num_dia = f.day
                    fecha_iso = f.strftime("%Y-%m-%d")
                    es_festivo = fecha_iso in FERIADOS

                    espacio_relleno = " " * (9 - len(nom_dia))
                    dia_base = f"{nom_dia}{espacio_relleno} | {num_dia:02d}"

                    if es_festivo or f.weekday() == 6:
                        col_dia_num = f":violet[{dia_base}]"
                    elif f.weekday() == 5:
                        col_dia_num = f":blue[{dia_base}]"
                    else:
                        col_dia_num = dia_base

                    aviso = " :violet[(FERIADO)]" if es_festivo else ""
                    label = f"⚪ {col_dia_num}{aviso}"

                    with st.expander(label):
                        with st.form(key=f"form_dia_{num_dia}"):
                            c_ent, c_sal = st.columns(2)
                            with c_ent:
                                inp_ent = st.time_input("Entrada", value=None, key=f"e_{num_dia}")
                            with c_sal:
                                inp_sal = st.time_input("Salida", value=None, key=f"s_{num_dia}")

                            inp_ob = st.selectbox("Obra", options=lista_obras, index=None, placeholder="Seleccionar...", key=f"o_{num_dia}")

                            st.write("")
                            col_btn, _ = st.columns([1, 3])
                            with col_btn:
                                guardar_btn = st.form_submit_button("💾 Guardar Registro", use_container_width=True)

                            if guardar_btn:
                                es_especial = inp_ob and inp_ob.strip().upper() in ["PERMISO", "NO TRABAJA"]
                                if not inp_ob:
                                    st.warning("⚠️ Debes seleccionar una Obra.")
                                elif not es_especial and (inp_ent is None or inp_sal is None):
                                    st.warning("⚠️ Debes ingresar Entrada y Salida para las obras normales.")
                                else:
                                    with st.spinner("Guardando en la planilla..."):
                                        try:
                                            fila_n = fila_segun_dia(num_dia)
                                            if es_especial:
                                                hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["-", "-"]], value_input_option="RAW")
                                                hoja_usuario.update(f"G{fila_n}", [[inp_ob]], value_input_option="RAW")
                                            else:
                                                ent_str = inp_ent.strftime("%H:%M")
                                                sal_str = inp_sal.strftime("%H:%M")
                                                hoja_usuario.update(f"C{fila_n}:D{fila_n}", [[ent_str, sal_str]], value_input_option="USER_ENTERED")
                                                hoja_usuario.update(f"G{fila_n}", [[inp_ob]], value_input_option="USER_ENTERED")

                                            if "filas_planilla" in st.session_state:
                                                del st.session_state["filas_planilla"]

                                            st.session_state["vista_actual"] = "RESUMEN"
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error al guardar: {err}")

        # --- VISTA 2: RESUMEN MENSUAL CON TABLA LIMPIA Y LÁPIZ LATERAL ---
        elif st.session_state["vista_actual"] == "RESUMEN":
            st.subheader("RESUMEN MENSUAL")
            
            val_hn_str = minutos_a_hora_str(total_hn)
            val_hr_str = minutos_a_hora_str(total_hr)
            
            html_cards_res = f"""
            <div style="display: flex; gap: 10px; width: 100%; margin-bottom: 1rem;">
                <div style="flex: 1; min-width: 0; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px; font-weight: 500; white-space: nowrap;">Total Horas Extras (Mes)</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff; white-space: nowrap;">{val_hn_str}</div>
                </div>
                <div style="flex: 1; min-width: 0; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px; font-weight: 500; white-space: nowrap;">Total Horas Recargo (Mes)</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff; white-space: nowrap;">{val_hr_str}</div>
                </div>
            </div>
            """
            st.markdown(html_cards_res, unsafe_allow_html=True)
            st.markdown("---")

            if "dia_en_edicion" not in st.session_state:
                st.session_state["dia_en_edicion"] = None

            if registros_tabla:
                col_encabezado, _ = st.columns([93, 7])
                with col_encabezado:
                    st.markdown('''
                    <div class="contenedor-tabla-6 es-encabezado-6">
                        <div>DÍA</div>
                        <div>ENTRADA</div>
                        <div>SALIDA</div>
                        <div>H.NORMAL</div>
                        <div>H.RECARGO</div>
                        <div>OBRA</div>
                    </div>
                    ''', unsafe_allow_html=True)

                for r in registros_tabla:
                    d = r["DÍA"] 
                    
                    try:
                        fecha_fila = date(2026, 8, 31) if d == 31 else date(2026, 9, d)
                        w_day = fecha_fila.weekday()
                        iso_f = fecha_fila.strftime("%Y-%m-%d")
                    except:
                        w_day = 0
                        iso_f = ""
                    
                    es_festivo = iso_f in FERIADOS
                    
                    if es_festivo or w_day == 6:
                        color_dia = "#b388ff"
                        dia_txt = f"{d} (F)" if es_festivo else str(d)
                    elif w_day == 5:
                        color_dia = "#448aff"
                        dia_txt = str(d)
                    else:
                        color_dia = "#ffffff"
                        dia_txt = str(d)

                    ent_val = r["ENTRADA"].strip() if r["ENTRADA"].strip() else "&nbsp;"
                    sal_val = r["SALIDA"].strip() if r["SALIDA"].strip() else "&nbsp;"
                    hn_val = r["HORA EXTRA"].strip() if r["HORA EXTRA"].strip() else "&nbsp;"
                    hr_val = r["HORA RECARGO"].strip() if r["HORA RECARGO"].strip() else "&nbsp;"
                    ob_val = r["OBRA"].strip() if r["OBRA"].strip() else "&nbsp;"

                    c_fila, c_lapiz = st.columns([93, 7])

                    with c_fila:
                        st.markdown(f'''
                        <div class="es-datos-6 contenedor-tabla-6">
                            <div style="color: {color_dia}; font-weight: 700;">{dia_txt}</div>
                            <div>{ent_val}</div>
                            <div>{sal_val}</div>
                            <div>{hn_val}</div>
                            <div>{hr_val}</div>
                            <div>{ob_val}</div>
                        </div>
                        ''', unsafe_allow_html=True)

                    with c_lapiz:
                        if st.button("✏️", key=f"btn_lapiz_{d}"):
                            if st.session_state.get("dia_en_edicion") == d:
                                st.session_state["dia_en_edicion"] = None
                            else:
                                st.session_state["dia_en_edicion"] = d
                            st.rerun()

                    if st.session_state.get("dia_en_edicion") == d:
                        datos_d = dict_por_dia.get(d, {})
                        val_e = str_a_time(datos_d.get("entrada", ""))
                        val_s = str_a_time(datos_d.get("salida", ""))
                        val_o = datos_d.get("obra", "")
                        idx_o = lista_obras.index(val_o) if val_o and val_o in lista_obras else 0

                        with st.form(key=f"form_inline_dia_{d}"):
                            c1e, c2e = st.columns(2)
                            with c1e:
                                edit_ent = st.time_input("Entrada", value=val_e, key=f"re_{d}")
                            with c2e:
                                edit_sal = st.time_input("Salida", value=val_s, key=f"rs_{d}")
                            
                            edit_ob = st.selectbox("Obra", options=lista_obras, index=idx_o, key=f"ro_{d}")

                            st.write("")
                            b1, b2 = st.columns(2)
                            with b1:
                                btn_guardar_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                            with b2:
                                btn_borrar_edit = st.form_submit_button("🧹 Limpiar Registro", use_container_width=True)

                            if btn_guardar_edit:
                                es_especial_edit = edit_ob and edit_ob.strip().upper() in ["PERMISO", "NO TRABAJA"]
                                if not edit_ob:
                                    st.warning("⚠️ Debes seleccionar Obra.")
                                elif not es_especial_edit and (edit_ent is None or edit_sal is None):
                                    st.warning("⚠️ Debes completar Entrada y Salida.")
                                else:
                                    with st.spinner("Actualizando planilla..."):
                                        fila_n = fila_segun_dia(d)
                                        if es_especial_edit:
                                            hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["-", "-"]], value_input_option="RAW")
                                            hoja_usuario.update(f"G{fila_n}", [[edit_ob]], value_input_option="RAW")
                                        else:
                                            ent_str = edit_ent.strftime("%H:%M")
                                            sal_str = edit_sal.strftime("%H:%M")
                                            hoja_usuario.update(f"C{fila_n}:D{fila_n}", [[ent_str, sal_str]], value_input_option="USER_ENTERED")
                                            hoja_usuario.update(f"G{fila_n}", [[edit_ob]], value_input_option="USER_ENTERED")

                                        if "filas_planilla" in st.session_state:
                                            del st.session_state["filas_planilla"]
                                        st.session_state["dia_en_edicion"] = None
                                        st.rerun()

                            if btn_borrar_edit:
                                with st.spinner("Limpiando registro..."):
                                    fila_n = fila_segun_dia(d)
                                    hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["", ""]], value_input_option="USER_ENTERED")
                                    hoja_usuario.update(f"G{fila_n}", [[""]], value_input_option="USER_ENTERED")

                                    if "filas_planilla" in st.session_state:
                                        del st.session_state["filas_planilla"]
                                    st.session_state["dia_en_edicion"] = None
                                    st.session_state["vista_actual"] = "SEPTIEMBRE"
                                    st.rerun()

            else:
                st.info("Aún no tienes jornadas registradas en este mes.")

            st.markdown("---")

            if REPORTLAB_DISPONIBLE:
                pdf_bytes = generar_pdf_horas(
                    nombre_trabajador,
                    registros_tabla,
                    val_hn_str,
                    val_hr_str
                )
                nombre_archivo_pdf = f"Horas_{nombre_trabajador.replace(' ', '_')}_Septiembre_2026.pdf"

                st.download_button(
                    label="📄 DESCARGAR HORAS DEL MES EN PDF",
                    data=pdf_bytes,
                    file_name=nombre_archivo_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Para habilitar la descarga en PDF en Streamlit Cloud, añade 'reportlab' en tu archivo requirements.txt en GitHub.")