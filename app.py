import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium


st.set_page_config(layout="wide")
st.markdown(
    """
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .main {
            background-color: #fbfbfb;
        }

        body, .reportview-container {
            color: #fbfbfb;
        }

        h1 {
            color: #193a73;
            font-weight: bold;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        h2, h3, h4 {
            color: #193a73;
            font-weight: bold;
        }
        .stSelectbox > div > div {
            background-color: white;
            color: #193a73;
            font-weight: bold;
        }
        .stSelectbox label {
            color: #193a73;
            font-weight: bold;
        }
        .stButton button {
            background-color: #fbc408;
            color: black;
            font-weight: bold;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            transition: background-color 0.3s;
        }
        .stButton button:hover {
            background-color: #ffd700;
        }
        .stDataFrame thead tr th {
            background-color: #193a73;
            color: white;
        }
        .stDataFrame tbody tr {
            background-color: #ffffff;
        }
    </style>
    <canvas id="dynamic-bg" width="100" height="100" style="position: fixed; top: 0; left: 0; z-index: -1; width: 100%; height: 100%; pointer-events: none;"></canvas>
    <script>
    document.addEventListener("DOMContentLoaded", function () {
        const canvas = document.getElementById('dynamic-bg');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        function resize() {
          canvas.width = window.innerWidth;
          canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();
        let t = 0;
        function draw() {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          for (let x = 0; x < canvas.width; x += 50) {
            for (let y = 0; y < canvas.height; y += 50) {
              ctx.beginPath();
              ctx.arc(x + 10*Math.sin(t + x/100 + y/100), y + 10*Math.cos(t + x/100 - y/100), 3, 0, Math.PI * 2);
              ctx.fillStyle = '#fbc408';
              ctx.fill();
            }
          }
          t += 0.01;
          requestAnimationFrame(draw);
        }
        draw();
    });
    </script>
    """,
    unsafe_allow_html=True
)
st.title("Visualización de Rutas por Tractos")

# Leer el archivo Excel con caché
@st.cache_data
def cargar_datos():
    return pd.read_excel("Base_final.xlsx")

df = cargar_datos()

# Crear columna combinada de ruta ciudad
df["Ruta Ciudad"] = df["Ciudad Origen"].astype(str).str.strip() + " - " + df["Ciudad Destino"].astype(str).str.strip()

df["Ciudad Origen"] = df["Ciudad Origen"].astype(str).str.strip()
df["Ciudad Destino"] = df["Ciudad Destino"].astype(str).str.strip()

# Asegurar que kmstotales no sea 0 ni NaN
df = df[df["kmstotales"].notna() & (df["kmstotales"] > 0)]

# Calcular Costo Total y CPK
df["Costo Total"] = df["Costo por carga"] + df["Costo Peajes"] + df["Costo Mantenimiento"]
df["CPK"] = df["Costo Total"] / df["kmstotales"]


ciudad_origen = st.selectbox("Selecciona ciudad de origen:", ["--- Mostrar todas ---"] + sorted(df["Ciudad Origen"].dropna().unique()))
ciudad_destino = st.selectbox("Selecciona ciudad de destino:", ["--- Mostrar todas ---"] + sorted(df["Ciudad Destino"].dropna().unique()))

if ciudad_origen != "--- Mostrar todas ---" and ciudad_destino != "--- Mostrar todas ---":
    df_filtrado = df[
        (df["Ciudad Origen"] == ciudad_origen) &
        (df["Ciudad Destino"] == ciudad_destino)
    ]
elif ciudad_origen != "--- Mostrar todas ---":
    df_filtrado = df[df["Ciudad Origen"] == ciudad_origen]
elif ciudad_destino != "--- Mostrar todas ---":
    df_filtrado = df[df["Ciudad Destino"] == ciudad_destino]
else:
    df_filtrado = df.copy()

# Mostrar CPK promedio solo cuando se haya seleccionado origen y destino
if ciudad_origen != "--- Mostrar todas ---" and ciudad_destino != "--- Mostrar todas ---" and not df_filtrado.empty:
    cpk_medio = round(df_filtrado["CPK"].dropna().mean(), 2)
    st.markdown(f"""
    <div style="position: relative; background-color: #fbc408; padding: 1rem 1.5rem; border-radius: 0.5rem; box-shadow: 0 2px 6px rgba(0,0,0,0.2); margin-top: 1rem; margin-bottom: 1rem; max-width: 320px;">
        <h4 style="margin: 0; color: #193a73; font-weight: bold; font-size: 1.2rem;">
            CPK promedio de la ruta: {cpk_medio}
        </h4>
    </div>
    """, unsafe_allow_html=True)

tractos = ["--- Mostrar todos ---"] + sorted(df_filtrado["Tracto"].dropna().astype(str).unique())
tracto_seleccionado = st.selectbox("Selecciona un tracto:", tractos)

if tracto_seleccionado != "--- Mostrar todos ---":
    df_filtrado = df_filtrado[df_filtrado["Tracto"].astype(str) == tracto_seleccionado]

if tracto_seleccionado != "--- Mostrar todos ---" and not df_filtrado.empty:
    cpk_individual = round(df_filtrado["CPK"].dropna().mean(), 2)
    st.markdown(f"""
    <div style="position: relative; background-color: #fbc408; padding: 1rem 1.5rem; border-radius: 0.5rem; box-shadow: 0 2px 6px rgba(0,0,0,0.2); margin-top: 1rem; margin-bottom: 1rem; max-width: 420px;">
        <h4 style="margin: 0; color: #193a73; font-weight: bold; font-size: 1.2rem;">
            CPK de este tracto en esta ruta: {cpk_individual}
        </h4>
    </div>
    """, unsafe_allow_html=True)

if len(df_filtrado) > 2000:
    st.warning("⚠️ Hay muchas rutas para mostrar. Filtra por origen, destino o tracto para mejorar el rendimiento.")
    st.stop()


# Filtrar filas con valores válidos en CPK y kmstotales
df_filtrado = df_filtrado[df_filtrado["CPK"].notna() & df_filtrado["kmstotales"].notna()]

# Obtener rutas únicas y limpiar CPK inválido
# Asegurarse de incluir todas las filas únicas por tracto, incluso si tienen misma ruta
df_rutas = df_filtrado[["lat_destino", "lon_destino", "lat_origen", "lon_origen", "Ruta Estados", "Tracto", "CPK"]].dropna(subset=["lat_origen", "lon_origen", "lat_destino", "lon_destino"])
df_rutas = df_rutas[df_rutas["CPK"].notna() & (df_rutas["CPK"] != float("inf"))]

# Verificar si hay rutas con coordenadas faltantes
rutas_invalidas = df_filtrado[["lat_destino", "lon_destino", "lat_origen", "lon_origen", "Ruta Estados", "Tracto", "CPK"]][
    df_filtrado[["lat_destino", "lon_destino", "lat_origen", "lon_origen"]].isna().any(axis=1)
]
if not rutas_invalidas.empty:
    st.warning("⚠️ Existen rutas con coordenadas faltantes que no se mostrarán en el mapa. Esto puede deberse a errores u omisiones en el registro de datos.")

# Filtrar rutas fuera del rango geográfico razonable para México
def coordenadas_validas(df):
    return (
        df["lat_origen"].between(14, 33) &
        df["lon_origen"].between(-120, -86) &
        df["lat_destino"].between(14, 33) &
        df["lon_destino"].between(-120, -86)
    )

rutas_invalidas = df_rutas[~coordenadas_validas(df_rutas)]
if not rutas_invalidas.empty:
    st.warning(f"⚠️ Se descartaron {len(rutas_invalidas)} rutas con coordenadas fuera del rango esperado. Verifica los datos.")

df_rutas = df_rutas[coordenadas_validas(df_rutas)]


# Opcional: mostrar rutas descartadas
with st.expander("Ver rutas descartadas"):
    st.dataframe(rutas_invalidas[["Tracto", "Ruta Estados", "lat_origen", "lon_origen", "lat_destino", "lon_destino"]])

# Crear mapa centrado en México
m = folium.Map(location=[23.6345, -102.5528], zoom_start=5)

# Agregar trayectos al mapa
if tracto_seleccionado == "--- Mostrar todos ---":
    mostrar_todas_rutas = True
else:
    mostrar_todas_rutas = False

for _, row in df_rutas.iterrows():
    destino = [row["lat_destino"], row["lon_destino"]]
    origen = [row["lat_origen"], row["lon_origen"]]
    ruta = [origen, destino]

    folium.PolyLine(
        ruta,
        color="blue",
        weight=3,
        opacity=0.4 if mostrar_todas_rutas else 0.9,
        tooltip=f"Tracto: {row['Tracto']}<br>Ruta: {row['Ruta Estados']}<br>CPK: {row['CPK']:.2f}"
    ).add_to(m)

    folium.CircleMarker(
        location=origen,
        radius=4 if mostrar_todas_rutas else 6,
        color="green" if not mostrar_todas_rutas else "#88cc88",
        fill=True,
        fill_opacity=0.6 if mostrar_todas_rutas else 0.9,
        tooltip="Origen" if not mostrar_todas_rutas else None
    ).add_to(m)

    folium.Marker(
        location=destino,
        icon=folium.Icon(color="red" if not mostrar_todas_rutas else "lightred", icon="remove"),
        tooltip="Destino" if not mostrar_todas_rutas else None
    ).add_to(m)


with st.container():
    st_folium(m, returned_objects=[], height=500, width=1200)

    st.markdown("### Resumen de rutas visualizadas", unsafe_allow_html=True)

    columnas = [
        "Ruta Estados",
        "Tracto",
        "kmstotales",
        "Costo por carga",
        "Costo Peajes",
        "Costo Mantenimiento",
        "Costo Total",
        "CPK"
    ]
    columnas_validas = [col for col in columnas if col in df_filtrado.columns]
    df_resumen = df_filtrado[columnas_validas].drop_duplicates().sort_values(by="CPK", ascending=False)

    for col in [
        "CPK",
        "kmstotales",
        "Costo por carga",
        "Costo Peajes",
        "Costo Mantenimiento",
        "Costo Total"
    ]:
        if col in df_resumen.columns:
            df_resumen[col] = df_resumen[col].map(lambda x: round(x, 2))

    def resaltar_cpk_alto(row):
        if "CPK" in row and row["CPK"] > 1000:
            return ['background-color: #fff3cd'] * len(row)
        else:
            return [''] * len(row)

    if not df_resumen.empty:
        st.dataframe(
            df_resumen.style.apply(resaltar_cpk_alto, axis=1),
            use_container_width=True
        )