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

tractos = ["--- Mostrar todos ---"] + sorted(df_filtrado["Tracto"].dropna().astype(str).unique())
tracto_seleccionado = st.selectbox("Selecciona un tracto:", tractos)

if tracto_seleccionado != "--- Mostrar todos ---":
    df_filtrado = df_filtrado[df_filtrado["Tracto"].astype(str) == tracto_seleccionado]

# Filtrar filas con valores válidos en CPK y kmstotales
df_filtrado = df_filtrado[df_filtrado["CPK"].notna() & df_filtrado["kmstotales"].notna()]

# Obtener rutas únicas y limpiar CPK inválido
df_rutas = df_filtrado[["lat_origen", "lon_origen", "lat_destino", "lon_destino", "Ruta Estados", "Tracto", "CPK"]]
df_rutas = df_rutas[df_rutas["CPK"].notna() & (df_rutas["CPK"] != float("inf"))]

# Crear figura
fig = go.Figure()
cpk_max = df_rutas["CPK"].max()
cpk_min = df_rutas["CPK"].min()

# Evitar división entre cero
rango_cpk = cpk_max - cpk_min
if rango_cpk == 0:
    rango_cpk = 1  # evita división por cero más adelante

for _, row in df_rutas.iterrows():
    if not (-118 <= row["lon_origen"] <= -86 and 14 <= row["lat_origen"] <= 33):
        continue
    if not (-118 <= row["lon_destino"] <= -86 and 14 <= row["lat_destino"] <= 33):
        continue

    color_val = (row["CPK"] - cpk_min) / rango_cpk
    color_val = max(0, min(1, color_val))  # asegurar rango válido
    color = f"rgba({int(255 * color_val)}, 0, {int(255 * (1 - color_val))}, 0.8)"
    
    fig.add_trace(go.Scattergeo(
        lon=[row["lon_origen"], row["lon_destino"]],
        lat=[row["lat_origen"], row["lat_destino"]],
        mode="lines",
        line=dict(width=2, color=color),
        hoverinfo="text",
        name=f"Ruta: {row['Ruta Estados']} (CPK: {row['CPK']:.2f})",
        text=f"Ruta: {row['Ruta Estados']}<br>CPK: {row['CPK']:.2f}"
    ))

    fig.add_trace(go.Scattergeo(
        lon=[row["lon_origen"]],
        lat=[row["lat_origen"]],
        mode="markers+text",
        marker=dict(size=6, color="green", symbol="circle"),
        text="Origen",
        textposition="top center",
        hoverinfo="skip",
        showlegend=False
    ))

    fig.add_trace(go.Scattergeo(
        lon=[row["lon_destino"]],
        lat=[row["lat_destino"]],
        mode="markers+text",
        marker=dict(size=6, color="red", symbol="x"),
        text="Destino",
        textposition="bottom center",
        hoverinfo="skip",
        showlegend=False
    ))

# Mostrar solo México (ajuste de límites del mapa)
fig.update_geos(
    resolution=50,
    showland=True,
    landcolor="rgb(240, 240, 240)",
    showcountries=True,
    countrycolor="Black",
    showcoastlines=True,
    lonaxis_range=[-118, -86],  # México
    lataxis_range=[14, 33]
)

fig.update_layout(height=600, margin={"r":0,"t":30,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# Mostrar tabla resumen de las rutas visualizadas
st.markdown("### Resumen de rutas visualizadas")
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

if "Tracto" in df_filtrado.columns and "Ruta Estados" in df_filtrado.columns:
    df_agrupado = df_filtrado.groupby(["Tracto", "Ruta Estados"]).agg({
        "CPK": "mean",
        "kmstotales": "sum"
    }).reset_index()
    df_agrupado["CPK"] = df_agrupado["CPK"].round(2)
    df_agrupado["kmstotales"] = df_agrupado["kmstotales"].round(2)
    st.dataframe(df_agrupado, use_container_width=True)
