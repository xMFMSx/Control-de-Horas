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
/* Ocultar UI nativa */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
footer { visibility: hidden !important; }
div[data-testid="stDecoration"] { display: none !important; }

.block-container { max-width: 95% !important; padding: 2rem !important; padding-bottom: 3rem !important; }
div[data-testid="stForm"] { border: none !important; padding: 0 !important; margin-top: 1.5rem !important; margin-bottom: 1rem !important; }

/* ELIMINACIÓN TOTAL DE FRANJAS NEGRAS Y ESPACIOS ENTRE FILAS */
div.element-container:has(.contenedor-tabla), 
div.stElementContainer:has(.contenedor-tabla) {
    margin-bottom: -1px !important; 
    padding-bottom: 0 !important;
    padding-top: 0 !important;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.2rem !important;
}

/* Fila horizontal principal de la tabla */
div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla) {
    display: flex !important;
    flex-direction: row !important;
    align-items: stretch !important; 
    background-color: #1a1e29 !important;
    border: 1px solid #353b4d !important;
    width: 100% !important;
    box-sizing: border-box !important;
    margin: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(.es-encabezado) {
    background-color: #222634 !important;
}

/* Proporciones: Tabla izquierda (88%), Botón derecha (12%) */
div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla) > div[data-testid="column"]:first-child {
    flex: 1 1 auto !important;
    width: 88% !important;
    min-width: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla) > div[data-testid="column"]:last-child {
    flex: 0 0 12% !important;
    width: 12% !important;
    display: flex !important; 
    align-items: center !important; 
    justify-content: center !important;
    border-left: 1px solid #353b4d !important;
}

/* Estructura interna de la tabla */
.contenedor-tabla {
    display: grid !important;
    grid-template-columns: 8% 16% 16% 16% 16% 28% !important;
    width: 100% !important;
    align-items: center !important;
    box-sizing: border-box !important;
    margin: 0 !important;
}

.es-encabezado { font-weight: 700 !important; color: #a3adc2 !important; font-size: 0.65rem !important; }
.es-datos { color: #ffffff !important; font-size: 0.85rem !important; }

.contenedor-tabla > div {
    border-right: 1px solid #353b4d !important;
    padding: 6px 8px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.contenedor-tabla > div:last-child { border-right: none !important; }

div[data-testid="stMarkdownContainer"]:has(.contenedor-tabla) p { 
    margin: 0 !important; 
    padding: 0 !important; 
    line-height: 1.2 !important; 
}

/* Botón de edición perfectamente centrado */
div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla) button {
    height: 26px !important; 
    width: 26px !important; 
    min-width: 26px !important;
    padding: 0 !important; 
    margin: auto !important;
    background-color: transparent !important; 
    border: 1px solid transparent !important;
    display: flex !important; 
    align-items: center !important; 
    justify-content: center !important;
}
div[data-testid="stHorizontalBlock"]:has(.contenedor-tabla) button:hover { border: 1px solid #a3adc2 !important; }
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
                # Columna de rol (asumimos índice 3 si existe, ej: 'admin' o 'trabajador')
                rol = r[3].strip().lower() if len(r) > 3 and r[3].strip() else "trabajador"
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
            rol = fila[3].strip().lower() if len(fila) > 3 and fila[3].strip() else "trabajador"
            
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

if not st.session_state.autenticado:
    st.title("🔐 Acceso a APP DE HORAS")
    st.write("Por favor, ingresa tu correo electrónico y contraseña para continuar[cite: 1].")
    
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

    c_gear, _ = st.columns([2.0, 8.0])
    with c_gear:
        with st.popover("⚙️"):
            st.markdown(f"**👤 {nombre_trabajador}**")
            if es_admin:
                st.markdown("🔑 *Rol: Administrador*")
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
                st.session_state.rol_usuario = "trabajador"
                st.session_state.cambiando_password = False
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
    else:
        # Selector de Vistas (Incluyendo Admin si corresponde)
        if "vista_actual" not in st.session_state:
            st.session_state["vista_actual"] = "SEPTIEMBRE"

        vistas_disponibles = ["📅 SEPTIEMBRE", "📊 RESUMEN"]
        if es_admin:
            vistas_disponibles.append("🛠️ ADMIN")

        # Pestañas de navegación superiores
        cols_nav = st.columns(len(vistas_disponibles))
        for i, v_nombre in enumerate(vistas_disponibles):
            v_key = "SEPTIEMBRE" if "SEPTIEMBRE" in v_nombre else ("RESUMEN" if "RESUMEN" in v_nombre else "ADMIN")
            activo = st.session_state["vista_actual"] == v_key
            bg_col = "#ff4b4b" if activo else "#1a1e29"
            border_col = "#ff4b4b" if activo else "#2e3547"
            
            with cols_nav[i]:
                if st.button(v_nombre, use_container_width=True, key=f"nav_{v_key}"):
                    st.session_state["vista_actual"] = v_key
                    st.rerun()

        st.markdown("---")

        # --- GESTIÓN DE PERÍODOS Y FECHAS ---
        if "admin_inicio" not in st.session_state:
            st.session_state["admin_inicio"] = date(2026, 8, 31)
        if "admin_fin" not in st.session_state:
            st.session_state["admin_fin"] = date(2026, 9, 30)

        inicio_mes = st.session_state["admin_inicio"]
        fin_mes = st.session_state["admin_fin"]
        delta_dias = (fin_mes - inicio_mes).days + 1
        fechas_periodo = [inicio_mes + timedelta(days=i) for i in range(delta_dias)]

        # --- VISTA 1: REGISTRO DIARIO (SEPTIEMBRE) ---
        if st.session_state["vista_actual"] == "SEPTIEMBRE":
            st.subheader("REGISTRO DIARIO")
            
            if "filas_planilla" not in st.session_state:
                try:
                    st.session_state["filas_planilla"] = hoja_usuario.get("A2:G32")
                except Exception:
                    st.session_state["filas_planilla"] = []

            filas_planilla = st.session_state["filas_planilla"]
            dict_por_dia = {}
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

            val_hn_str = minutos_a_hora_str(total_hn)
            val_hr_str = minutos_a_hora_str(total_hr)
            
            st.markdown(f'''
            <div style="display: flex; gap: 10px; width: 100%; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px;">Total Horas Extras</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff;">{val_hn_str}</div>
                </div>
                <div style="flex: 1; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px;">Total Horas Recargo</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff;">{val_hr_str}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown("---")

            dias_pendientes = [f for f in fechas_periodo if not (dict_por_dia.get(f.day, {}).get("entrada") or dict_por_dia.get(f.day, {}).get("obra"))]

            if not dias_pendientes:
                st.success("🎉 ¡Todos los días del periodo ya han sido completados!")
            else:
                for f in dias_pendientes:
                    nom_dia = DIAS_MAP[f.weekday()]
                    num_dia = f.day
                    fecha_iso = f.strftime("%Y-%m-%d")
                    es_festivo = fecha_iso in FERIADOS
                    dia_base = f"{nom_dia} | {num_dia:02d}"
                    label = f"⚪ {dia_base}{' (FERIADO)' if es_festivo else ''}"

                    with st.expander(label):
                        with st.form(key=f"form_dia_{num_dia}"):
                            c_ent, c_sal = st.columns(2)
                            with c_ent:
                                inp_ent = st.time_input("Entrada", value=None, key=f"e_{num_dia}")
                            with c_sal:
                                inp_sal = st.time_input("Salida", value=None, key=f"s_{num_dia}")
                            inp_ob = st.selectbox("Obra", options=lista_obras, index=None, placeholder="Seleccionar...", key=f"o_{num_dia}")
                            
                            if st.form_submit_button("💾 Guardar Registro", use_container_width=True):
                                es_especial = inp_ob and inp_ob.strip().upper() in ["PERMISO", "NO TRABAJA"]
                                if not inp_ob:
                                    st.warning("⚠️ Debes seleccionar una Obra.")
                                elif not es_especial and (inp_ent is None or inp_sal is None):
                                    st.warning("⚠️ Debes ingresar Entrada y Salida.")
                                else:
                                    fila_n = fila_segun_dia(num_dia)
                                    if es_especial:
                                        hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["-", "-"]], value_input_option="RAW")
                                        hoja_usuario.update(f"G{fila_n}", [[inp_ob]], value_input_option="RAW")
                                    else:
                                        hoja_usuario.update(f"C{fila_n}:D{fila_n}", [[inp_ent.strftime("%H:%M"), inp_sal.strftime("%H:%M")]], value_input_option="USER_ENTERED")
                                        hoja_usuario.update(f"G{fila_n}", [[inp_ob]], value_input_option="USER_ENTERED")
                                    
                                    if "filas_planilla" in st.session_state:
                                        del st.session_state["filas_planilla"]
                                    st.session_state["vista_actual"] = "RESUMEN"
                                    st.rerun()

        # --- VISTA 2: RESUMEN MENSUAL Y EXPORTAR PDF ---
        elif st.session_state["vista_actual"] == "RESUMEN":
            st.subheader("RESUMEN MENSUAL")
            
            if "filas_planilla" not in st.session_state:
                try:
                    st.session_state["filas_planilla"] = hoja_usuario.get("A2:G32")
                except Exception:
                    st.session_state["filas_planilla"] = []

            registros_tabla = []
            total_hn, total_hr = 0, 0
            dict_por_dia = {}
            for idx, r in enumerate(st.session_state["filas_planilla"]):
                num_dia = int(r[1]) if len(r) > 1 and r[1].isdigit() else (idx + 1)
                e, s, hn, hr, ob = (r[2] if len(r)>2 else ""), (r[3] if len(r)>3 else ""), (r[4] if len(r)>4 else ""), (r[5] if len(r)>5 else ""), (r[6] if len(r)>6 else "")
                dict_por_dia[num_dia] = {"entrada": e, "salida": s, "hn": hn, "hr": hr, "obra": ob}
                
                def a_minutos(txt):
                    if not txt: return 0
                    t = str(txt).strip()
                    if ":" in t:
                        p = t.split(":")
                        return int(float(p[0])) * 60 + int(float(p[1]))
                    return int(round(float(t.replace(",", ".")) * 60))
                try: total_hn += a_minutos(hn)
                except: pass
                try: total_hr += a_minutos(hr)
                except: pass

                if e or s or ob:
                    registros_tabla.append({"DÍA": num_dia, "ENTRADA": e, "SALIDA": s, "HORA EXTRA": hn, "HORA RECARGO": hr, "OBRA": ob})

            st.markdown(f'''
            <div style="display: flex; gap: 10px; width: 100%; margin-bottom: 1rem;">
                <div style="flex: 1; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px;">Total Horas Extras</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff;">{minutos_a_hora_str(total_hn)}</div>
                </div>
                <div style="flex: 1; background-color: #0e1117; border: 1px solid #262d3d; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.68rem; color: #838c9e; margin-bottom: 4px;">Total Horas Recargo</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #ffffff;">{minutos_a_hora_str(total_hr)}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # Botón de exportación a PDF (Base estructurada)
            if st.button("📄 Descargar Reporte en PDF"):
                st.info("ℹ️ Módulo de PDF listo para ser conectado con ReportLab/FPDF en la siguiente fase de pulido.")

            st.markdown("---")

            if "dia_en_edicion" not in st.session_state:
                st.session_state["dia_en_edicion"] = None

            if registros_tabla:
                c_h1, c_h2 = st.columns([0.88, 0.12], vertical_alignment="center")
                with c_h1:
                    st.markdown('''
                    <div class="contenedor-tabla es-encabezado">
                        <div class="col-dia">DÍA</div>
                        <div class="col-ent">ENTRADA</div>
                        <div class="col-sal">SALIDA</div>
                        <div class="col-hn">H.NORMAL</div>
                        <div class="col-hr">H.RECARGO</div>
                        <div class="col-ob">OBRA</div>
                    </div>
                    ''', unsafe_allow_html=True)

                for r in registros_tabla:
                    d = r["DÍA"]
                    c_dat, c_b = st.columns([0.88, 0.12], vertical_alignment="center")
                    with c_dat:
                        st.markdown(f'''
                        <div class="contenedor-tabla es-datos">
                            <div class="col-dia">{d}</div>
                            <div class="col-ent">{r["ENTRADA"]}</div>
                            <div class="col-sal">{r["SALIDA"]}</div>
                            <div class="col-hn">{r["HORA EXTRA"] or "&nbsp;"}</div>
                            <div class="col-hr">{r["HORA RECARGO"] or "&nbsp;"}</div>
                            <div class="col-ob">{r["OBRA"]}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    with c_b:
                        if st.button("✏️", key=f"btn_edit_{d}"):
                            st.session_state["dia_en_edicion"] = None if st.session_state.get("dia_en_edicion") == d else d
                            st.rerun()

                    if st.session_state.get("dia_en_edicion") == d:
                        datos_d = dict_por_dia.get(d, {})
                        with st.form(key=f"form_inline_dia_{d}"):
                            c1e, c2e = st.columns(2)
                            with c1e:
                                edit_ent = st.time_input("Entrada", value=str_a_time(datos_d.get("entrada")), key=f"re_{d}")
                            with c2e:
                                edit_sal = st.time_input("Salida", value=str_a_time(datos_d.get("salida")), key=f"rs_{d}")
                            edit_ob = st.selectbox("Obra", options=lista_obras, index=lista_obras.index(datos_d.get("obra")) if datos_d.get("obra") in lista_obras else 0, key=f"ro_{d}")
                            
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.form_submit_button("💾 Guardar", use_container_width=True):
                                    fila_n = fila_segun_dia(d)
                                    es_esp = edit_ob.upper() in ["PERMISO", "NO TRABAJA"]
                                    if es_esp:
                                        hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["-", "-"]], value_input_option="RAW")
                                        hoja_usuario.update(f"G{fila_n}", [[edit_ob]], value_input_option="RAW")
                                    else:
                                        hoja_usuario.update(f"C{fila_n}:D{fila_n}", [[edit_ent.strftime("%H:%M"), edit_sal.strftime("%H:%M")]], value_input_option="USER_ENTERED")
                                        hoja_usuario.update(f"G{fila_n}", [[edit_ob]], value_input_option="USER_ENTERED")
                                    if "filas_planilla" in st.session_state: del st.session_state["filas_planilla"]
                                    st.session_state["dia_en_edicion"] = None
                                    st.rerun()
                            with b2:
                                if st.form_submit_button("🧹 Limpiar", use_container_width=True):
                                    fila_n = fila_segun_dia(d)
                                    hoja_usuario.update(f"C{fila_n}:D{fila_n}", [["", ""]], value_input_option="USER_ENTERED")
                                    hoja_usuario.update(f"G{fila_n}", [[""]], value_input_option="USER_ENTERED")
                                    if "filas_planilla" in st.session_state: del st.session_state["filas_planilla"]
                                    st.session_state["dia_en_edicion"] = None
                                    st.rerun()
            else:
                st.info("Aún no tienes jornadas registradas.")

        # --- VISTA 3: MODO ADMINISTRADOR ---
        elif st.session_state["vista_actual"] == "ADMIN" and es_admin:
            st.subheader("🛠️ PANEL DE ADMINISTRADOR")
            st.write("Control global de personal y selector de ciclos mensuales.")
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                nuevo_inicio = st.date_input("Fecha Inicio de Ciclo", value=st.session_state["admin_inicio"])
            with c_f2:
                nuevo_fin = st.date_input("Fecha Término de Ciclo", value=st.session_state["admin_fin"])
            
            if nuevo_inicio != st.session_state["admin_inicio"] or nuevo_fin != st.session_state["admin_fin"]:
                st.session_state["admin_inicio"] = nuevo_inicio
                st.session_state["admin_fin"] = nuevo_fin
                st.success("✔ Período actualizado correctamente.")

            st.markdown("---")
            st.write("### 👥 Listado General de Trabajadores")
            
            # Mostrar tabla global de todos los trabajadores registrados
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