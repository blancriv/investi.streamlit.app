import streamlit as st
import pandas as pd
import altair as alt
import networkx as nx
import matplotlib.pyplot as plt
import re
from collections import Counter

# ================================
# CONFIGURACIÓN GENERAL
# ================================
st.set_page_config(
    page_title="InvestiData – Análisis Forense Digital",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar st.session_state para la navegación con filtros
if 'filter_pass' not in st.session_state:
    st.session_state['filter_pass'] = None

# ================================
# ESTILOS CSS PERSONALIZADOS
# ================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1a73e8;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 2px solid #1a73e8;
        padding-bottom: 5px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #1a73e8;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #666;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #1a73e8;
        font-size: 2rem;
        font-weight: bold;
    }
    /* Estilo para tablas */
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    .welcome-container {
        padding: 40px;
        border-radius: 15px;
        background: linear-gradient(135deg, #e6f3ff, #ffffff);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# DICCIONARIO DE PALABRAS CLAVE (HALLAZGOS)
# ================================
# Basado en tu documentación del proyecto
KEYWORDS_ALERTS = {
    "Drogas / Sustancias": ["droga", "cocaina", "marihuana", "pasto", "blanca", "cristal", "tusi", "pepa", "keta", "gramo"],
    "Armas / Violencia": ["arma", "pistola", "fierro", "bala", "municion", "calibre", "cañon", "muerto", "matar", "plomo"],
    "Delitos Graves": ["secuestro", "extorsion", "plata", "niña", "menor", "pago", "rescate", "vuelta"]
}

# ================================
# FUNCIONES AUXILIARES
# ================================

@st.cache_resource # <--- CAMBIO CLAVE: Usamos cache_resource para objetos ExcelFile
def load_excel(file):
    """Carga el archivo Excel en caché para optimizar rendimiento."""
    # Usar engine='openpyxl' es esencial para archivos XLSX modernos
    return pd.ExcelFile(file, engine='openpyxl') 

def normalize_sheet_names(sheet_names):
    """
    Normaliza los nombres de las hojas para detectar automáticamente 
    el contenido sin importar el idioma (Español/Inglés) o variaciones.
    """
    mapping = {}
    sheet_names_lower = {s.lower(): s for s in sheet_names}
    
    # Patrones de búsqueda para cada categoría
    keywords = {
        "device": ["device", "dispositivo", "resumen", "summary", "info", "general"],
        "calls": ["call", "llama", "voice", "voz", "registro"],
        "messages": ["message", "mensaje", "sms", "chat", "convers", "whatsapp", "telegram"],
        "contacts": ["contact", "agenda", "people", "persona", "directorio"],
        "locations": ["location", "ubicac", "gps", "map", "place", "geo"],
        "web": ["web", "historial", "history", "internet", "browser", "navegac", "busqued", "search"],
        "apps": ["app", "aplicacion", "installed", "paquete", "software"]
    }

    for category, keys in keywords.items():
        for key in keys:
            # Buscar coincidencia parcial
            match = next((real_name for s_low, real_name in sheet_names_lower.items() if key in s_low), None)
            if match:
                mapping[category] = match
                break
    
    return mapping

def find_columns(df, candidates):
    """Busca columnas en el DataFrame que coincidan con términos esperados."""
    df_cols_lower = [c.lower() for c in df.columns]
    found_cols = {}
    
    for key, search_terms in candidates.items():
        for term in search_terms:
            for i, col_lower in enumerate(df_cols_lower):
                if term in col_lower:
                    found_cols[key] = df.columns[i]
                    break
            if key in found_cols:
                break
    return found_cols

# ================================
# VISTAS DE ANÁLISIS (MÓDULOS)
# ================================

def view_dashboard(xls, mapping):
    st.markdown('<div class="main-header">📊 Dashboard General - InvestiData</div>', unsafe_allow_html=True)
    st.markdown("Resumen ejecutivo de la extracción forense.")
    
    # --- METRICAS KPI ---
    cols = st.columns(4)
    
    metrics_config = [
        ("Dispositivo", mapping.get("device"), "📱"),
        ("Llamadas", mapping.get("calls"), "📞"),
        ("Mensajes", mapping.get("messages"), "💬"),
        ("Contactos", mapping.get("contacts"), "📇")
    ]
    
    for i, (label, sheet, icon) in enumerate(metrics_config):
        count = "N/A"
        if sheet:
            try:
                # Usar solo el conteo para la métrica
                df = xls.parse(sheet, usecols=[0], skiprows=[0])
                count = f"{len(df):,}"
            except:
                pass
        
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{icon} {label}</div>
                <div class="metric-value">{count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        # --- PERFIL DEL DISPOSITIVO ---
        if mapping.get("device"):
            st.markdown('<div class="sub-header">📱 Perfil del Dispositivo</div>', unsafe_allow_html=True)
            try:
                df_dev = xls.parse(mapping.get("device"))
                # Si tiene pocas columnas y 1 fila, transponer para mejor lectura
                if len(df_dev) == 1 or len(df_dev.columns) < 5:
                    st.table(df_dev.T)
                else:
                    st.dataframe(df_dev.head(15), use_container_width=True)
            except Exception as e:
                st.error(f"Error leyendo perfil: {e}")
        else:
             st.info("Hoja de información del dispositivo no detectada automáticamente.")

    with col_right:
        # --- ALERTAS RÁPIDAS (HALLAZGOS) ---
        st.markdown('<div class="sub-header">🚨 Hallazgos Clave (Alertas)</div>', unsafe_allow_html=True)
        
        found_alerts = False
        
        if mapping.get("messages"):
            df_msg = xls.parse(mapping.get("messages"))
            # Buscar columnas de texto
            text_cols = find_columns(df_msg, {"body": ["body", "cuerpo", "text", "mensaje", "content", "contenido"]})
            
            if "body" in text_cols:
                col_target = text_cols["body"]
                df_msg[col_target] = df_msg[col_target].astype(str).fillna("")
                
                total_hits = 0
                for category, terms in KEYWORDS_ALERTS.items():
                    pattern = '|'.join(terms)
                    # Máscara booleana para encontrar coincidencias
                    mask = df_msg[col_target].str.contains(pattern, case=False, na=False)
                    count = mask.sum()
                    
                    if count > 0:
                        found_alerts = True
                        total_hits += count
                        with st.expander(f"🔴 {category}: {count} coincidencias", expanded=True):
                            st.warning(f"Se encontraron términos como: **{', '.join(terms)}**")
                            # Mostrar un pequeño extracto
                            st.dataframe(df_msg[mask][[col_target]].head(5), use_container_width=True)
                            
                            # Botón para ver la lista completa, usando session_state para forzar la navegación
                            if st.button(f"Ver todos ({category})", key=category):
                                # Almacenar la hoja y la máscara de filtro en el estado
                                st.session_state['filter_pass'] = (mapping.get("messages"), mask, category)
                                st.experimental_rerun()
                
                if not found_alerts:
                    st.success("✔ Escaneo inicial limpio: No se detectaron palabras clave de alto riesgo.")
            else:
                st.warning("No se identificó columna de texto en Mensajes para el escaneo automático.")
        else:
            st.info("No hay hoja de mensajes para escanear alertas.")

def view_messages(xls, sheet_name):
    st.markdown(f'<div class="main-header">💬 Análisis de Conversaciones y Llamadas</div>', unsafe_allow_html=True)
    st.caption(f"Fuente: {sheet_name}")
    
    df = xls.parse(sheet_name)
    
    # Mapeo de columnas críticas
    cols_map = find_columns(df, {
        "date": ["date", "fecha", "time", "hora", "timestamp"],
        "body": ["body", "text", "mensaje", "content", "contenido"],
        "from": ["from", "de", "remitente", "sender", "source", "direction", "sent"],
        "to": ["to", "para", "destinatario", "receiver"],
        "direction": ["direction", "tipo", "dir"], # Columna específica de la dirección (in/out)
        "party": ["party", "interlocutor", "contacto", "partner"] # Columna que contiene el otro extremo
    })
    
    # ------------------------------------
    # 1. ANÁLISIS GRÁFICO (Top Contactos y Dirección)
    # ------------------------------------
    st.markdown('<div class="sub-header">📊 Análisis Gráfico de Interacciones</div>', unsafe_allow_html=True)
    
    col_chart_left, col_chart_right = st.columns([1, 1])
    
    # --- Top 10 Contactos ---
    if "from" in cols_map and "to" in cols_map:
        
        # 1. Intentar identificar el "dispositivo local" como el valor más frecuente en 'from' (enviados)
        potential_device_ids = df[cols_map["from"]].value_counts()
        device_id = None
        if not potential_device_ids.empty:
            # Seleccionar el valor más común como potencial ID del dispositivo
            device_id = potential_device_ids.index[0]

        # Paso 2: Crear la columna de "Interlocutor"
        # Si el remitente es el ID del dispositivo, el interlocutor es el destinatario, y viceversa.
        df['Interlocutor'] = df.apply(
            lambda row: row[cols_map["to"]] if row[cols_map["from"]] == device_id else row[cols_map["from"]],
            axis=1
        ).astype(str).str.strip()
        
        # Limpieza: Excluir el propio ID del dispositivo y valores nulos
        df_parties = df[df['Interlocutor'] != str(device_id)]
        df_parties = df_parties[df_parties['Interlocutor'].str.lower() != 'nan']
        
        top_parties = df_parties['Interlocutor'].value_counts().nlargest(10).reset_index()
        top_parties.columns = ['Contacto', 'Frecuencia']
        
        with col_chart_left:
            st.markdown("##### 🥇 Top 10 de Interacciones por Contacto")
            if not top_parties.empty:
                chart_bar = alt.Chart(top_parties).mark_bar().encode(
                    x=alt.X('Frecuencia:Q', title='Número de Interacciones'),
                    y=alt.Y('Contacto:N', sort='-x', title='Contacto/Número'),
                    tooltip=['Contacto', 'Frecuencia'],
                    color=alt.value("#1a73e8")
                ).properties(height=300).interactive()
                st.altair_chart(chart_bar, use_container_width=True)
            else:
                st.info("No se pudo calcular el Top 10 de contactos.")

    # --- Distribución de Dirección (Enviado vs Recibido) ---
    if "direction" in cols_map:
        direction_col = cols_map["direction"]
        # Normalizar y contar las direcciones (ej: 'in', 'out', 'incoming', 'outgoing')
        df['Direction_Normalized'] = df[direction_col].astype(str).str.lower().str.replace('incoming|in|received', 'Recibido', regex=True).str.replace('outgoing|out|sent|enviado', 'Enviado', regex=True).fillna('Desconocido')
        
        direction_counts = df['Direction_Normalized'].value_counts().reset_index()
        direction_counts.columns = ['Dirección', 'Total']
        
        with col_chart_right:
            st.markdown("##### 🔄 Distribución Enviado vs. Recibido")
            if not direction_counts.empty:
                chart_pie = alt.Chart(direction_counts).mark_arc(outerRadius=120).encode(
                    theta=alt.Theta("Total", stack=True),
                    color=alt.Color("Dirección"),
                    tooltip=["Dirección", "Total", alt.Tooltip("Total", format=".1%")]
                ).properties(height=350)
                st.altair_chart(chart_pie, use_container_width=True)
            else:
                st.info("No se pudo calcular la distribución por dirección.")
    
    st.markdown("---")
    
    # ------------------------------------
    # 2. FILTROS Y TABLA DE DATOS
    # ------------------------------------
    st.markdown('<div class="sub-header">🔎 Explorador Detallado de Registros</div>', unsafe_allow_html=True)

    with st.container():
        c1, c2, c3 = st.columns([2, 1, 1])
        search_term = c1.text_input("🔍 Buscar palabra clave, nombre o número:", placeholder="Ej: droga, Juan, 3001234567")
        
        # Filtro de fecha si existe columna
        min_date, max_date = None, None
        if "date" in cols_map:
            try:
                df["fecha_dt"] = pd.to_datetime(df[cols_map["date"]], errors='coerce')
                min_val = df["fecha_dt"].min()
                max_val = df["fecha_dt"].max()
                if pd.notnull(min_val) and pd.notnull(max_val):
                    d_range = c2.date_input("📅 Rango de Fechas", [min_val, max_val])
                    if len(d_range) == 2:
                        min_date, max_date = d_range
            except:
                st.error("Error al convertir la columna de fecha. Revisar formato de la hoja.")

    # Aplicar filtros
    filtered_df = df.copy()
    
    # Filtro texto global
    if search_term:
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Filtro fecha
    if min_date and max_date and "fecha_dt" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["fecha_dt"].dt.date >= min_date) & 
            (filtered_df["fecha_dt"].dt.date <= max_date)
        ]

    st.info(f"Mostrando {len(filtered_df)} registros filtrados.")
    st.dataframe(filtered_df, use_container_width=True)
    
    # ------------------------------------
    # 3. GRÁFICA TEMPORAL
    # ------------------------------------
    if "fecha_dt" in filtered_df.columns and not filtered_df.empty:
        st.markdown('<div class="sub-header">📈 Línea de Tiempo de Actividad</div>', unsafe_allow_html=True)
        try:
            timeline = filtered_df.groupby(filtered_df["fecha_dt"].dt.date).size().reset_index(name='count')
            chart = alt.Chart(timeline).mark_bar().encode(
                x=alt.X('fecha_dt:T', title='Fecha'),
                y=alt.Y('count:Q', title='Mensajes/Registros'),
                tooltip=['fecha_dt', 'count']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error generando gráfico temporal: {e}")

def view_contacts_graph(xls, sheet_name):
    st.markdown('<div class="main-header">🕸️ Grafo de Conexiones</div>', unsafe_allow_html=True)
    st.markdown("Visualización de interacciones entre el dispositivo y terceros.")
    
    df = xls.parse(sheet_name)
    
    cols_map = find_columns(df, {
        "source": ["from", "de", "source", "remitente", "party", "number"],
        "target": ["to", "para", "dest", "destination", "recipient"]
    })
    
    # Si es hoja de contactos simple (Nombre, Numero)
    if "source" not in cols_map or "target" not in cols_map:
        # Intentar lógica de contactos: Nombre vs Número
        cols_contact = find_columns(df, {"name": ["name", "nombre"], "number": ["number", "numero", "phone", "telefono", "value"]})
        if "name" in cols_contact and "number" in cols_contact:
            st.success("Visualizando lista de Contactos (Red Estática)")
            # Simular grafo centro -> contactos
            G = nx.Graph()
            center_node = "DISPOSITIVO"
            df_sample = df.head(100) # Limite para evitar saturación
            for _, row in df_sample.iterrows():
                contact_name = str(row[cols_contact["name"]])
                G.add_edge(center_node, contact_name)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            pos = nx.spring_layout(G, k=0.15)
            nx.draw(G, pos, with_labels=True, node_size=50, node_color="#a8d5e2", edge_color="#e0e0e0", font_size=8)
            st.pyplot(fig)
            
            st.markdown('<div class="sub-header">Detalle de Contactos</div>', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            return

    # Logica para llamadas/mensajes (Origen -> Destino)
    if "source" in cols_map and "target" in cols_map:
        df_sample = df.head(300) # Limitar la muestra para el grafo
        G = nx.Graph()
        
        for _, row in df_sample.iterrows():
            src = str(row[cols_map["source"]])
            dst = str(row[cols_map["target"]])
            if src != "nan" and dst != "nan" and src != dst:
                G.add_edge(src, dst)
        
        col_graph, col_data = st.columns([2, 1])
        
        with col_graph:
            if G.number_of_nodes() > 0:
                fig, ax = plt.subplots(figsize=(8, 6))
                # Layout circular suele ser mejor para redes centralizadas
                pos = nx.spring_layout(G, k=0.2)
                nx.draw(G, pos, with_labels=False, node_size=40, node_color="#1a73e8", edge_color="gray", alpha=0.6)
                # Etiquetas inteligentes
                for node, (x, y) in pos.items():
                    if G.degree[node] > 1: # Solo mostrar nodos recurrentes
                        plt.text(x, y+0.05, s=node, fontsize=7, ha='center')
                st.pyplot(fig)
            else:
                st.warning("No hay suficientes datos para generar el grafo.")
        
        with col_data:
            st.markdown("**Top Conectados**")
            degrees = sorted(G.degree, key=lambda x: x[1], reverse=True)[:10]
            st.table(pd.DataFrame(degrees, columns=["Entidad", "Conexiones"]))

def view_locations(xls, sheet_name):
    st.markdown('<div class="main-header">📍 Mapa de Ubicaciones</div>', unsafe_allow_html=True)
    df = xls.parse(sheet_name)
    
    cols_map = find_columns(df, {
        "lat": ["lat", "latitude"],
        "lon": ["lon", "long", "longitude"],
        "time": ["time", "fecha", "date", "timestamp"]
    })
    
    if "lat" in cols_map and "lon" in cols_map:
        gps_data = df.rename(columns={cols_map["lat"]: 'lat', cols_map["lon"]: 'lon'})
        
        # Limpieza robusta
        gps_data['lat'] = pd.to_numeric(gps_data['lat'], errors='coerce')
        gps_data['lon'] = pd.to_numeric(gps_data['lon'], errors='coerce')
        gps_data = gps_data.dropna(subset=['lat', 'lon'])
        
        # Filtro de ruido (latitudes/longitudes imposibles)
        gps_data = gps_data[(gps_data['lat'] >= -90) & (gps_data['lat'] <= 90)]
        gps_data = gps_data[(gps_data['lon'] >= -180) & (gps_data['lon'] <= 180)]

        # Centrar el mapa en la primera ubicación o en un punto central
        if not gps_data.empty:
            initial_view_state = {
                'latitude': gps_data['lat'].iloc[0],
                'longitude': gps_data['lon'].iloc[0],
                'zoom': 10
            }
            st.map(gps_data[['lat', 'lon']], zoom=initial_view_state['zoom'])
        else:
            st.warning("Datos GPS válidos filtrados o insuficientes para mostrar en el mapa.")
        
        st.markdown('<div class="sub-header">Detalle de Coordenadas</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No se encontraron columnas de Latitud/Longitud claras en esta hoja.")
        st.dataframe(df.head())

def view_raw_explorer(xls, mapping):
    """Permite al usuario visualizar cualquier hoja del Excel."""
    st.markdown('<div class="main-header">📁 Explorador de Archivos (RAW)</div>', unsafe_allow_html=True)
    st.markdown("Visualice cualquier hoja del archivo Excel sin filtros.")
    
    sheet_names = xls.sheet_names
    
    # Pre-seleccionar la hoja de dispositivo si está disponible, sino la primera
    default_sheet = sheet_names[0]
    if mapping.get("device") in sheet_names:
        default_sheet = mapping["device"]
        
    selected_sheet = st.selectbox(
        "Seleccione la hoja de datos:", 
        sheet_names,
        index=sheet_names.index(default_sheet) if default_sheet in sheet_names else 0
    )
    
    if selected_sheet:
        st.caption(f"Mostrando datos de la hoja: **{selected_sheet}**")
        try:
            df = xls.parse(selected_sheet)
            st.dataframe(df, use_container_width=True)
            st.info(f"Total de registros: {len(df):,}")
        except Exception as e:
            st.error(f"Error al cargar la hoja '{selected_sheet}'. Asegúrese de que el formato sea correcto. Error: {e}")

# ================================
# INTERFAZ: SIDEBAR Y NAVEGACIÓN
# ================================

with st.sidebar:
    # --- LOGO ---
    # Usamos un placeholder con un diseño profesional que se ajusta al tema forense/datos
    st.image("https://placehold.co/400x100/1a73e8/ffffff?text=InvestiData+ID", use_column_width=True)
    st.markdown("**Plataforma Forense v2.0**")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📂 Cargar UFED (.xlsx)", type=["xlsx"])
    
    st.markdown("---")
    st.markdown("### Navegación")

    selection = "Inicio"
    sheet_mapping = {}
    xls = None

    if uploaded_file:
        try:
            xls = load_excel(uploaded_file)
            sheet_mapping = normalize_sheet_names(xls.sheet_names)
            
            # Opciones dinámicas según lo encontrado
            nav_options = {"Inicio": "Dashboard"}
            
            if sheet_mapping.get("messages"): nav_options["Mensajes"] = "Mensajes / Chats"
            if sheet_mapping.get("calls"): nav_options["Llamadas"] = "Registro de Llamadas"
            if sheet_mapping.get("contacts"): nav_options["Contactos"] = "Red de Contactos"
            if sheet_mapping.get("locations"): nav_options["Ubicaciones"] = "Mapa GPS"
            if sheet_mapping.get("web"): nav_options["Historial Web"] = "Historial Web"
            if sheet_mapping.get("apps"): nav_options["Aplicaciones"] = "Apps Instaladas"
            
            nav_options["Raw"] = "Explorador de Archivos"
            
            # Si hay un filtro activo, forzar a la vista de resultados filtrados
            if st.session_state['filter_pass']:
                selection = "Resultados Filtrados"
            else:
                selection = st.radio("Ir a:", list(nav_options.keys()), format_func=lambda x: nav_options[x])
            
            st.success("✅ Archivo cargado")
        except Exception as e:
            st.error(f"Error al procesar el archivo Excel. Por favor, verifique el formato. Error: {e}")
            uploaded_file = None # Resetear la carga si hay un error
            xls = None
            
    else:
        st.info("Esperando archivo UFED...")
        # Mensaje de bienvenida si no hay archivo
        st.markdown("---")
        st.markdown("""
        **Guía Rápida:**
        1. Carga un archivo XLSX (reporte UFED/Cellebrite).
        2. Navega por las secciones detectadas automáticamente.
        3. Usa el **Dashboard** para las alertas rápidas y el resumen.
        """)


    st.markdown("---")
    st.caption("InvestiData © 2025\nEsp. Análisis de Datos")

# ================================
# CONTROLADOR PRINCIPAL
# ================================

if uploaded_file and xls:
    
    # 1. MANEJAR PASO DE FILTRO DESDE EL DASHBOARD (PRIORIDAD)
    if st.session_state['filter_pass']:
        sheet_name, mask, category = st.session_state['filter_pass']
        
        st.markdown(f'<div class="main-header">🚨 Hallazgos Filtrados: {category}</div>', unsafe_allow_html=True)
        st.caption(f"Mostrando mensajes filtrados de la hoja: **{sheet_name}**")
        
        try:
            df_full = xls.parse(sheet_name)
            df_filtered = df_full[mask]
            
            st.info(f"Total de registros de alerta: {len(df_filtered):,}")
            st.dataframe(df_filtered, use_container_width=True)
        except Exception as e:
            st.error(f"Error al aplicar el filtro: {e}")

        # Botón para limpiar el estado y volver a la navegación normal
        if st.button("⬅️ Volver al Dashboard"):
            st.session_state['filter_pass'] = None
            st.experimental_rerun()
            
    # 2. MANEJAR NAVEGACIÓN NORMAL
    elif selection == "Inicio":
        view_dashboard(xls, sheet_mapping)
        
    elif selection == "Mensajes":
        if sheet_mapping.get("messages"):
            view_messages(xls, sheet_mapping["messages"])
        else:
            st.warning("Hoja de Mensajes no detectada.")
        
    elif selection == "Llamadas":
        if sheet_mapping.get("calls"):
            # Reutilizamos la vista de mensajes (que maneja filtros generales y gráficos)
            st.markdown(f'<div class="main-header">📞 Registro de Llamadas</div>', unsafe_allow_html=True)
            view_messages(xls, sheet_mapping["calls"])
        else:
            st.warning("Hoja de Llamadas no detectada.")
        
    elif selection == "Contactos":
        if sheet_mapping.get("contacts"):
            view_contacts_graph(xls, sheet_mapping["contacts"])
        else:
            st.warning("Hoja de Contactos no detectada.")
        
    elif selection == "Ubicaciones":
        if sheet_mapping.get("locations"):
            view_locations(xls, sheet_mapping["locations"])
        else:
            st.warning("Hoja de Ubicaciones (GPS) no detectada.")
        
    elif selection == "Historial Web":
        st.markdown(f'<div class="main-header">🌐 Historial de Navegación</div>', unsafe_allow_html=True)
        if sheet_mapping.get("web"):
            df = xls.parse(sheet_mapping["web"])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Hoja de Historial Web no detectada.")
        
    elif selection == "Aplicaciones":
        st.markdown(f'<div class="main-header">📲 Aplicaciones Instaladas</div>', unsafe_allow_html=True)
        if sheet_mapping.get("apps"):
            df = xls.parse(sheet_mapping["apps"])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Hoja de Aplicaciones no detectada.")

    elif selection == "Raw":
        view_raw_explorer(xls, sheet_mapping)
        
else:
    # --- PANTALLA DE BIENVENIDA (LANDING PAGE) ---
    st.markdown(
        f"""
        <div class="welcome-container">
            <h1 style="color: #1a73e8; font-size: 3rem;">InvestiData <span style="font-size: 1.5rem;">v2.0</span></h1>
            <p style="font-size: 1.5rem; color: #333; margin-bottom: 30px;">
                La plataforma inteligente para el análisis automatizado de extracciones forenses móviles.
            </p>
            <hr style="border-top: 2px solid #ddd; margin: 30px 0;">
            <h3 style="color: #1a73e8;">⚙️ Instrucciones de Inicio</h3>
            <div style="text-align: left; max-width: 600px; margin: 0 auto;">
                <ol style="font-size: 1.1rem; line-height: 1.8;">
                    <li>**Prepare el Reporte:** Obtenga un reporte de extracción forense (ej: UFED, Cellebrite) en formato **.xlsx**.</li>
                    <li>**Utilice el Cargador:** Vaya a la barra lateral izquierda y use el botón: 
                        <span style="font-weight: bold; color: #008000;">📂 Cargar UFED (.xlsx)</span>.
                    </li>
                    <li>**Comience a Analizar:** Una vez cargado, el sistema procesará los datos, identificará las hojas y lo dirigirá automáticamente al **Dashboard General**.</li>
                </ol>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
