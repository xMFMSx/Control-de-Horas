import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import json
import base64
import hmac
import hashlib
from datetime import datetime, date, time, timedelta
import time as time_lib
import urllib.parse

st.set_page_config(
    page_title="Control de Horas",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
/* Ocultar elementos nativos de Streamlit */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
footer { visibility: hidden !important; }
div[data-testid="stDecoration"] { display: none !important; }

.block-container {
    max-width: 95% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-top: 2.2rem !important;
    padding-bottom: 3rem !important;
}

div[data-testid="stExpander"] { width: 100% !important; }
div[data-testid="stExpander"] summary p {
    font-family: 'Consolas', 'Courier New', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: #FFFFFF !important;
}

/* Espacio seguro para el formulario de edición */
div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
}

/* --- 1. ENCABEZADO PURO HTML --- */
.encabezado-puro {
    display: flex !important;
    width: 100% !important;
    border-top: 1px solid #282d3c !important;
    border-bottom: 1px solid #282d3c !important;
    padding: 6px 0px !important;
    margin-top: 10px !important;
}
.datos-encabezado {
    width: 92% !important;
    display: flex !important;
    font-size: 0.65rem !important;
    color: #838c9e !important;
    font-weight: 600 !important;
    align-items: center !important;
}
.vacio-encabezado {
    width: 8% !important;
}

/* LA SOLUCIÓN AL ESPACIO: Aumentamos el margen inferior para separar el encabezado de los datos */
div[data-testid="stMarkdownContainer"]:has(.encabezado-puro) p {
    margin: 0 !important;
    padding: 0 !important;
}
div.element-container:has(.encabezado-puro),
div.stElementContainer:has(.encabezado-puro) {
    margin-bottom: 3px !important; /* <--- AUMENTADO PARA DAR SEPARACIÓN VISUAL */
}

/* --- 2. FILAS DE DATOS Y COLUMNAS --- */
div.element-container:has(.fila-datos),
div.stElementContainer:has(.fila-datos) {
    margin-top: -16px !important;
    margin-bottom: -16px !important; /* Mantiene unidas las filas de datos entre sí */
}

div[data-testid="stHorizontalBlock"]:has(.fila-datos) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0px !important; 
    border-bottom: 1px solid #1c202a !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
    width: 100% !important;
    min-height: 40px !important;
}

/* Forzar anchos mínimos exactos anti-móvil */
div[data-testid="stHorizontalBlock"]:has(.fila-datos) > div[data-testid="column"]:first-child {
    width: 92% !important;
    min-width: 92% !important;
    max-width: 92% !important;
    flex: 0 0 92% !important;
}
div[data-testid="stHorizontalBlock"]:has(.fila-datos) > div[data-testid="column"]:last-child {
    width: 8% !important;
    min-width: 8% !important;
    max-width: 8% !important;
    flex: 0 0 8% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* --- 3. ALINEACIÓN VERTICAL PERFECTA (Textos) --- */
div[data-testid="stHorizontalBlock"]:has(.fila-datos) div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
    gap: 0 !important;
    justify-content: center !important;
}
div[data-testid="stHorizontalBlock"]:has(.fila-datos) div.stElementContainer,
div[data-testid="stHorizontalBlock"]:has(.fila-datos) div.element-container,
div[data-testid="stHorizontalBlock"]:has(.fila-datos) div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.fila-datos) div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 28px !important; 
    transform: none !important; /* Limpiamos cualquier empuje extraño */
}

.fila-datos {
    display: flex !important;
    width: 100% !important;
    height: 28px !important; 
    font-size: 0.75rem !important;
    color: #ffffff !important;
    align-items: center !important;
}

/* Proporciones de las celdas de texto */
.c-dia { flex: 0 0 8%; font-weight: bold; }
.c-ent { flex: 0 0 16%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-sal { flex: 0 0 16%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-hn  { flex: 0 0 17%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-hr  { flex: 0 0 17%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-ob  { flex: 0 0 26%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* --- 4. DISEÑO DEL BOTÓN LÁPIZ Y EMOJI (Restaurado al centro exacto) --- */
div[data-testid="stHorizontalBlock"]:has(.fila-datos) div[data-testid="stButton"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.fila-datos) button {
    height: 28px !important;
    min-height: 28px !important;
    width: 28px !important;
    min-width: 28px !important;
    padding: 0 !important;
    margin: 0 auto !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

div[data-testid="stHorizontalBlock"]:has(.fila-datos) button p {
    font-size: 14px !important;
    line-height: 1 !important; 
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transform: none !important; /* Asegura que el icono no se caiga */
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

def conectar_libro(reintentos=3):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    for intento in range(reintentos):
        try:
            if "gcp_service_account" in st.secrets:
                cred_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
            else:
                creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
                
            client = gspread.authorize(creds)
            return client.open("APP DE HORAS")
        except Exception as e:
            if intento == reintentos - 1:
                raise e
            time_lib.sleep(1)

def obtener_hoja_trabajador(nombre_trabajador: str):
    clave = f"hoja_{nombre_trabajador}"
    if clave in st.session_state:
        return st.session_state[clave]
    if "libro_sheets" not in st.session_state:
        st.session_state["libro_sheets"] = conectar_libro()
    try:
        hoja = st.session_state["libro_sheets"].worksheet(nombre_trabajador)
    except Exception:
        st.session_state["libro_sheets"] = conectar_libro()
        hoja = st.session_state["libro_sheets"].worksheet(nombre_trabajador)
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
                usuarios[r[1].strip().lower()] = r[0].strip()
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
            
            if correo_ingresado.lower() == correo_db.lower() and password_ingresada == password_db:
                return True, nombre
                
        return False, None
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return False, None

# --- SCRIPT DE PERSISTENCIA AUTOMÁTICA (LOCALSTORAGE) ---
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
            st.session_state["nombre_usuario"] = usuarios_map[correo_token.lower()]

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "cambiando_password" not in st.session_state:
    st.session_state.cambiando_password = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso a APP DE HORAS")
    st.write("Por favor, ingresa tu correo electrónico y contraseña para continuar.")
    
    with st.form("form_login"):
        correo_input = st.text_input("Correo Electrónico")
        password_input = st.text_input("Contraseña (Número de Teléfono)", type="password")
        submit_button = st.form_submit_button("Iniciar Sesión")
        
        if submit_button:
            valido, nombre = validar_usuario(correo_input, password_input)
            if valido:
                st.session_state["autenticado"] = True
                st.session_state["nombre_usuario"] = nombre
                st.session_state["user_email"] = correo_input.lower()
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
    hoja_usuario = obtener_hoja_trabajador(nombre_trabajador)

    c_gear, _ = st.columns([2.0, 8.0])
    with c_gear:
        with st.popover("⚙️"):
            st.markdown(f"**👤 {nombre_trabajador}**")
            st.markdown("---")
            if st.button("🔑 Cambiar Contraseña", use_container_width=True):
                st.session_state.cambiando_password = True
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
                st.session_state.cambiando_password = False
                st.rerun()

    if st.session_state.get("cambiando_password", False):
        st.subheader("🔑 Cambiar Contraseña")
        st.write("Ingresa tu contraseña actual y tu nueva contraseña.")
        
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
                                else:
                                    st.error("❌ La contraseña actual es incorrecta.")
                                    encontrado = True
                                    break
                        if encontrado and pass_en_tabla.strip() == pass_actual.strip():
                            st.success("✔ ¡Contraseña actualizada con éxito en la nube!")
                            st.session_state.cambiando_password = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la contraseña: {e}")
    else:
        if "vista_actual" not in st.session_state:
            st.session_state["vista_actual"] = "SEPTIEMBRE"

        is_sep = st.session_state["vista_actual"] == "SEPTIEMBRE"
        bg_sep = "#ff4b4b" if is_sep else "#1a1e29"
        border_sep = "#ff4b4b" if is_sep else "#2e3547"
        bg_res = "#ff4b4b" if not is_sep else "#1a1e29"
        border_res = "#ff4b4b" if not is_sep else "#2e3547"

        session_actual = st.query_params.get("session", "")

        st.markdown(f'''
            <div style="display: flex; gap: 8px; width: 100%; margin-bottom: 1rem;">
                <form action="" method="get" style="flex: 1; margin: 0;">
                    <input type="hidden" name="session" value="{session_actual}">
                    <button type="submit" name="nav_vista" value="SEPTIEMBRE" style="width: 100%; background-color: {bg_sep}; border: 1px solid {border_sep}; color: white; padding: 0.6rem 0.2rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.82rem; white-space: nowrap; cursor: pointer;">📅 SEPTIEMBRE 2026</button>
                </form>
                <form action="" method="get" style="flex: 1; margin: 0;">
                    <input type="hidden" name="session" value="{session_actual}">
                    <button type="submit" name="nav_vista" value="RESUMEN" style="width: 100%; background-color: {bg_res}; border: 1px solid {border_res}; color: white; padding: 0.6rem 0.2rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.82rem; white-space: nowrap; cursor: pointer;">📊 RESUMEN DEL MES</button>
                </form>
            </div>
        ''', unsafe_allow_html=True)

        q_params = st.query_params
        if "nav_vista" in q_params:
            val_nav = q_params["nav_vista"]
            if val_nav in ["SEPTIEMBRE", "RESUMEN"] and st.session_state["vista_actual"] != val_nav:
                st.session_state["vista_actual"] = val_nav
                if val_nav == "SEPTIEMBRE":
                    st.session_state["dia_en_edicion"] = None
                del st.query_params["nav_vista"]
                st.rerun()

        st.markdown("---")

        inicio_mes = date(2026, 8, 31)
        fin_mes = date(2026, 9, 30)
        delta_dias = (fin_mes - inicio_mes).days + 1
        fechas_periodo = [inicio_mes + timedelta(days=i) for i in range(delta_dias)]

        if "filas_planilla" not in st.session_state:
            try:
                st.session_state["filas_planilla"] = hoja_usuario.get("A2:G32")
            except Exception:
                hoja_usuario = obtener_hoja_trabajador(nombre_trabajador)
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

            if entrada or salida or obra_val:
                registros_tabla.append({
                    "DÍA": num_dia, "ENTRADA": entrada, "SALIDA": salida,
                    "HORA EXTRA": hn_val, "HORA RECARGO": hr_val, "OBRA": obra_val
                })

        if st.session_state["vista_actual"] == "SEPTIEMBRE":
            st.subheader("SEPTIEMBRE 2026")
            
            val_hn_str = minutos_a_hora_str(total_hn)
            val_hr_str = minutos_a_hora_str(total_hr)
            html_cards = f'''
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
            '''
            st.markdown(html_cards, unsafe_allow_html=True)
            st.markdown("---")

            dias_pendientes = []
            for f in fechas_periodo:
                num_dia = f.day
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

            if "dia_en_edicion" not in st.session_state:
                st.session_state["dia_en_edicion"] = None

            if registros_tabla:
                # --- ENCABEZADO HTML PURO ---
                st.markdown("""
                <div class="encabezado-puro">
                    <div class="datos-encabezado">
                        <div style="flex: 0 0 8%;">DÍA</div>
                        <div style="flex: 0 0 16%;">ENTRADA</div>
                        <div style="flex: 0 0 16%;">SALIDA</div>
                        <div style="flex: 0 0 17%;">H.NORMAL</div>
                        <div style="flex: 0 0 17%;">H.RECARGO</div>
                        <div style="flex: 0 0 26%;">OBRA</div>
                    </div>
                    <div class="vacio-encabezado"></div>
                </div>
                """, unsafe_allow_html=True)

                for r in registros_tabla:
                    d = r["DÍA"] 
                    c_dat, c_b = st.columns([0.92, 0.08], vertical_alignment="center")
                    
                    with c_dat:
                        hn_val = r["HORA EXTRA"].strip() if r["HORA EXTRA"].strip() else "&nbsp;"
                        hr_val = r["HORA RECARGO"].strip() if r["HORA RECARGO"].strip() else "&nbsp;"
                        
                        st.markdown(f"""
                        <div class="fila-datos">
                            <div class="c-dia">{d}</div>
                            <div class="c-ent">{r["ENTRADA"]}</div>
                            <div class="c-sal">{r["SALIDA"]}</div>
                            <div class="c-hn">{hn_val}</div>
                            <div class="c-hr">{hr_val}</div>
                            <div class="c-ob">{r["OBRA"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_b:
                        if st.button("✏️", key=f"btn_edit_{d}"):
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
                                btn_borrar_edit = st.form_submit_button("🧹 Limpiar (volver a Septiembre)", use_container_width=True)

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