import json
import streamlit as st

# Carga inteligente de credenciales (Nube vs Local)
if "client_oauth" in st.secrets:
    client_secrets_dict = {
        "web": {
            "client_id": st.secrets["client_oauth"]["client_id"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": st.secrets["client_oauth"]["client_secret"],
            "javascript_origins": ["https://control-de-horas-mq9pnhrvdgerzovdyyi8zq.streamlit.app"]
        }
    }
    creds_dict = dict(st.secrets["gcp_service_account"])
else:
    with open("client_secret.json", "r", encoding="utf-8") as f:
        client_secrets_dict = json.load(f)
    with open("credenciales.json", "r", encoding="utf-8") as f:
        creds_dict = json.load(f)

import os
import json
import streamlit as st

# Generar archivos .json automáticamente desde st.secrets en la nube
if not os.path.exists("client_secret.json") and "client_oauth" in st.secrets:
    with open("client_secret.json", "w", encoding="utf-8") as f:
        json.dump({
            "web": {
                "client_id": st.secrets["client_oauth"]["client_id"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": st.secrets["client_oauth"]["client_secret"],
                "javascript_origins": ["https://control-de-horas-mq9pnhrvdgerzovdyyi8zq.streamlit.app"]
            }
        }, f)

if not os.path.exists("credenciales.json") and "gcp_service_account" in st.secrets:
    with open("credenciales.json", "w", encoding="utf-8") as f:
        json.dump(dict(st.secrets["gcp_service_account"]), f)

import base64
from datetime import date, datetime, time, timedelta
import hashlib
import hmac
import json
import time as time_lib
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Control de Horas",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""<style>
/* 1. Ocultar barra superior de Streamlit y menus */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
footer { visibility: hidden !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* 2. Margenes y contenedor */
.block-container {
    max-width: 95% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-top: 2.2rem !important;
    padding-bottom: 3rem !important;
}

div[data-testid="stAppViewBlockContainer"] { transition: none !important; }
div[data-testid="stAppViewContainer"] > .main { opacity: 1 !important; }

/* 3. Desplegables de Septiembre */
div[data-testid="stExpander"] { width: 100% !important; }
div[data-testid="stExpander"] summary { width: 100% !important; }
div[data-testid="stExpander"] summary p {
    font-family: 'Consolas', 'Courier New', monospace !important;
    font-size: 1.12rem !important;
    font-weight: 500 !important;
    color: #FFFFFF !important;
    white-space: pre !important;
    width: 100% !important;
}
div[data-testid="stExpander"] summary svg { width: 1.2rem !important; height: 1.2rem !important; }

/* 4. Inputs de tiempo limpios */
div[data-testid="stTimeInput"] input::-webkit-datetime-edit-hour-field:not([aria-valuenow]),
div[data-testid="stTimeInput"] input::-webkit-datetime-edit-minute-field:not([aria-valuenow]),
div[data-testid="stTimeInput"] input::-webkit-datetime-edit-text { color: transparent !important; }
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-hour-field,
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-minute-field,
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-text { color: #FFFFFF !important; }

div[data-testid="stForm"] { border: none !important; padding: 0 !important; }

/* 5. Estructura de Tabla Ultra Compacta (sin separaciones excesivas) */
.tabla-resumen-header {
    display: flex;
    align-items: center;
    border-top: 1px solid #282d3c;
    border-bottom: 1px solid #282d3c;
    padding: 6px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #838c9e;
    letter-spacing: 0.3px;
    white-space: nowrap !important;
    margin-bottom: 0px !important;
}

/* Reduccion estricta de la altura vertical de cada fila */
div[data-testid="stVerticalBlock"]:has(> div > div[data-testid="element-container"] .fila-tabla-contenido),
div[data-testid="stVerticalBlock"]:has(.fila-tabla-contenido) {
    gap: 0px !important;
}

div[data-testid="element-container"]:has(.fila-tabla-contenido) {
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.fila-tabla-contenido) {
    align-items: center !important;
    min-height: 36px !important;
    height: 36px !important;
    margin: 0 !important;
    padding: 0 !important;
    border-bottom: 1px solid #1c202a;
    gap: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.fila-tabla-contenido) div[data-testid="column"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.fila-tabla-contenido {
    display: flex;
    align-items: center;
    height: 36px;
    padding: 0 12px;
    font-size: 0.90rem;
    color: #ffffff;
    white-space: nowrap !important;
}

div[data-testid="column"]:has(button:has(p:contains("✏️"))) {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
}

/* Boton lapiz nitido */
button:has(p:contains("✏️")) {
    height: 26px !important;
    min-height: 26px !important;
    width: 32px !important;
    padding: 0 !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 6px !important;
    margin: 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

button:has(p:contains("✏️")) div[data-testid="stMarkdownContainer"] p {
    font-size: 13px !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}

button:has(p:contains("✏️")):hover {
    background-color: #262c3b !important;
    border-color: #40495f !important;
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

CLIENT_SECRETS_FILE = "client_secret.json"
try:
    with open(CLIENT_SECRETS_FILE, "r", encoding="utf-8") as f:
        datos_oauth = json.load(f)
        cfg = datos_oauth.get("web") or datos_oauth.get("installed")
        CLIENT_ID = cfg["client_id"]
        CLIENT_SECRET = cfg["client_secret"]
except Exception as e:
    st.error(f"Error al leer '{CLIENT_SECRETS_FILE}': {e}")
    st.stop()

# REDIRECT_URI dinámico para PC y Celular
try:
    host_actual = st.context.headers.get("Host", "localhost:8501")
    proto = "https" if "streamlit.app" in host_actual else "http"
    REDIRECT_URI = f"{proto}://{host_actual}"
except Exception:
    REDIRECT_URI = "http://localhost:8501"

def conectar_libro(reintentos=3):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    for intento in range(reintentos):
        try:
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
        obras = [r[1].strip() for r in filas if len(r) > 1 and r[1].strip()]
        return obras if obras else ["LOTE 1", "LOTE 4", "LOTE 11", "MONTESSORI"]
    except Exception:
        return ["LOTE 1", "LOTE 4", "LOTE 11", "MONTESSORI"]

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

query_params = st.query_params

if "session" in query_params:
    correo_token = verificar_token(query_params["session"])
    if correo_token:
        st.session_state["user_email"] = correo_token

if "editar_dia" in query_params:
    del query_params["editar_dia"]

if "code" in query_params and "user_email" not in st.session_state:
    auth_code = query_params["code"]
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(token_url, data=payload).json()

    if "access_token" in resp:
        info_resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {resp['access_token']}"}
        ).json()
        email_verificado = info_resp.get("email", "").lower().strip()
        st.session_state["user_email"] = email_verificado
        st.query_params["session"] = firmar_correo(email_verificado)
        st.rerun()

if not st.session_state.get("user_email"):
    st.markdown("### ⏱️ Iniciar Sesión")
    st.write("Accede con tu cuenta autorizada de Google:")
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    }
    login_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"
    boton_google = f'<a href="{login_url}" target="_self" style="display: block; max-width: 320px; background-color: #4285F4; color: white; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🔑 Continuar con Google</a>'
    st.markdown(boton_google, unsafe_allow_html=True)

else:
    correo_google = st.session_state["user_email"]
    usuarios_autorizados = cargar_trabajadores()
    lista_obras = cargar_obras()

    if correo_google not in usuarios_autorizados:
        st.error(f"⛔ Acceso denegado: El correo '{correo_google}' no está en la nómina de trabajadores.")
        if st.button("Intentar con otra cuenta"):
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()
    else:
        nombre_trabajador = usuarios_autorizados[correo_google]
        hoja_usuario = obtener_hoja_trabajador(nombre_trabajador)

        c_header, c_out = st.columns([5, 1], vertical_alignment="center")
        with c_header:
            st.markdown(f"### 👤 {nombre_trabajador}")
        with c_out:
            if st.button("🚪 Salir", use_container_width=True):
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

        if "vista_actual" not in st.session_state:
            st.session_state["vista_actual"] = "SEPTIEMBRE"

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("📅 SEPTIEMBRE", use_container_width=True,
                         type="primary" if st.session_state["vista_actual"] == "SEPTIEMBRE" else "secondary"):
                st.session_state["vista_actual"] = "SEPTIEMBRE"
                st.session_state["dia_en_edicion"] = None
                st.rerun()
        with btn_col2:
            if st.button("📊 RESUMEN DEL MES", use_container_width=True,
                         type="primary" if st.session_state["vista_actual"] == "RESUMEN" else "secondary"):
                st.session_state["vista_actual"] = "RESUMEN"
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
                "entrada": entrada,
                "salida": salida,
                "hn": hn_val,
                "hr": hr_val,
                "obra": obra_val
            }

            def a_minutos(txt):
                if not txt:
                    return 0
                t = str(txt).strip()
                if ":" in t:
                    p = t.split(":")
                    return int(float(p[0])) * 60 + int(float(p[1]))
                return int(round(float(t.replace(",", ".")) * 60))

            try:
                total_hn += a_minutos(hn_val)
            except Exception:
                pass
            try:
                total_hr += a_minutos(hr_val)
            except Exception:
                pass

            if entrada or salida or obra_val:
                registros_tabla.append({
                    "DÍA": num_dia,
                    "ENTRADA": entrada,
                    "SALIDA": salida,
                    "HORA EXTRA": hn_val,
                    "HORA RECARGO": hr_val,
                    "OBRA": obra_val
                })

        if st.session_state["vista_actual"] == "SEPTIEMBRE":
            st.subheader("MES DE SEPTIEMBRE 2026")
            c1, c2 = st.columns(2)
            c1.metric("Total Horas Extras (Mes)", minutos_a_hora_str(total_hn))
            c2.metric("Total Horas Recargo (Mes)", minutos_a_hora_str(total_hr))
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

                    espacio_relleno = " " * (9 - len(nom_dia))
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
                            c_ent, c_sal, c_ob = st.columns([1, 1, 2])

                            with c_ent:
                                inp_ent = st.time_input("Entrada", value=None, key=f"e_{num_dia}")
                            with c_sal:
                                inp_sal = st.time_input("Salida", value=None, key=f"s_{num_dia}")
                            with c_ob:
                                inp_ob = st.selectbox("Obra", options=lista_obras, index=None, placeholder="Seleccionar obra...", key=f"o_{num_dia}")

                            st.write("")
                            col_btn, _ = st.columns([1, 3])
                            with col_btn:
                                guardar_btn = st.form_submit_button("💾 Guardar Registro", use_container_width=True)

                            if guardar_btn:
                                if inp_ent is None or inp_sal is None or not inp_ob:
                                    st.warning("⚠️ Debes ingresar Entrada, Salida y seleccionar la Obra.")
                                else:
                                    with st.spinner("Guardando en la planilla..."):
                                        try:
                                            fila_n = fila_segun_dia(num_dia)
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
            st.subheader(f"RESUMEN MENSUAL — {nombre_trabajador}")
            m1, m2 = st.columns(2)
            m1.metric("Total Horas Extras (Mes)", minutos_a_hora_str(total_hn))
            m2.metric("Total Horas Recargo (Mes)", minutos_a_hora_str(total_hr))
            st.markdown("---")

            if "dia_en_edicion" not in st.session_state:
                st.session_state["dia_en_edicion"] = None

            if registros_tabla:
                st.markdown("""
                <div class="tabla-resumen-header">
                    <span style="width: 7%;">DÍA</span>
                    <span style="width: 12%;">ENTRADA</span>
                    <span style="width: 12%;">SALIDA</span>
                    <span style="width: 16%;">HORA EXTRA</span>
                    <span style="width: 18%;">HORA RECARGO</span>
                    <span style="width: 29%;">OBRA</span>
                    <span style="width: 6%;"></span>
                </div>
                """, unsafe_allow_html=True)

                for r in registros_tabla:
                    d = r["DÍA"]
                    c_datos, c_btn = st.columns([9.2, 0.8], vertical_alignment="center")

                    with c_datos:
                        st.markdown(f"""
                        <div class="fila-tabla-contenido">
                            <span style="width: 7.6%; font-weight: bold;">{d}</span>
                            <span style="width: 13.0%;">{r["ENTRADA"]}</span>
                            <span style="width: 13.0%;">{r["SALIDA"]}</span>
                            <span style="width: 17.4%;">{r["HORA EXTRA"]}</span>
                            <span style="width: 19.5%;">{r["HORA RECARGO"]}</span>
                            <span style="width: 29.5%;">{r["OBRA"]}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with c_btn:
                        if st.button("✏️", key=f"btn_edit_{d}"):
                            if st.session_state.get("dia_en_edicion") == d:
                                st.session_state["dia_en_edicion"] = None
                            else:
                                st.session_state["dia_en_edicion"] = d
                            st.rerun()

                    # Formulario directo bajo el dia seleccionado, sin caja ni cartel intermedio
                    if st.session_state.get("dia_en_edicion") == d:
                        datos_d = dict_por_dia.get(d, {})
                        val_e = str_a_time(datos_d.get("entrada", ""))
                        val_s = str_a_time(datos_d.get("salida", ""))
                        val_o = datos_d.get("obra", "")
                        idx_o = lista_obras.index(val_o) if val_o and val_o in lista_obras else 0

                        with st.form(key=f"form_inline_dia_{d}"):
                            c1e, c2e, c3e = st.columns([1, 1, 2])
                            with c1e:
                                edit_ent = st.time_input("Entrada", value=val_e, key=f"re_{d}")
                            with c2e:
                                edit_sal = st.time_input("Salida", value=val_s, key=f"rs_{d}")
                            with c3e:
                                edit_ob = st.selectbox("Obra", options=lista_obras, index=idx_o, key=f"ro_{d}")

                            st.write("")
                            b1, b2 = st.columns(2)
                            with b1:
                                btn_guardar_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                            with b2:
                                btn_borrar_edit = st.form_submit_button("🧹 Limpiar (volver a Septiembre)", use_container_width=True)

                            if btn_guardar_edit:
                                if edit_ent is None or edit_sal is None or not edit_ob:
                                    st.warning("⚠️ Debes completar Entrada, Salida y Obra.")
                                else:
                                    with st.spinner("Actualizando planilla..."):
                                        fila_n = fila_segun_dia(d)
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
            if st.button("📅 Volver a Septiembre", use_container_width=True):
                st.session_state["vista_actual"] = "SEPTIEMBRE"
                st.session_state["dia_en_edicion"] = None
                st.rerun()
