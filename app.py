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

/* Scroll fluido total en la vista */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    overflow-y: auto !important;
    height: auto !important;
    min-height: 100% !important;
}

.block-container { 
    max-width: 95% !important; 
    padding: 1.5rem !important; 
    padding-bottom: 25rem !important; 
}

div[data-testid="stForm"] { 
    border: none !important; 
    padding: 0 !important; 
    margin-top: 0.5rem !important; 
    margin-bottom: 0.5rem !important; 
}

div[data-testid="stVerticalBlock"] {
    gap: 0.1rem !important;
}

/* ==========================================================
   ESTRUCTURA CSS GRID DE 6 COLUMNAS (TABLA SIN COLUMNA EDITAR)
   ========================================================== */
.contenedor-tabla-6 {
    display: grid !important;
    grid-template-columns: 8% 18% 18% 18% 18% 20% !important;
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

/* ==========================================================
   BOTÓN LÁPIZ LATERAL FLOTANTE / EXTERNO A LA TABLA
   ========================================================== */
div.lapiz-lateral-wrapper {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

div.lapiz-lateral-wrapper button {
    background-color: #1a1e29 !important;
    border: 1px solid #353b4d !important;
    color: white !important;
    border-radius: 5px !important;
    padding: 0 !important;
    min-height: 22px !important;
    height: 22px !important;
    width: 28px !important;
    font-size: 0.65rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transform: translateY(6px) !important; /* Mueve el botón hacia abajo */
}

/* Achica el emoji/ícono dentro del botón */
div.lapiz-lateral-wrapper button p {
    font-size: 0.70rem !important;
    line-height: 1 !important;
    margin: 0 !important;
}
/* Forzar que las columnas nunca se rompan verticalmente sin importar el zoom */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
    min-width: 0 !important;
    flex: 1 1 93% !important;
    width: 93% !important;
}

div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
    min-width: 38px !important;
    flex: 0 0 7% !important;
    width: 7% !important;
}

div.lapiz-lateral-wrapper {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 0 !important;
}

/* Eliminar completamente el espacio entre filas forzando solape vertical */
div[data-testid="stVerticalBlock"]:has(div.es-datos-6) {
    gap: 0 !important;
    row-gap: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(div.es-datos-6) > div {
    margin-bottom: -10px !important;
    padding-bottom: 0 !important;
    padding-top: 0 !important;
}

div[data-testid="stHorizontalBlock"] {
    margin-bottom: 0 !important;
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

if not st.session_state.autenticado:
    st.title("🔐 Acceso a APP DE HORAS")
    st.write(f"Por favor, ingresa tu correo electrónico y contraseña para continuar[cite: 1].")
    
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

    # --- MENÚ DESPLEGABLE DE CONFIGURACIÓN (⚙️) ---
    c_gear, _ = st.columns([2.0, 8.0])
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
        # --- VISTA: MODO ADMINISTRADOR ---
        st.subheader("🛠️ PANEL DE ADMINISTRADOR")
        st.write("Control global de personal y selector de ciclos mensuales.")
        
        if st.button("⬅️ Volver a mi vista normal"):
            st.session_state["modo_admin_activo"] = False
            st.rerun()

        st.markdown("---")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            nuevo_inicio = st.date_input("Fecha Inicio de Ciclo", value=date(2026, 8, 31))
        with c_f2:
            nuevo_fin = st.date_input("Fecha Término de Ciclo", value=date(2026, 9, 30))

        st.markdown("### 👥 Listado General de Trabajadores")
        try:
            libro_admin = conectar_libro()
            resumen_global = []
            for correo_w, info_w in usuarios_autorizados.items():
                nom = info_w["nombre"]
                try:
                    h_w = libro_admin.worksheet(nom)
                    vals = h_w.get_all_values()[1:]
                    total_dias_reg = sum(1 for r in vals if len(r) > 2 and (r[2].strip() or r[6].strip()))
                    resumen_global.append({"Trabajador": nom, "Correo": correo_w, "Días Registrados": total_dias_reg})
                except Exception:
                    resumen_global.append({"Trabajador": nom, "Correo": correo_w, "Días Registrados": 0})
            
            df_global = pd.DataFrame(resumen_global)
            st.dataframe(df_global, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo cargar el resumen global: {e}")

    else:
        # --- NAVEGACIÓN PRINCIPAL (SEPTIEMBRE / RESUMEN LADO A LADO) ---
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
                # Contenedor 93% tabla achicada + 7% para el lápiz exterior
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

                # --- FILAS DE DATOS + BOTÓN LÁPIZ LATERAL EXTERIOR ---
                for r in registros_tabla:
                    d = r["DÍA"] 
                    
                    try:
                        fecha_fila = date(2026, 9, d)
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

                    hn_val = r["HORA EXTRA"].strip() if r["HORA EXTRA"].strip() else "&nbsp;"
                    hr_val = r["HORA RECARGO"].strip() if r["HORA RECARGO"].strip() else "&nbsp;"

                    c_fila, c_lapiz = st.columns([93, 7])

                    with c_fila:
                        st.markdown(f'''
                        <div class="es-datos-6 contenedor-tabla-6">
                            <div style="color: {color_dia}; font-weight: 700;">{dia_txt}</div>
                            <div>{r["ENTRADA"]}</div>
                            <div>{r["SALIDA"]}</div>
                            <div>{hn_val}</div>
                            <div>{hr_val}</div>
                            <div>{r["OBRA"]}</div>
                        </div>
                        ''', unsafe_allow_html=True)

                    with c_lapiz:
                        st.markdown('<div class="lapiz-lateral-wrapper">', unsafe_allow_html=True)
                        if st.button("✏️", key=f"edit_btn_{d}"):
                            if st.session_state.get("dia_en_edicion") == d:
                                st.session_state["dia_en_edicion"] = None
                            else:
                                st.session_state["dia_en_edicion"] = d
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Formulario desplegable al presionar el lápiz (Toggle abrir/cerrar)
                    if st.session_state.get("dia_en_edicion") == d:
                        datos_d = dict_por_dia.get(d, {})
                        val_e = str_a_time(datos_d.get("entrada", ""))
                        val_s = str_a_time(datos_d.get("salida", ""))
                        val_o = datos_d.get("obra", "")
                        idx_o = lista_obras.index(val_o) if val_o and val_o in lista_obras else 0

                        with st.form(key=f"form_inline_dia_{d}"):
                            st.markdown(f"**✏️ Editando Día {d}**")
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
            # --- BOTÓN DE REPORTE PDF ABAJO ---
            if st.button("📄 DESCARGAR HORAS DEL MES EN PDF", use_container_width=True):
                st.info("ℹ️ Módulo de PDF listo para ser conectado.")