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

/* --- FORZAR TAMAÑO COMPACTO GLOBAL DE BOTONES --- */
div.stButton > button {
    height: 28px !important;
    min-height: 28px !important;
    max-height: 28px !important;
    width: 32px !important;
    min-width: 32px !important;
    max-width: 32px !important;
    padding: 0px !important;
    margin: 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
div.stButton > button p {
    font-size: 12px !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div.stButton {
    min-height: 0px !important;
    height: auto !important;
}


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

div[data-testid="stAppViewBlockContainer"] { transition: none !important; }
div[data-testid="stAppViewContainer"] > .main { opacity: 1 !important; }

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

/* Ocultar únicamente la flecha del primer selectbox (engranaje) y hacerlo compacto */
div.block-container > div:first-child div[data-testid="stSelectbox"] [data-baseweb="select"] svg,
div[data-testid="stVerticalBlock"] > div:first-child div[data-testid="stSelectbox"] [data-baseweb="select"] svg {
    display: none !important;
}
div.block-container > div:first-child div[data-testid="stSelectbox"],
div[data-testid="stVerticalBlock"] > div:first-child div[data-testid="stSelectbox"] {
    max-width: 65px !important;
}

div[data-testid="stTimeInput"] input::-webkit-datetime-edit-hour-field:not([aria-valuenow]),
div[data-testid="stTimeInput"] input::-webkit-datetime-edit-minute-field:not([aria-valuenow]),
div[data-testid="stTimeInput"] input::-webkit-datetime-edit-text { color: transparent !important; }
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-hour-field,
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-minute-field,
div[data-testid="stTimeInput"] input:focus::-webkit-datetime-edit-text { color: #FFFFFF !important; }

div[data-testid="stForm"] { border: none !important; padding: 0 !important; }

.tabla-resumen-header {
    display: flex;
    align-items: center;
    border-top: 1px solid #282d3c;
    border-bottom: 1px solid #282d3c;
    padding: 4px 2px;
    font-size: 0.52rem;
    font-weight: 600;
    color: #838c9e;
    letter-spacing: 0px;
    white-space: nowrap !important;
    margin-bottom: 0px !important;
    overflow: hidden;
}

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
    padding: 0 4px;
    font-size: 0.75rem;
    color: #ffffff;
    white-space: nowrap !important;
}

div[data-testid="column"]:has(button:has(p:contains("✏️"))) {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
}

button:has(p:contains("✏️")) {
    height: 22px !important;
    min-height: 22px !important;
    width: 26px !important;
    padding: 0 !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 4px !important;
    margin: 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
button:has(p:contains("✏️")) div[data-testid="stMarkdownContainer"] p {
    font-size: 11px !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
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

/* Fijar el tamaño y diseño del botón de engranaje para que el zoom no lo deforme */
div[data-testid="stSelectbox"]:has(input[aria-label="⚙️"]), 
div[data-testid="stSelectbox"]:has(div[aria-label="⚙️"]) {
    width: 60px !important;
    min-width: 60px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 6px !important;
}

div[data-testid="stSelectbox"]:has(input[aria-label="⚙️"]), 
div[data-testid="stSelectbox"]:has(div[aria-label="⚙️"]),
div.block-container > div:first-child div[data-testid="stSelectbox"] {
    width: 55px !important;
    max-width: 55px !important;
    min-width: 55px !important;
    height: 38px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    width: 55px !important;
    max-width: 55px !important;
    height: 38px !important;
    background-color: #1a1e29 !important;
    border: 1px solid #2e3547 !important;
    border-radius: 6px !important;
}

div[data-testid="stSelectbox"]:has(input[aria-label="⚙️"]), 
div[data-testid="stSelectbox"]:has(div[aria-label="⚙️"]) {
    min-width: 90px !important;
}

/* Forzar que los botones de Septiembre y Resumen se queden lado a lado en móviles */
div[data-testid="stHorizontalBlock"]:has(button:has(p:contains("SEPTIEMBRE"))) {
    flex-direction: row !important;
}
div[data-testid="stHorizontalBlock"]:has(button:has(p:contains("SEPTIEMBRE"))) > div[data-testid="column"] {
    width: 50% !important;
    flex: 1 1 50% !important;
    min-width: 0 !important;
}


/* Forzar que los bloques horizontales de columnas nunca se apilen en dispositivos móviles */

@media (max-width: 768px) {
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 50% !important;
        max-width: 50% !important;
        min-width: 0 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stSelectbox"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }
}

/* --- DISEÑO MÓVIL PERFECTO --- */
@media (max-width: 768px) {
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 50% !important;
        max-width: 50% !important;
        min-width: 0 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stSelectbox"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }
}

/* --- DISEÑO MÓVIL: ENTRADA, SALIDA Y OBRA --- */
@media (max-width: 768px) {
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        flex: 1 1 50% !important;
        max-width: 50% !important;
        min-width: 0 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stSelectbox"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }
}
</style>


