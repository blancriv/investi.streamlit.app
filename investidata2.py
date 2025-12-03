import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io

# -----------------------------------------------------------------------------
# 1. DEFINICIÓN SEGURA DE VALORES CSS EN PYTHON 
# -----------------------------------------------------------------------------

# Sombras 
DEFAULT_SHADOW_CSS = "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);"
HOVER_SHADOW_CSS = "box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);"

# Tiempos de Transición 
TRANSITION_TIME_SHORT = "0.2s"
TRANSITION_TIME_MEDIUM = "0.3s"

# Tamaño de Fuente Tooltip 
FONT_SIZE_TOOLTIP = "0.875rem"

# Opacidad (Se usará en la inyección de JavaScript/D3)
TOOLTIP_OPACITY_VAL = "0.9" 


# -----------------------------------------------------------------------------
# 2. Lógica de Streamlit (Parte de Python)
# -----------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="InvestiData Forense")

# --- Estado de la Sesión para manejar la carga ---
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'df_loaded' not in st.session_state:
    st.session_state.df_loaded = None


# --- SIDEBAR: Carga de Archivo ---
st.sidebar.markdown("# 📂 Carga de Archivo UFED")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Selecciona el archivo XLSX de extracción forense (UFED)",
    type=['xlsx'],
    help="Debe ser el reporte de extracción que contiene las múltiples hojas de datos (mensajes, llamadas, ubicaciones, etc.).",
)

if uploaded_file is not None:
    # Simulación de procesamiento: solo cargamos un DataFrame simulado
    st.session_state.file_uploaded = True
    
    st.sidebar.success(f"Archivo cargado: **{uploaded_file.name}**")
    st.sidebar.info("Simulando el procesamiento de 30+ hojas de datos...")
    
    # Simulación de los datos cargados para que el Dashboard tenga algo que mostrar
    mock_data = {
        'IMEI Principal': '358945001234567',
        'Marca': 'Samsung',
        'Modelo': 'Galaxy S21 (SM-G991U)',
        'Usuario': 'JRivera_user',
        'Fecha de Extracción': '2025-05-15',
        'Hallazgos Clave': 48,
    }
    st.session_state.df_loaded = mock_data

else:
    st.session_state.file_uploaded = False
    st.session_state.df_loaded = None
    st.sidebar.warning("Esperando la carga del archivo XLSX.")


# -----------------------------------------------------------------------------
# 3. Contenido Principal del Dashboard
# -----------------------------------------------------------------------------

st.markdown("# InvestiData: Plataforma Inteligente Forense")
st.markdown("---")

if st.session_state.file_uploaded and st.session_state.df_loaded:
    # --- Si el archivo está cargado, renderizamos el Dashboard ---
    
    # Inyectamos el valor simulado del IMEI en el HTML
    imei_val = st.session_state.df_loaded['IMEI Principal']
    
    # Definimos la plantilla HTML 
    # NOTA: Todos los corchetes internos de JS/D3/Tailwind config deben ser ESCAPADOS ({{ }})
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InvestiData - Panel de Control Forense</title>
        <!-- Carga de Tailwind CSS -->
        <script src="https://cdn.tailwindcss.com"></script>
        <!-- Carga de D3.js para visualizaciones -->
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <!-- Configuración y Estilos de Tailwind -->
        <script>
            // CORCHETES ESCAPADOS EN CONFIGURACIÓN TAILWIND
            tailwind.config = {{{{
                theme: {{{{
                    extend: {{{{
                        colors: {{{{
                            'primary-blue': '#1a56db', 
                            'secondary-cyan': '#06b6d4', 
                            'accent-red': '#f87171', 
                            'dark-gray': '#1f2937', 
                        }}}},
                        fontFamily: {{{{
                            sans: ['Inter', 'sans-serif'],
                        }}}},
                    }}}},
                }}}},
            }}}}
        </script>
        <style>
            /* Estilos personalizados para el dashboard */
            .card-shadow {{
                /* INYECTADO: Sombra con 0.1 y 0.06 */
                {{DEFAULT_SHADOW}}
                /* Marcadores de posición CSS */
                transition: transform {{TRANSITION_SHORT}}, box-shadow {{TRANSITION_SHORT}};
            }}
            .card-shadow:hover {{
                transform: translateY(-3px);
                /* INYECTADO: Sombra de hover */
                {{HOVER_SHADOW}}
            }}
            /* Estilo para el gráfico D3 */
            .bar-chart rect {{
                fill: #06b6d4;
                transition: fill {{TRANSITION_MEDIUM}} ease;
            }}
            .bar-chart rect:hover {{
                fill: #1a56db;
            }}
            .tooltip {{
                position: absolute;
                text-align: center;
                padding: 8px;
                background: #1f2937;
                color: white;
                border-radius: 6px;
                pointer-events: none;
                opacity: 0;
                transition: opacity {{TRANSITION_MEDIUM}};
                font-size: {{FONT_SIZE}};
                z-index: 100;
            }}
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen font-sans antialiased">

        <!-- Encabezado Fijo con Logo -->
        <header class="bg-dark-gray shadow-xl">
            <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <!-- Logo SVG: Lupa (Investigación) y Bits (Datos) -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-secondary-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10 4v4m0 0v4m0-4h4m-4 0h-4" class="text-white opacity-70" />
                    </svg>
                    <h1 class="text-3xl font-extrabold text-white tracking-wider">
                        InvestiData
                    </h1>
                </div>
                <button id="btn-dashboard" class="px-4 py-2 bg-primary-blue hover:bg-secondary-cyan hover:text-dark-gray text-white font-semibold rounded-lg transition duration-150">
                    Panel Principal
                </button>
            </div>
        </header>

        <!-- Contenido Principal -->
        <main class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <div id="loading-message" class="text-center text-lg text-gray-600 mt-20 hidden">
                Cargando datos y autenticando...
            </div>

            <!-- ID de Usuario (MANDATORIO para apps multiusuario) -->
            <div class="mb-4 text-sm text-gray-500 flex justify-end">
                ID de Usuario (Firebase): <span id="user-id" class="font-mono text-dark-gray ml-2 break-all">Cargando...</span>
            </div>

            <!-- VISTA DEL DASHBOARD PRINCIPAL -->
            <div id="dashboard-view" class="space-y-8">
                
                <!-- Panel de Perfil del Dispositivo (Identificación Forense) - EN LA CIMA -->
                <div class="bg-white p-6 rounded-xl shadow-xl border border-primary-blue/20">
                    <h3 class="text-2xl font-bold text-dark-gray mb-4 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-blue mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        Perfil del Dispositivo Analizado
                    </h3>
                    <div id="device-profile-data" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-gray-700">
                        <!-- Los datos se insertarán aquí por JavaScript -->
                    </div>
                </div>
                
                <h2 class="text-2xl font-bold text-dark-gray border-b-2 border-secondary-cyan pb-2">Panel de Control General</h2>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <!-- Tarjeta de Mensajes Analizados -->
                    <div class="bg-white p-6 rounded-xl card-shadow cursor-pointer border-t-4 border-primary-blue" onclick="navigateToAnalysis('mensajes')">
                        <p class="text-sm font-medium text-gray-500">Total Mensajes</p>
                        <p class="text-4xl font-extrabold text-dark-gray mt-1">1,245</p>
                        <p class="text-sm text-green-600 mt-2 font-medium">Hallazgos: 48 (3.8%)</p>
                    </div>
                    <!-- Tarjeta de Contactos Clave -->
                    <div class="bg-white p-6 rounded-xl card-shadow cursor-pointer border-t-4 border-accent-red" onclick="navigateToAnalysis('contactos')">
                        <p class="text-sm font-medium text-gray-500">Contactos SOSPECHOSOS</p>
                        <p class="text-4xl font-extrabold text-accent-red mt-1">12</p>
                        <p class="text-sm text-gray-600 mt-2">Vínculos detectados: 35</p>
                    </div>
                    <!-- Tarjeta de Geo-localizaciones -->
                    <div class="bg-white p-6 rounded-xl card-shadow cursor-pointer border-t-4 border-secondary-cyan" onclick="navigateToAnalysis('ubicacion')">
                        <p class="text-sm font-medium text-gray-500">Ubicaciones Relevantes</p>
                        <p class="text-4xl font-extrabold text-dark-gray mt-1">4</p>
                        <p class="text-sm text-gray-600 mt-2">Patrones Nocturnos: 2</p>
                    </div>
                    <!-- Tarjeta de Archivos Multimedia -->
                    <div class="bg-white p-6 rounded-xl card-shadow cursor-pointer border-t-4 border-primary-blue" onclick="navigateToAnalysis('archivos')">
                        <p class="text-sm font-medium text-gray-500">Archivos con Coincidencias</p>
                        <p class="text-4xl font-extrabold text-dark-gray mt-1">203</p>
                        <p class="text-sm text-gray-600 mt-2">Contenido Filtrado: 14%</p>
                    </div>
                </div>

                <!-- Panel de Análisis Temático y Búsqueda -->
                <div class="bg-white p-8 rounded-xl shadow-xl border border-primary-blue/20 mt-8">
                    <h3 class="text-xl font-bold text-primary-blue mb-4">Análisis por Temática Criminal</h3>
                    <p class="text-gray-600 mb-4">Haz clic en un tema para ver el análisis detallado de coincidencias y patrones de comunicación.</p>

                    <!-- Botones Temáticos (Clickables) -->
                    <div class="flex flex-wrap gap-4 mb-8">
                        <button class="px-6 py-3 bg-red-600 text-white font-semibold rounded-full hover:bg-red-700 shadow-md transition duration-150" onclick="navigateToAnalysis('matar')">
                            <span class="text-xl mr-1">🔪</span> Homicidio
                        </button>
                        <button class="px-6 py-3 bg-yellow-600 text-white font-semibold rounded-full hover:bg-yellow-700 shadow-md transition duration-150" onclick="navigateToAnalysis('armas')">
                            <span class="text-xl mr-1">🔫</span> Armas / Porte
                        </button>
                        <button class="px-6 py-3 bg-purple-600 text-white font-semibold rounded-full hover:bg-purple-700 shadow-md transition duration-150" onclick="navigateToAnalysis('sexo')">
                            <span class="text-xl mr-1">🔞</span> Delitos Sexuales
                        </button>
                    </div>
                </div>
            </div>

            <!-- VISTA DE ANÁLISIS PROFUNDO / BÚSQUEDA -->
            <div id="analysis-view" class="space-y-8 hidden">
                <h2 id="analysis-title" class="text-3xl font-bold text-dark-gray border-b-2 border-secondary-cyan pb-2">Análisis Profundo</h2>

                <!-- Panel de Búsqueda de Palabras Clave -->
                <div class="bg-white p-6 rounded-xl shadow-xl border border-gray-200">
                    <h3 class="text-xl font-semibold text-dark-gray mb-4">Búsqueda Rápida de Palabras Clave</h3>
                    <div class="flex space-x-3">
                        <input type="text" id="keyword-input" placeholder="Escribe tu palabra clave (ej: dinero, encuentro, dirección...)" class="flex-grow p-3 border-2 border-gray-300 rounded-lg focus:border-primary-blue focus:ring focus:ring-primary-blue/20">
                        <button id="search-button" class="px-6 py-3 bg-primary-blue text-white font-semibold rounded-lg hover:bg-secondary-cyan hover:text-dark-gray transition duration-150">
                            Buscar
                        </button>
                    </div>
                    <div class="mt-4">
                        <p class="text-sm font-medium text-gray-600 mb-2">Sugerencias de Palabras Clave:</p>
                        <div id="keyword-suggestions" class="flex flex-wrap gap-2">
                            <!-- Las sugerencias se insertarán aquí por JS -->
                        </div>
                    </div>
                </div>

                <!-- Sección de Visualizaciones -->
                <div class="grid grid-cols-1 lg:col-span-2 gap-6">
                    <!-- Gráfico de Coincidencias -->
                    <div class="lg:col-span-2 bg-white p-6 rounded-xl shadow-xl border border-gray-200">
                        <h4 class="text-lg font-semibold text-dark-gray mb-4">Gráfico Estadístico de Coincidencias por Frecuencia</h4>
                        <div id="chart-container" class="w-full h-80">
                            <svg id="bar-chart"></svg>
                        </div>
                        <p class="text-sm text-gray-500 mt-4">Frecuencia de las 5 coincidencias más importantes en el dispositivo.</p>
                    </div>

                    <!-- Resumen y Hallazgos Clave -->
                    <div class="lg:col-span-1 bg-white p-6 rounded-xl shadow-xl border border-gray-200">
                        <h4 class="text-lg font-semibold text-dark-gray mb-4">Resumen de Hallazgos</h4>
                        <div id="hallazgos-resumen" class="space-y-4">
                            <p class="text-gray-700 leading-relaxed">
                                <span class="font-bold text-accent-red">Análisis Categórico:</span> Se detectó una alta concentración de mensajes relacionados con el tema "<span id="current-topic-display" class="font-bold text-primary-blue">---</span>", específicamente en los contactos *Juan P.* y *María L*.
                            </p>
                            <p class="text-gray-700 leading-relaxed">
                                <span class="font-bold text-primary-blue">Patrón Temporal:</span> El 85% de las coincidencias ocurrieron entre las 23:00 y 02:00 horas, indicando actividad nocturna.
                            </p>
                            <p class="text-gray-700 leading-relaxed">
                                <span class="font-bold text-primary-blue">Geográfico:</span> Una dirección fue mencionada 7 veces en mensajes codificados.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Resultados de Búsqueda -->
                <div id="search-results-section" class="bg-white p-6 rounded-xl shadow-xl border border-gray-200 hidden">
                    <h4 class="text-lg font-semibold text-dark-gray mb-4">Resultados para "<span id="searched-keyword" class="text-secondary-cyan font-mono"></span>" (<span id="result-count">0</span>)</h4>
                    <div id="search-results-list" class="space-y-3 max-h-96 overflow-y-auto">
                        <p class="text-gray-500 italic" id="no-results-message">No se encontraron mensajes que coincidan con la palabra clave.</p>
                        <!-- Los mensajes de resultado se insertarán aquí -->
                    </div>
                </div>
            </div>

        </main>

        <!-- Scripts de Firebase y Lógica de la Aplicación -->
        <script type="module">
            // Importaciones de Firebase (requeridas para persistencia/autenticación)
            import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
            import {{ getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged }} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
            import {{ getFirestore, doc, setDoc, getDoc }} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
            import {{ setLogLevel }} from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

            // Establecer nivel de log para depuración de Firestore
            setLogLevel('error'); 

            // Variables Globales
            let app;
            let db;
            let auth;
            let userId = null;
            let isAuthReady = false;

            // Configuración de Firebase (proporcionada por el entorno)
            const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{{}}');
            const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
            const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;

            const loadingMessage = document.getElementById('loading-message');
            loadingMessage.classList.remove('hidden');

            // --- 1. Inicialización de Firebase y Autenticación ---
            if (Object.keys(firebaseConfig).length > 0) {{{{ // ESCAPE DE LLAVES
                app = initializeApp(firebaseConfig);
                db = getFirestore(app);
                auth = getAuth(app);

                // Asegurar la autenticación antes de usar Firestore
                onAuthStateChanged(auth, async (user) => {{{{ // ESCAPE DE LLAVES
                    if (!user) {{{{ // ESCAPE DE LLAVES
                        try {{{{ // ESCAPE DE LLAVES
                            if (initialAuthToken) {{{{ // ESCAPE DE LLAVES
                                await signInWithCustomToken(auth, initialAuthToken);
                            }}}} else {{{{ // ESCAPE DE LLAVES
                                await signInAnonymously(auth);
                            }}}} // ESCAPE DE LLAVES
                            // La lógica se ejecutará nuevamente cuando onAuthStateChanged detecte el usuario
                        }}}} catch (error) {{{{ // ESCAPE DE LLAVES
                            console.error("Error en la autenticación:", error);
                            document.getElementById('user-id').textContent = 'Error de Auth';
                            isAuthReady = true;
                            loadingMessage.classList.add('hidden');
                        }}}} // ESCAPE DE LLAVES
                    }}}} else {{{{ // ESCAPE DE LLAVES
                        userId = user.uid;
                        document.getElementById('user-id').textContent = userId;
                        isAuthReady = true;
                        loadingMessage.classList.add('hidden');
                        // Una vez autenticado, cargar el estado o inicializar la app
                        loadAppState();
                    }}}} // ESCAPE DE LLAVES
                }}}}); // ESCAPE DE LLAVES
            }}}} else {{{{ // ESCAPE DE LLAVES
                console.error("Configuración de Firebase no disponible. La persistencia de datos estará deshabilitada.");
                userId = 'Anon-Simulated-' + Math.random().toString(36).substr(2, 9);
                document.getElementById('user-id').textContent = userId;
                isAuthReady = true;
                loadingMessage.classList.add('hidden');
            }}}} // ESCAPE DE LLAVES

            // --- 2. Lógica de Navegación y Estado ---
            let currentView = 'dashboard'; // 'dashboard' o 'analysis'
            let currentFocusTopic = 'general'; // Tema actual para el análisis

            const dashboardView = document.getElementById('dashboard-view');
            const analysisView = document.getElementById('analysis-view');
            const analysisTitle = document.getElementById('analysis-title');
            const currentTopicDisplay = document.getElementById('current-topic-display');
            const keywordInput = document.getElementById('keyword-input');
            const searchButton = document.getElementById('search-button');
            const resultsList = document.getElementById('search-results-list');
            const searchResultsSection = document.getElementById('search-results-section');
            const searchedKeywordSpan = document.getElementById('searched-keyword');
            const resultCountSpan = document.getElementById('result-count');
            const noResultsMessage = document.getElementById('no-results-message');

            function switchView(view) {{{{ // ESCAPE DE LLAVES
                currentView = view;
                if (view === 'dashboard') {{{{ // ESCAPE DE LLAVES
                    dashboardView.classList.remove('hidden');
                    analysisView.classList.add('hidden');
                }}}} else {{{{ // ESCAPE DE LLAVES
                    dashboardView.classList.add('hidden');
                    analysisView.classList.remove('hidden');
                }}}} // ESCAPE DE LLAVES
                saveAppState();
            }}}} // ESCAPE DE LLAVES

            window.navigateToAnalysis = function(topic) {{{{ // ESCAPE DE LLAVES
                currentFocusTopic = topic;
                let titleText = 'Análisis Profundo';
                
                // Simular el título según el tema
                switch (topic) {{{{ // ESCAPE DE LLAVES
                    case 'armas': titleText = 'Análisis Temático: Armas y Porte'; break;
                    case 'sexo': titleText = 'Análisis Temático: Delitos Sexuales'; break;
                    case 'matar': titleText = 'Análisis Temático: Homicidio y Amenazas'; break;
                    case 'mensajes': titleText = 'Análisis General de Mensajes'; break;
                    case 'contactos': titleText = 'Análisis de Redes y Contactos Clave'; break;
                    case 'ubicacion': titleText = 'Análisis Geográfico y Patrones de Movimiento'; break;
                    case 'archivos': titleText = 'Análisis de Contenido Multimedia'; break;
                }}}} // ESCAPE DE LLAVES

                analysisTitle.textContent = titleText;
                currentTopicDisplay.textContent = titleText.split(': ')[1] || topic.charAt(0).toUpperCase() + topic.slice(1);
                
                // Renderizar el gráfico para el tema
                renderBarChart(getMockChartData(topic));
                
                // Cargar sugerencias
                renderKeywordSuggestions(topic);
                
                // Ocultar resultados de búsqueda al cambiar de análisis
                searchResultsSection.classList.add('hidden');
                
                switchView('analysis');
            }}}} // ESCAPE DE LLAVES

            // Navegación al Dashboard
            document.getElementById('btn-dashboard').addEventListener('click', () => {{{{ // ESCAPE DE LLAVES
                switchView('dashboard');
            }}}}); // ESCAPE DE LLAVES

            // --- 3. Firebase: Persistencia del Estado ---
            async function saveAppState() {{{{ // ESCAPE DE LLAVES
                if (!isAuthReady || !db) return;
                try {{{{ // ESCAPE DE LLAVES
                    // Corregido: Uso de plantilla literal de JS para las variables de Firebase
                    const userSettingsRef = doc(db, `artifacts/\${{appId}}/users/\${{userId}}/investidata_settings`, 'dashboard_state');
                    await setDoc(userSettingsRef, {{{{ // ESCAPE DE LLAVES
                        currentView: currentView,
                        currentFocusTopic: currentFocusTopic,
                        lastUpdated: new Date().toISOString()
                    }}}}, {{{{ merge: true }}}} ); // ESCAPE DE LLAVES
                    // console.log("Estado de la aplicación guardado.");
                }}}} catch (e) {{{{ // ESCAPE DE LLAVES
                    console.error("Error al guardar el estado: ", e);
                }}}} // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES

            async function loadAppState() {{{{ // ESCAPE DE LLAVES
                if (!isAuthReady || !db) return;
                try {{{{ // ESCAPE DE LLAVES
                    // Corregido: Uso de plantilla literal de JS para las variables de Firebase
                    const userSettingsRef = doc(db, `artifacts/\${{appId}}/users/\${{userId}}/investidata_settings`, 'dashboard_state');
                    const docSnap = await getDoc(userSettingsRef);

                    if (docSnap.exists()) {{{{ // ESCAPE DE LLAVES
                        const data = docSnap.data();
                        // Restaurar el último estado visitado
                        if (data.currentView === 'analysis') {{{{ // ESCAPE DE LLAVES
                            navigateToAnalysis(data.currentFocusTopic || 'mensajes');
                        }}}} else {{{{ // ESCAPE DE LLAVES
                            switchView('dashboard');
                        }}}} // ESCAPE DE LLAVES
                        // console.log("Estado de la aplicación cargado.");
                    }}}} else {{{{ // ESCAPE DE LLAVES
                        switchView('dashboard');
                    }}}} // ESCAPE DE LLAVES
                }}}} catch (e) {{{{ // ESCAPE DE LLAVES
                    console.error("Error al cargar el estado: ", e);
                    switchView('dashboard'); // Fallback
                }}}} // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES

            // --- 4. Datos Simulados y Funcionalidad de Búsqueda ---
            
            // Mock de Datos del Perfil del Dispositivo
            const mockDeviceProfile = {{{{ // ESCAPE DE LLAVES
                imei: '{imei_val}', // Usamos la variable inyectada desde Python
                marca: 'Samsung',
                modelo: 'Galaxy S21 (SM-G991U)',
                usuario: 'JRivera_user',
                correo_asociado: 'j.rivera.clave@fake-mail.com',
                whatsapp_id: '+57 310 123 4567',
                facebook_profile: 'JuanRivera1985',
                instagram_id: 'riveraj_official'
            }}}} // ESCAPE DE LLAVES ;

            // Mock de Datos Forenses (Mensajes)
            const mockMessages = [ // ESCAPE DE LLAVES
                {{ id: 1, contact: 'Juan P.', text: 'El paquete ya está listo. Trae el juguete nuevo (arma).', date: '2025-11-20' }}, // ESCAPE DE LLAVES
                {{ id: 2, contact: 'María L.', text: 'Nos vemos a las 10pm en el lugar de siempre. Confirma el precio.', date: '2025-11-21' }}, // ESCAPE DE LLAVES
                {{ id: 3, contact: 'Contacto X', text: 'Hay que anular el negocio si no traen el dinero pronto.', date: '2025-11-21' }}, // ESCAPE DE LLAVES
                {{ id: 4, contact: 'Juan P.', text: 'Tengo las coordenadas del punto de encuentro. Es vital no fallar.', date: '2025-11-22' }}, // ESCAPE DE LLAVES
                {{ id: 5, contact: 'El Jefe', text: 'Si se resiste, hay que neutralizarlo (matar). Sin testigos.', date: '2025-11-23' }}, // ESCAPE DE LLAVES
                {{ id: 6, contact: 'María L.', text: 'Las fotos de la mercancía. ¿Necesitas algo más del sexo?', date: '2025-11-24' }}, // ESCAPE DE LLAVES
                {{ id: 7, contact: 'Contacto X', text: 'Revisa las cuentas y el balance.', date: '2025-11-25' }}, // ESCAPE DE LLAVES
                {{ id: 8, contact: 'Juan P.', text: 'La pistola está en el escondite. Asegúrate de llevarla.', date: '2025-11-26' }}, // ESCAPE DE LLAVES
                {{ id: 9, contact: 'El Jefe', text: 'El objetivo debe ser eliminado antes del amanecer.', date: '2025-11-27' }}, // ESCAPE DE LLAVES
                {{ id: 10, contact: 'María L.', text: 'Te envío los detalles para la reunión privada. Es un cliente importante.', date: '2025-11-28' }}, // ESCAPE DE LLAVES
            ]; // ESCAPE DE LLAVES

            // Función para simular datos de gráfico por tema
            function getMockChartData(topic) {{{{ // ESCAPE DE LLAVES
                let data = []; // ESCAPE DE LLAVES
                switch (topic) {{{{ // ESCAPE DE LLAVES
                    case 'armas':
                        data = [ // ESCAPE DE LLAVES
                            {{ keyword: 'pistola', count: 35 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'juguete', count: 18 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'fierro', count: 12 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'munición', count: 9 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'calibre', count: 5 }}, // ESCAPE DE LLAVES
                        ]; // ESCAPE DE LLAVES
                        break;
                    case 'sexo':
                        data = [ // ESCAPE DE LLAVES
                            {{ keyword: 'privada', count: 42 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'fotos', count: 31 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'cita', count: 19 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'cliente', count: 15 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'hotel', count: 10 }}, // ESCAPE DE LLAVES
                        ]; // ESCAPE DE LLAVES
                        break;
                    case 'matar':
                        data = [ // ESCAPE DE LLAVES
                            {{ keyword: 'eliminar', count: 55 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'neutralizar', count: 40 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'anular', count: 28 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'deshacer', count: 15 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'silenciar', count: 10 }}, // ESCAPE DE LLAVES
                        ]; // ESCAPE DE LLAVES
                        break;
                    default:
                        data = [ // ESCAPE DE LLAVES
                            {{ keyword: 'dinero', count: 50 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'encuentro', count: 40 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'dirección', count: 30 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'paquete', count: 20 }}, // ESCAPE DE LLAVES
                            {{ keyword: 'coordenadas', count: 10 }}, // ESCAPE DE LLAVES
                        ]; // ESCAPE DE LLAVES
                        break;
                }}}} // ESCAPE DE LLAVES
                return data;
            }}}} // ESCAPE DE LLAVES

            // Lógica de Búsqueda
            function handleSearch() {{{{ // ESCAPE DE LLAVES
                const keyword = keywordInput.value.trim().toLowerCase();
                if (!keyword) return;

                const results = mockMessages.filter(msg =>
                    msg.text.toLowerCase().includes(keyword)
                );

                // Mostrar resultados
                resultsList.innerHTML = '';
                searchResultsSection.classList.remove('hidden');
                searchedKeywordSpan.textContent = keyword;
                resultCountSpan.textContent = results.length;
                noResultsMessage.classList.add('hidden');

                if (results.length === 0) {{{{ // ESCAPE DE LLAVES
                    noResultsMessage.classList.remove('hidden');
                }}}} else {{{{ // ESCAPE DE LLAVES
                    results.forEach(msg => {{{{ // ESCAPE DE LLAVES
                        const resultItem = document.createElement('div');
                        resultItem.className = 'p-3 bg-gray-100 rounded-lg border border-gray-200 hover:bg-primary-blue/5 transition duration-150';
                        // Resaltar la palabra clave encontrada
                        const highlightedText = msg.text.replace(new RegExp('(' + keyword + ')', 'gi'), '<span class="bg-yellow-300 font-bold text-dark-gray rounded-sm p-0.5">\$1</span>'); // ESCAPE DE LLAVES
                        // ESCAPE DE LLAVES EN LAS PLANTILLAS LITERALES DE JS
                        resultItem.innerHTML = `
                            <p class="text-xs text-gray-500 font-mono">ID: \${{msg.id}} | Contacto: \${{msg.contact}} | Fecha: \${{msg.date}}</p>
                            <p class="text-gray-800 mt-1">\${{highlightedText}}</p>
                        `;
                        resultsList.appendChild(resultItem);
                    }}}}); // ESCAPE DE LLAVES
                }}}} // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES

            searchButton.addEventListener('click', handleSearch);
            keywordInput.addEventListener('keypress', (e) => {{{{ // ESCAPE DE LLAVES
                if (e.key === 'Enter') {{{{ // ESCAPE DE LLAVES
                    handleSearch();
                }}}} // ESCAPE DE LLAVES
            }}}}); // ESCAPE DE LLAVES

            // --- 5. Sugerencias de Palabras Clave ---

            // Palabras clave fijas para sugerir
            const fixedSuggestions = {{{{ // ESCAPE DE LLAVES
                armas: ['pistola', 'calibre', 'fierro', 'munición', 'juguete'],
                sexo: ['privada', 'fotos', 'cita', 'hotel', 'cliente', 'sexo'],
                matar: ['eliminar', 'neutralizar', 'anular', 'testigos', 'silenciar'],
                general: ['dinero', 'encuentro', 'paquete', 'coordenadas', 'dirección']
            }}}} // ESCAPE DE LLAVES;

            function renderKeywordSuggestions(topic) {{{{ // ESCAPE DE LLAVES
                const container = document.getElementById('keyword-suggestions');
                container.innerHTML = '';
                
                const suggestions = fixedSuggestions[topic] || fixedSuggestions.general;

                suggestions.forEach(keyword => {{{{ // ESCAPE DE LLAVES
                    const button = document.createElement('button');
                    button.textContent = keyword;
                    button.className = 'px-3 py-1 text-sm bg-gray-200 text-dark-gray rounded-full hover:bg-secondary-cyan hover:text-dark-gray transition duration-150 shadow-sm';
                    button.onclick = () => {{{{ // ESCAPE DE LLAVES
                        keywordInput.value = keyword;
                        handleSearch();
                    }}}} // ESCAPE DE LLAVES;
                    container.appendChild(button);
                }}}}); // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES

            // --- 6. Visualización con D3.js (Gráfico de Barras) ---

            function renderBarChart(data) {{{{ // ESCAPE DE LLAVES
                const container = d3.select("#chart-container");
                const svg = d3.select("#bar-chart");
                
                // Limpiar el SVG anterior
                svg.selectAll('*').remove();

                const margin = {{{{ top: 20, right: 30, bottom: 50, left: 60 }}}}; // ESCAPE DE LLAVES
                
                // Hacer el gráfico responsivo
                const containerWidth = document.getElementById('chart-container').offsetWidth;
                const containerHeight = document.getElementById('chart-container').offsetHeight;
                
                const width = containerWidth - margin.left - margin.right;
                const height = containerHeight - margin.top - margin.bottom;

                svg.attr("width", containerWidth)
                   .attr("height", containerHeight);

                // CORRECCIÓN: Usar la plantilla literal de JS con doble escape para Python
                const chartGroup = svg.append("g")
                    .attr("transform", `translate(\${{margin.left}},\${{margin.top}})` );

                // 1. Escalas
                const x = d3.scaleBand()
                    .domain(data.map(d => d.keyword))
                    .range([0, width])
                    .padding(0.3);

                const y = d3.scaleLinear()
                    .domain([0, d3.max(data, d => d.count) * 1.1])
                    .range([height, 0]);

                // Tooltip
                const tooltip = d3.select("body").append("div")
                    .attr("class", "tooltip");

                // 2. Barras
                chartGroup.selectAll(".bar")
                    .data(data)
                    .enter().append("rect")
                    .attr("class", "bar-chart")
                    // CORRECCIÓN: Los argumentos de D3 necesitan ser doblemente escapados (d => x(d.keyword))
                    .attr("x", d => x(d.keyword))
                    .attr("y", d => y(d.count))
                    .attr("width", x.bandwidth())
                    .attr("height", d => height - y(d.count))
                    .on("mouseover", function(event, d) {{{{ // ESCAPE DE LLAVES
                        d3.select(this).attr("fill", "#1a56db"); // Hover color
                        tooltip.transition()
                            .duration(200)
                            // CORRECCIÓN CLAVE: Se pasa la variable como string simple para evitar conflictos de doble llave.
                            .style("opacity", "{{TOOLTIP_OPACITY}}"); 
                        // CORRECCIÓN: El contenido de la plantilla literal necesita ESCAPE DE LLAVES
                        tooltip.html(`Coincidencias: <strong>\${{d.count}}</strong>`)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 28) + "px");
                    }}}} ) // ESCAPE DE LLAVES
                    .on("mouseout", function() {{{{ // ESCAPE DE LLAVES
                        d3.select(this).attr("fill", "#06b6d4"); // Restore color
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0);
                    }}}}); // ESCAPE DE LLAVES

                // 3. Ejes
                // Eje X (Palabras Clave)
                chartGroup.append("g")
                    // CORRECCIÓN: Usar la plantilla literal de JS con doble escape para Python
                    .attr("transform", `translate(0,\${{height}})` )
                    .call(d3.axisBottom(x))
                    .selectAll("text")
                    .style("text-anchor", "middle")
                    .attr("class", "text-dark-gray");

                // Etiqueta del Eje X
                chartGroup.append("text")
                    // CORRECCIÓN: Usar la plantilla literal de JS con doble escape para Python
                    .attr("transform", `translate(\${{width / 2}}, \${{height + margin.bottom - 10}})` )
                    .style("text-anchor", "middle")
                    .text("Palabras Clave Detectadas")
                    .attr("class", "text-sm font-semibold text-dark-gray");

                // Eje Y (Frecuencia)
                chartGroup.append("g")
                    .call(d3.axisLeft(y).ticks(5))
                    .attr("class", "text-dark-gray");

                // Etiqueta del Eje Y
                chartGroup.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("y", 0 - margin.left)
                    // CORRECCIÓN: Usar la plantilla literal de JS con doble escape para Python
                    .attr("x", 0 - (\${{height}} / 2))
                    .attr("dy", "1em")
                    .style("text-anchor", "middle")
                    .text("Frecuencia Absoluta")
                    .attr("class", "text-sm font-semibold text-dark-gray");
            }}}} // ESCAPE DE LLAVES
            
            // --- 7. Renderizado del Perfil del Dispositivo ---
            
            function renderDeviceProfile() {{{{ // ESCAPE DE LLAVES
                const container = document.getElementById('device-profile-data');
                container.innerHTML = ''; // Limpiar

                const data = [ // ESCAPE DE LLAVES
                    {{ label: 'IMEI Principal', value: mockDeviceProfile.imei }}, // ESCAPE DE LLAVES
                    {{ label: 'Marca / Fabricante', value: mockDeviceProfile.marca }}, // ESCAPE DE LLAVES
                    {{ label: 'Modelo Exacto', value: mockDeviceProfile.modelo }}, // ESCAPE DE LLAVES
                    {{ label: 'Nombre de Usuario', value: mockDeviceProfile.usuario }}, // ESCAPE DE LLAVES
                    {{ label: 'Correo Asociado (Cuentas)', value: mockDeviceProfile.correo_asociado }}, // ESCAPE DE LLAVES
                    {{ label: 'ID de WhatsApp', value: mockDeviceProfile.whatsapp_id }}, // ESCAPE DE LLAVES
                    {{ label: 'Perfil de Facebook', value: mockDeviceProfile.facebook_profile }}, // ESCAPE DE LLAVES
                    {{ label: 'ID de Instagram', value: mockDeviceProfile.instagram_id }} // ESCAPE DE LLAVES
                ]; // ESCAPE DE LLAVES

                data.forEach(item => {{{{ // ESCAPE DE LLAVES
                    const itemDiv = document.createElement('div');
                    // Ajustar el estilo para el diseño de la grilla
                    itemDiv.className = 'p-3 bg-gray-50 rounded-lg border border-gray-200 shadow-inner'; 
                    // CORRECCIÓN: Se escapan las llaves en las plantillas literales.
                    itemDiv.innerHTML = `
                        <p class="text-xs font-semibold text-primary-blue">\${{item.label}}</p>
                        <p class="text-sm font-mono text-dark-gray break-all mt-0.5">\${{item.value}}</p>
                    `;
                    container.appendChild(itemDiv);
                }}}}); // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES


            // Inicialización de la vista
            window.onload = function() {{{{ // ESCAPE DE LLAVES
                renderDeviceProfile(); // Llamar a la función al inicio
                if (isAuthReady) {{{{ // ESCAPE DE LLAVES
                    loadAppState();
                }}}} // ESCAPE DE LLAVES
                // Asegurarse de que el gráfico se renderice si se carga directamente en análisis
                if (currentView === 'analysis') {{{{ // ESCAPE DE LLAVES
                    renderBarChart(getMockChartData(currentFocusTopic));
                }}}} else {{{{ // ESCAPE DE LLAVES
                     // Mostrar el dashboard por defecto si no hay estado cargado
                     switchView('dashboard');
                }}}} // ESCAPE DE LLAVES
            }}}} // ESCAPE DE LLAVES;

            // Escucha de resize para hacer el gráfico responsivo
            window.addEventListener('resize', () => {{{{ // ESCAPE DE LLAVES
                 if (currentView === 'analysis') {{{{ // ESCAPE DE LLAVES
                    renderBarChart(getMockChartData(currentFocusTopic));
                }}}} // ESCAPE DE LLAVES
            }}}}); // ESCAPE DE LLAVES

        </script>
    </body>
    </html>
    """

    # Sustituimos TODOS los placeholders con las cadenas CSS/JS definidas de forma segura.
    HTML_FINAL = HTML_TEMPLATE.format(
        DEFAULT_SHADOW=DEFAULT_SHADOW_CSS,
        HOVER_SHADOW=HOVER_SHADOW_CSS,
        TRANSITION_SHORT=TRANSITION_TIME_SHORT,
        TRANSITION_MEDIUM=TRANSITION_TIME_MEDIUM,
        FONT_SIZE=FONT_SIZE_TOOLTIP,
        TOOLTIP_OPACITY=TOOLTIP_OPACITY_VAL
    )

    components.html(
        HTML_FINAL,
        height=1200,
        scrolling=True
    )



    
else:
    # --- Mensaje de bienvenida/instrucción si no hay archivo cargado ---
    st.markdown("""
        <div class="p-8 bg-white rounded-xl shadow-xl border-l-4 border-secondary-cyan mt-10">
            <h3 class="text-3xl font-bold text-dark-gray mb-4">Bienvenido a InvestiData</h3>
            <p class="text-lg text-gray-600 mb-6">
                Para comenzar, por favor, **carga el archivo de extracción forense (.xlsx)** en la barra lateral izquierda.
            </p>
            <ul class="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>El archivo debe ser el reporte consolidado generado por herramientas como **UFED/Cellebrite**.</li>
                <li>InvestiData procesará automáticamente las múltiples hojas de datos (mensajes, llamadas, ubicaciones).</li>
                <li>Una vez cargado, se mostrará el panel de análisis completo.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
