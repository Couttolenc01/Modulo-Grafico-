import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Visualización de Rutas por Tracto (CPK Heatmap)")

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

# Obtener rutas únicas y limpiar CPK inválido
df_rutas = df_filtrado[["lat_origen", "lon_origen", "lat_destino", "lon_destino", "Ruta Estados", "CPK"]]
df_rutas = df_rutas[df_rutas["CPK"].notna() & (df_rutas["CPK"] != float("inf"))].drop_duplicates()

# Crear figura
fig = go.Figure()
cpk_max = df_rutas["CPK"].max()
cpk_min = df_rutas["CPK"].min()

for _, row in df_rutas.iterrows():
    color_val = (row["CPK"] - cpk_min) / (cpk_max - cpk_min)
    color_val = max(0, min(1, color_val))  # asegurar rango válido
    color = f"rgba({int(255 * color_val)}, 0, {int(255 * (1 - color_val))}, 0.8)"
    
    fig.add_trace(go.Scattergeo(
        lon=[row["lon_origen"], row["lon_destino"]],
        lat=[row["lat_origen"], row["lat_destino"]],
        mode="lines",
        line=dict(width=2, color=color),
        hoverinfo="text",
        text=f"Ruta: {row['Ruta Estados']}<br>CPK: {row['CPK']:.2f}"
    ))

# Mostrar solo México (ajuste de límites del mapa)
fig.update_geos(
    resolution=50,
    showland=True,
    landcolor="rgb(240, 240, 240)",
    showcountries=True,
    countrycolor="Black",
    fitbounds="locations",
    lonaxis_range=[-118, -86],  # México
    lataxis_range=[14, 33]
)

fig.update_layout(height=600, margin={"r":0,"t":30,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)