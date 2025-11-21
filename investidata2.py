import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import re

# -----------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------------------------------------
st.set_page_config(
    page_title="InvestiData - Análisis Forense",
    layout="wide"
)
# ============================================================
#                   ESTILO PERSONALIZADO
# ============================================================
st.markdown("""
<style>

    /* Bordes suaves de las tarjetas */
    .metric-container {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 10px;
        background: #FAFAFA;
    }

    /* Quitar el fondo feo del sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F5F7FF;
    }

    /* Títulos más lindos */
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }

</style>
""", unsafe_allow_html=True)

DEFAULT_FILE = "/mnt/data/202500019_2025-06-26_Informe.xlsx"

# -----------------------------------------------------------
# TÍTULO
# -----------------------------------------------------------
st.title("📊 InvestiData – Analítica de Extracciones Forenses")
st.write("Mapas, palabras clave, nombres propios, grafo de contactos y más.")

# -----------------------------------------------------------
# SUBIR ARCHIVO
# -----------------------------------------------------------
uploaded_file = st.file_uploader("📂 Cargar archivo XLSX", type=["xlsx"])
use_default = st.checkbox("Usar archivo integrado (si no subo archivo)", value=False)

# -----------------------------------------------------------
# PERFIL DEL DISPOSITIVO — LADO DERECHO
# -----------------------------------------------------------
col_left, col_right = st.columns([3, 1])

with col_right:
    st.markdown("### 🟦 Perfil del Dispositivo")
    st.markdown(
        """
        <div style="font-size: 13px; line-height: 1.3; padding: 8px;
                    border: 1px solid #2980b9; border-radius: 8px;">
        📱 <b>Moto G24 – Motorola</b><br>
        📧 <b>herreragus1976@gmail.com</b><br>
        💬 <b>+57 311 252 8641 – “Calvin Klein”</b><br>
        🔢 <b>IMEI:</b><br>
        &nbsp;&nbsp;• 354102943867594<br>
        &nbsp;&nbsp;• 354102943902490<br>
        🎨 <b>Color:</b> Gris<br>
        🧩 <b>SIM:</b> 1 encontrada<br>
        🛠 <b>Estado:</b> Bueno<br>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------------------------------
# LEER ARCHIVO
# -----------------------------------------------------------
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        st.success("✔ Archivo cargado correctamente.")
    except:
        st.error("❌ No se pudo leer el archivo subido.")
        st.stop()

elif use_default:
    try:
        xls = pd.ExcelFile(DEFAULT_FILE)
        st.success(f"✔ Archivo por defecto cargado: {DEFAULT_FILE}")
    except:
        st.error("❌ No se pudo leer el archivo por defecto.")
        st.stop()

else:
    st.info("Sube un archivo o activa 'Usar archivo integrado'.")
    st.stop()

# -----------------------------------------------------------
# SELECCIÓN DE HOJA
# -----------------------------------------------------------
hoja = st.selectbox("📑 Selecciona la hoja a analizar", xls.sheet_names)
df = xls.parse(hoja)

st.markdown("### 👀 Vista previa")
st.dataframe(df.head())

# Normalizar columnas
df.columns = [c.strip() for c in df.columns]
df.columns = [c.lower() for c in df.columns]

# ============================================================
#           🟦 TABLERO GENERAL – INVESTIDATA
# ============================================================
import altair as alt

st.markdown("## 📊 Tablero General de Análisis")

# Crear columnas para tarjetas tipo KPI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# KPI 1 → Total registros
kpi1.metric(
    label="📁 Total de registros",
    value=f"{len(df):,}"
)

# KPI 2 → Total números detectados
all_text_tab = " ".join(df.astype(str).values.flatten())
numbers_tab = re.findall(r"\b(?:\+?\d{7,15}|\d{7,15})\b", all_text_tab)
kpi2.metric(
    label="📞 Total números detectados",
    value=len(numbers_tab)
)

# KPI 3 → Palabra más frecuente
words = re.findall(r"\b[a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,}\b", all_text_tab.lower())
word_counts = Counter(words)
top_word, freq_word = word_counts.most_common(1)[0]
kpi3.metric(
    label="🔠 Palabra más repetida",
    value=top_word,
    delta=f"{freq_word} veces"
)

# KPI 4 → Fecha más activa
if "fecha" in df.columns:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    fecha_counts = df["fecha"].value_counts().sort_values(ascending=False)
    if not fecha_counts.empty:
        kpi4.metric(
            label="📅 Fecha con más actividad",
            value=str(fecha_counts.index[0].date()),
            delta=f"{fecha_counts.iloc[0]} registros"
        )
else:
    kpi4.metric("📅 Fecha activa", "No disponible")

# ============================================================
# GRÁFICOS ALTOS CALIDAD – AUTOMÁTICOS
# ============================================================

st.markdown("### 📈 Actividad por fechas")
if "fecha" in df.columns:
    chart_fecha = alt.Chart(df.dropna(subset=["fecha"])).mark_line().encode(
        x='fecha:T',
        y='count()',
        tooltip=['fecha:T', 'count()']
    ).properties(
        width='container',
        height=250
    )
    st.altair_chart(chart_fecha, use_container_width=True)
else:
    st.info("No existen datos de fecha para graficar actividad temporal.")

# ============================================================

st.markdown("### 🔢 Números más mencionados")
df_nums = pd.DataFrame(Counter(numbers_tab).most_common(15), columns=["Número", "Frecuencia"])

chart_nums = alt.Chart(df_nums).mark_bar().encode(
    x='Número:N',
    y='Frecuencia:Q',
    tooltip=['Número', 'Frecuencia']
).properties(
    width='container',
    height=250
)

st.altair_chart(chart_nums, use_container_width=True)

# ============================================================

st.markdown("### 🔡 Palabras más frecuentes")
df_words = pd.DataFrame(word_counts.most_common(20), columns=["Palabra", "Frecuencia"])

chart_words = alt.Chart(df_words).mark_bar().encode(
    x='Palabra:N',
    y='Frecuencia:Q',
    tooltip=['Palabra', 'Frecuencia']
).properties(
    width='container',
    height=250
)

st.altair_chart(chart_words, use_container_width=True)

# -----------------------------------------------------------
# FILTROS RÁPIDOS
# -----------------------------------------------------------
st.markdown("### 🎯 Filtros rápidos")
c1, c2, c3, c4 = st.columns(4)

with c1:
    keyword = st.text_input("🔍 Palabra clave")

with c2:
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        min_f = df["fecha"].min()
        max_f = df["fecha"].max()
        fecha_inicio = st.date_input("📅 Desde", min_f)
    else:
        fecha_inicio = None

with c3:
    if "fecha" in df.columns:
        fecha_fin = st.date_input("📅 Hasta", max_f)
    else:
        fecha_fin = None

with c4:
    contact_filter = st.text_input("👤 Contacto / Número")

df_filtered = df.copy()

if keyword:
    df_filtered = df_filtered[df_filtered.astype(str).apply(
        lambda row: row.str.contains(keyword, case=False).any(), axis=1)]

if "fecha" in df_filtered.columns and fecha_inicio and fecha_fin:
    df_filtered = df_filtered[
        (df_filtered["fecha"] >= pd.to_datetime(fecha_inicio)) &
        (df_filtered["fecha"] <= pd.to_datetime(fecha_fin))
    ]

if contact_filter:
    df_filtered = df_filtered[df_filtered.astype(str).apply(
        lambda row: row.str.contains(contact_filter, case=False).any(), axis=1)]

st.markdown("### 📋 Resultados filtrados (primeros 200 registros)")
st.dataframe(df_filtered.head(200))

# -----------------------------------------------------------
# DETECCIÓN DE NOMBRES PROPIOS
# -----------------------------------------------------------
st.markdown("### 🧾 Nombres propios detectados")
text_columns = [c for c in df_filtered.columns if df_filtered[c].dtype == object]
combined_text = " ".join(df_filtered[text_columns].astype(str).values.flatten())

tokens = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b", combined_text)
top_names = Counter(tokens).most_common(20)

st.write(pd.DataFrame(top_names, columns=["Nombre", "Frecuencia"]))

# -----------------------------------------------------------
# PALABRAS SOSPECHOSAS
# -----------------------------------------------------------
st.markdown("### 🚨 Detección de patrones sospechosos")
keywords = [
    "arma", "pistola", "revólver", "droga", "matar",
    "niña", "extorsión", "vacuna", "pagar", "amenaza"
]
patron = "|".join(keywords)

df_sos = df_filtered[df_filtered.astype(str).apply(
    lambda row: row.str.contains(patron, case=False).any(), axis=1)]

st.write(f"Registros sospechosos encontrados: {len(df_sos)}")
st.dataframe(df_sos.head(200))

# -----------------------------------------------------------
# DETECCIÓN DE NÚMEROS FRECUENTES
# -----------------------------------------------------------
st.markdown("### 🔢 Números detectados más comunes")
all_text = " ".join(df_filtered.astype(str).values.flatten())
numbers = re.findall(r"\b(?:\+?\d{7,15}|\d{7,15})\b", all_text)
num_counts = Counter(numbers).most_common(10)
st.write(pd.DataFrame(num_counts, columns=["Número", "Frecuencia"]))

# -----------------------------------------------------------
# MAPA DE UBICACIONES
# -----------------------------------------------------------
st.markdown("### 🗺️ Mapa de ubicaciones")
lat_cols = [c for c in df_filtered.columns if "lat" in c]
lon_cols = [c for c in df_filtered.columns if "lon" in c or "long" in c]

if lat_cols and lon_cols:
    map_df = df_filtered[[lat_cols[0], lon_cols[0]]].dropna()
    map_df.columns = ["lat", "lon"]
    try:
        map_df["lat"] = map_df["lat"].astype(float)
        map_df["lon"] = map_df["lon"].astype(float)
        st.map(map_df)
    except:
        st.info("Las coordenadas no están en formato numérico.")
else:
    st.info("No se detectaron columnas de latitud/longitud.")

# -----------------------------------------------------------
# GRAFO DE CONTACTOS
# -----------------------------------------------------------
st.markdown("### 🔗 Grafo de contactos")

sender_cols = [c for c in df_filtered.columns if "remit" in c]
receiver_cols = [c for c in df_filtered.columns if "recept" in c or "receptor" in c]

if sender_cols and receiver_cols:
    s = sender_cols[0]
    r = receiver_cols[0]
    edges = df_filtered[[s, r]].dropna().astype(str).values.tolist()

    G = nx.DiGraph()
    G.add_edges_from(edges)

    fig, ax = plt.subplots(figsize=(7, 5))
    pos = nx.spring_layout(G, k=0.5)
    nx.draw(G, pos, node_size=20, alpha=0.6, ax=ax, with_labels=False)
    ax.set_title("Grafo de contactos")
    st.pyplot(fig)
else:
    st.info("No se detectaron columnas de remitente/receptor.")

# -----------------------------------------------------------
# DESCARGA CSV
# -----------------------------------------------------------
st.download_button(
    "⬇️ Descargar CSV filtrado",
    df_filtered.to_csv(index=False).encode("utf-8"),
    "investidata_filtrado.csv",
    mime="text/csv"
)

st.success("Análisis completado ✔️")
