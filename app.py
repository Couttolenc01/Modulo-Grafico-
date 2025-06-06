import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Visualización de Rutas por Tractos")

# Leer el archivo Excel
df = pd.read_excel("Base_final.xlsx")

# Asegurar que kmstotales no sea 0 ni NaN
df = df[df["kmstotales"].notna() & (df["kmstotales"] > 0)]

# Calcular Costo Total y CPK
df["Costo Total"] = df["Costo por carga"] + df["Costo Peajes"] + df["Costo Mantenimiento"]
df["CPK"] = df["Costo Total"] / df["kmstotales"]

# 👉 Crear selector de estado basado en "Estado Origen"
estados = sorted(df["Estado Origen"].dropna().unique())
estado_seleccionado = st.selectbox("Selecciona un estado de origen:", estados)


# Filtrar por estado seleccionado
df_filtrado = df[df["Estado Origen"] == estado_seleccionado]

tractos = ["--- Mostrar todos ---"] + sorted(df_filtrado["Tracto"].dropna().astype(str).unique())
tracto_seleccionado = st.selectbox("Selecciona un tracto:", tractos)

from streamlit_folium import st_folium
import folium

# Filtrar por tracto seleccionado
if tracto_seleccionado != "--- Mostrar todos ---":
    df_filtrado = df_filtrado[df_filtrado["Tracto"].astype(str) == tracto_seleccionado]

# Filtrar filas con valores válidos en CPK y kmstotales
df_filtrado = df_filtrado[df_filtrado["CPK"].notna() & df_filtrado["kmstotales"].notna()]

# Obtener rutas únicas y limpiar CPK inválido
df_rutas = df_filtrado[["lat_destino", "lon_destino", "lat_origen", "lon_origen", "Ruta Estados", "Tracto", "CPK"]]
df_rutas = df_rutas[df_rutas["CPK"].notna() & (df_rutas["CPK"] != float("inf"))]

# Verificar si hay rutas con coordenadas faltantes
rutas_invalidas = df_rutas[df_rutas[["lat_origen", "lon_origen", "lat_destino", "lon_destino"]].isna().any(axis=1)]
if not rutas_invalidas.empty:
    st.warning("⚠️ Existen rutas con coordenadas faltantes que no se mostrarán en el mapa. Esto puede deberse a errores u omisiones en el registro de datos.")


df_rutas = df_rutas.dropna(subset=["lat_origen", "lon_origen", "lat_destino", "lon_destino"])

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
for _, row in df_rutas.iterrows():
    destino = [row["lat_destino"], row["lon_destino"]]
    origen = [row["lat_origen"], row["lon_origen"]]
    ruta = [origen, destino]

    folium.PolyLine(
        ruta,
        color="blue",
        weight=3,
        opacity=0.7,
        tooltip=f"Tracto: {row['Tracto']}<br>Ruta: {row['Ruta Estados']}<br>CPK: {row['CPK']:.2f}"
    ).add_to(m)

    folium.CircleMarker(
        location=origen,
        radius=5,
        color="green",
        fill=True,
        fill_opacity=0.8,
        tooltip="Origen"
    ).add_to(m)

    folium.Marker(
        location=destino,
        icon=folium.Icon(color="red", icon="remove"),
        tooltip="Destino"
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
