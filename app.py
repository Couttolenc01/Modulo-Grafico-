import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

st.markdown(
    """
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
    .main {
        background-color: #fbfbfb;
    }
    body, .reportview-container {
        color: #193a73;
    }
    h1, h2, h3, h4 {
        color: #193a73;
    }
    .stSelectbox > div > div {
        background-color: white;
        color: #193a73;
    }
    .stSelectbox label {
        color: #193a73;
    }
    .stButton button {
        background-color: #fbc408;
        color: black;
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
    """,
    unsafe_allow_html=True
)
st.markdown("<h1 style='color:#193a73; font-size: 2.8rem; font-weight: 700;'>Visualización de Rutas por Tractos</h1>", unsafe_allow_html=True)


# Leer el archivo Excel con caché
@st.cache_data
def cargar_datos():
    return pd.read_excel("Base_final.xlsx")

df = cargar_datos()
ciudad_origen = st.selectbox("Selecciona ciudad de origen:", ["--- Mostrar todas ---"] + sorted(df["Ciudad Origen"].dropna().unique()))
ciudad_destino = st.selectbox("Selecciona ciudad de destino:", ["--- Mostrar todas ---"] + sorted(df["Ciudad Destino"].dropna().unique()))

# Crear columna combinada de ruta ciudad
df["Ruta Ciudad"] = df["Ciudad Origen"].astype(str).str.strip() + " - " + df["Ciudad Destino"].astype(str).str.strip()

df["Ciudad Origen"] = df["Ciudad Origen"].astype(str).str.strip()
df["Ciudad Destino"] = df["Ciudad Destino"].astype(str).str.strip()

# Asegurar que kmstotales no sea 0 ni NaN
df = df[df["kmstotales"].notna() & (df["kmstotales"] > 0)]

# Calcular Costo Total y CPK
df["Costo Total"] = df["Costo por carga"] + df["Costo Peajes"] + df["Costo Mantenimiento"]
df["CPK"] = df["Costo Total"] / df["kmstotales"]


if ciudad_origen != "--- Mostrar todas ---" and ciudad_destino != "--- Mostrar todas ---":
    df_filtrado = df[
        (df["Ciudad Origen"] == ciudad_origen) &
        (df["Ciudad Destino"] == ciudad_destino)
    ]
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron tractos que hayan realizado esta ruta. Verifica que exista en los datos.")
        st.stop()
elif ciudad_origen != "--- Mostrar todas ---":
    df_filtrado = df[df["Ciudad Origen"] == ciudad_origen]
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron tractos que hayan realizado esta ruta. Verifica que exista en los datos.")
        st.stop()
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

# Crear mapa centrado en México con estilo moderno
m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, tiles="OpenStreetMap")

# Agregar trayectos al mapa
if tracto_seleccionado == "--- Mostrar todos ---":
    mostrar_todas_rutas = True
else:
    mostrar_todas_rutas = False

for _, row in df_rutas.iterrows():
    destino = [row["lat_destino"], row["lon_destino"]]
    origen = [row["lat_origen"], row["lon_origen"]]
    ruta = [origen, destino]

    cpk = row["CPK"]
    if cpk < 5:
        color = "green"
    elif cpk < 10:
        color = "orange"
    else:
        color = "red"

    tooltip_text = f"Tracto: {row['Tracto']}<br>Ruta: {row['Ruta Estados']}<br>CPK: {row['CPK']:.2f}"
    tooltip_style = ""
    folium.PolyLine(
        ruta,
        color=color,
        weight=3,
        opacity=0.4 if mostrar_todas_rutas else 0.9,
        tooltip=folium.Tooltip(tooltip_text, style=tooltip_style)
    ).add_to(m)

    color_circle = "green"

    folium.CircleMarker(
        location=origen,
        radius=4 if mostrar_todas_rutas else 6,
        color=color_circle,
        fill=True,
        fill_opacity=0.6 if mostrar_todas_rutas else 0.9,
        tooltip="Origen" if not mostrar_todas_rutas else None
    ).add_to(m)

    folium.CircleMarker(
        location=destino,
        radius=6 if not mostrar_todas_rutas else 4,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.9 if not mostrar_todas_rutas else 0.6,
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

    import altair as alt

    # Filtrar para la ruta seleccionada, o usar todos si no se seleccionó una ruta específica
    df_ruta_sin_tracto = df[
        (df["Ciudad Origen"] == ciudad_origen) &
        (df["Ciudad Destino"] == ciudad_destino)
    ] if ciudad_origen != "--- Mostrar todas ---" and ciudad_destino != "--- Mostrar todas ---" else df

    df_ruta_sin_tracto = df_ruta_sin_tracto[df_ruta_sin_tracto["CPK"].notna()]

    if not df_ruta_sin_tracto.empty and "Tracto" in df_ruta_sin_tracto.columns:
        # Ordenar por CPK descendente, luego obtener el primer registro por tracto (el de mayor CPK), y luego tomar los 5 mayores
        top5 = (
            df_ruta_sin_tracto
            .sort_values("CPK", ascending=False)
            .groupby("Tracto", as_index=False)
            .first()
            .nlargest(5, "CPK")
        )

        # Calcular el número real de tractos mostrados en el gráfico
        num_tractos_top = len(top5)

        # Construir etiqueta de ruta para el título
        route_label = f"{ciudad_origen} - {ciudad_destino}" if ciudad_origen != "--- Mostrar todas ---" and ciudad_destino != "--- Mostrar todas ---" else ""
        chart = alt.Chart(top5).mark_bar().encode(
            x=alt.X("Tracto:N", title="Tracto"),
            y=alt.Y("CPK:Q", title="CPK", scale=alt.Scale(nice=True)),
            color=alt.value("#fbc408")
        ).properties(
            title=f"Top {num_tractos_top} tractos con mayor CPK en esta ruta ({route_label})",
            width=500,
            height=300
        )
        st.altair_chart(chart, use_container_width=True)