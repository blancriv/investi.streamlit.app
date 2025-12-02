
import streamlit as st
import pandas as pd
import altair as alt
import networkx as nx
import matplotlib.pyplot as plt
import re

# ================================
# CONFIGURACIÓN GENERAL
# ================================
st.set_page_config(
    page_title='InvestiData v3.1 – Análisis Forense Digital',
    page_icon='🔍',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ================================
# ESTILOS CSS (Modo Oscuro)
# ================================
st.markdown("""
<style>
body {background-color: #121212; color: #fff;}
.main-header {font-size: 2.5rem; color: #4fc3f7; font-weight: 700; margin-bottom: 20px;}
.sub-header {font-size: 1.5rem; color: #fff; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #4fc3f7; padding-bottom: 5px;}
.metric-card {background-color: #1e1e1e; border-left: 5px solid #4fc3f7; border-radius: 5px; padding: 15px; text-align: center;}
.metric-title {color: #ccc; font-size: 1rem; font-weight: 600; margin-bottom: 5px;}
.metric-value {color: #4fc3f7; font-size: 2rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ================================
# PALABRAS CLAVE ALERTAS
# ================================
KEYWORDS_ALERTS = {
    'Drogas / Sustancias': ['droga', 'cocaina', 'marihuana', 'pasto', 'blanca', 'cristal', 'tusi', 'pepa', 'keta', 'gramo'],
    'Armas / Violencia': ['arma', 'pistola', 'fierro', 'bala', 'municion', 'calibre', 'cañon', 'muerto', 'matar', 'plomo'],
    'Delitos Graves': ['secuestro', 'extorsion', 'plata', 'niña', 'menor', 'pago', 'rescate', 'vuelta']
}

# ================================
# FUNCIONES AUXILIARES
# ================================
@st.cache_resource
def load_excel(file):
    return pd.ExcelFile(file, engine='openpyxl')

@st.cache_data(show_spinner=False)
def load_sheet(xls, sheet_name):
    return xls.parse(sheet_name)

def normalize_sheet_names(sheet_names):
    mapping = {}
    sheet_names_lower = {s.lower(): s for s in sheet_names}
    keywords = {
        'device': ['device', 'dispositivo', 'resumen', 'summary', 'info'],
        'calls': ['call', 'llama', 'voice'],
        'messages': ['message', 'mensaje', 'sms', 'chat', 'whatsapp'],
        'contacts': ['contact', 'agenda'],
        'locations': ['location', 'ubicac', 'gps'],
        'web': ['web', 'historial', 'browser'],
        'apps': ['app', 'aplicacion', 'installed'],
        'accounts': ['cuenta', 'account', 'perfil', 'usuario']
    }
    for category, keys in keywords.items():
        for key in keys:
            match = next((real_name for s_low, real_name in sheet_names_lower.items() if key in s_low), None)
            if match:
                mapping[category] = match
                break
    return mapping

def extract_device_info(df):
    text_data = ' '.join(df.astype(str).values.flatten())
    imei_match = re.search(r'\d{15}', text_data)
    imei = imei_match.group(0) if imei_match else 'No disponible'
    brand_match = re.search(r'(Marca|Brand):\s*(\w+)', text_data, re.IGNORECASE)
    brand = brand_match.group(2) if brand_match else 'No disponible'
    model_match = re.search(r'(Modelo|Model):\s*(\w+)', text_data, re.IGNORECASE)
    model = model_match.group(2) if model_match else 'No disponible'
    return imei, brand, model

def extract_accounts_info(df):
    accounts = []
    for _, row in df.iterrows():
        row_text = ' '.join(row.astype(str))
        email_match = re.findall(r'[\w.-]+@[\w.-]+\.[a-z]{2,}', row_text)
        user_match = re.findall(r'(usuario|user|id):\s*(\w+)', row_text, re.IGNORECASE)
        platform_match = re.findall(r'(facebook|instagram|twitter|tiktok)', row_text, re.IGNORECASE)
        if email_match or user_match or platform_match:
            accounts.append({'Correo': ', '.join(email_match), 'Usuario': ', '.join([u[1] for u in user_match]), 'Plataforma': ', '.join(platform_match)})
    return accounts

# ================================
# DASHBOARD PRINCIPAL
# ================================
def view_dashboard(xls, mapping):
    st.markdown('<div class="main-header">📊 Dashboard General - InvestiData v3.1</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    metrics_config = [
        ('Dispositivo', mapping.get('device'), '📱'),
        ('Llamadas', mapping.get('calls'), '📞'),
        ('Mensajes', mapping.get('messages'), '💬'),
        ('Contactos', mapping.get('contacts'), '📇')
    ]
    for i, (label, sheet, icon) in enumerate(metrics_config):
        count = 'N/A'
        if sheet:
            try:
                df = load_sheet(xls, sheet)
                count = f"{len(df):,}"
            except:
                pass
        with cols[i]:
            st.markdown(f"""<div class='metric-card'><div class='metric-title'>{icon} {label}</div><div class='metric-value'>{count}</div></div>""", unsafe_allow_html=True)

    st.markdown('---')
    st.markdown('<div class="sub-header">📱 Perfil del Dispositivo</div>', unsafe_allow_html=True)
    if mapping.get('device'):
        df_dev = load_sheet(xls, mapping['device'])
        imei, brand, model = extract_device_info(df_dev)
        st.write(f"IMEI: {imei}")
        st.write(f"Marca: {brand}")
        st.write(f"Modelo: {model}")
    else:
        st.info('No se encontró hoja de dispositivo.')

    st.markdown('<div class="sub-header">👤 Cuentas Asociadas</div>', unsafe_allow_html=True)
    if mapping.get('accounts'):
        df_acc = load_sheet(xls, mapping['accounts'])
        accounts = extract_accounts_info(df_acc)
        if accounts:
            st.table(pd.DataFrame(accounts))
        else:
            st.info('No se detectaron cuentas asociadas.')
    else:
        st.info('No se encontró hoja de cuentas/perfiles.')

# ================================
# INTERFAZ PRINCIPAL
# ================================
st.markdown('<div class="main-header">Bienvenido a InvestiData v3.1</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader('📂 Cargar archivo UFED (.xlsx)', type=['xlsx'])
if uploaded_file:
    xls = load_excel(uploaded_file)
    mapping = normalize_sheet_names(xls.sheet_names)
    view_dashboard(xls, mapping)
