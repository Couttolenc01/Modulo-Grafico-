import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import random

st.set_page_config(layout="wide")
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

tractos = ["--- Mostrar todos ---"] + sorted(df_filtrado["Tracto"].dropna().astype(str).unique())
tracto_seleccionado = st.selectbox("Selecciona un tracto:", tractos)

if tracto_seleccionado != "--- Mostrar todos ---":
    df_filtrado = df_filtrado[df_filtrado["Tracto"].astype(str) == tracto_seleccionado]

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

# Mostrar CPK promedio del tracto en esta ruta
if not df_filtrado.empty:
    cpk_medio = round(df_filtrado["CPK"].mean(), 2)
    st.markdown(f"**CPK promedio del tracto en esta ruta:** {cpk_medio}")

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

    color = f"#{random.randint(0, 0xFFFFFF):06x}"

    folium.PolyLine(
        ruta,
        color=color,
        weight=3 if mostrar_todas_rutas else 4,
        opacity=0.4 if mostrar_todas_rutas else 0.9,
        tooltip=f"Tracto: {row['Tracto']}"
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
        tooltip=f"Destino - Tracto: {row['Tracto']}" if not mostrar_todas_rutas else None
    ).add_to(m)

st_folium(m, returned_objects=[], height=500, width=1200)
st.markdown("### Resumen de rutas visualizadas", unsafe_allow_html=True)

# Mostrar tabla resumen de las rutas visualizadas
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
df_resumen = df_filtrado[columnas_validas].sort_values(by="CPK", ascending=False)

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

# Aplicar resaltado condicional a filas con CPK alto
def resaltar_cpk_alto(row):
    if "CPK" in row and row["CPK"] > 1000:
        return ['background-color: #fff3cd'] * len(row)  # color amarillo claro
    else:
        return [''] * len(row)

if not df_resumen.empty:
    st.dataframe(
        df_resumen.style.apply(resaltar_cpk_alto, axis=1),
        use_container_width=True
    )

# Mostrar resumen agrupado por Tracto y Ruta
st.markdown("### Resumen promedio por Tracto y Ruta")

df_agrupado = df_filtrado.groupby(["Tracto", "Ruta Estados"]).agg({
    "CPK": "mean",
    "kmstotales": "sum"
}).reset_index()
df_agrupado["CPK"] = df_agrupado["CPK"].round(2)
df_agrupado["kmstotales"] = df_agrupado["kmstotales"].round(2)
st.dataframe(df_agrupado, use_container_width=True)