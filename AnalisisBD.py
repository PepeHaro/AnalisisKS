import streamlit as st
import pandas as pd
import altair as alt
from sklearn.linear_model import LinearRegression
from datetime import datetime
import numpy as np

# Título de la aplicación
st.title("ANÁLISIS DE VENTAS MANUFACTURA KONCEPT")

# Barra lateral para la selección de pestañas
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una pestaña:",
    ["Análisis Ventas", "Análisis Productos"]
)

# Subir archivo CSV solo si se seleccionó una opción
if opcion in ["Análisis Ventas", "Análisis Productos"]:
    st.markdown(f"#### Subir archivo CSV para {opcion}")
    uploaded_file = st.file_uploader("Elige un archivo CSV", type="csv")

    if uploaded_file is not None:
        try:
            # Intentar cargar datos con utf-8
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Si hay un error, intentar con otro encoding
            df = pd.read_csv(uploaded_file, encoding='latin1')

        # Manejo de datos faltantes
        df.fillna(0, inplace=True)  # Rellena los valores nulos con 0

        # Normalización de nombres de clientes
        cliente_mapeo = {
            'Interceramic': 'Interceramic',
            'Home Depot': 'Home Depot',
            'Daltile': 'Daltile',
            'Kolher': 'Kolher',
            'Cesantoni': 'Cesantoni',
            'USA': 'USA',
            'Lamosa': 'Lamosa',
            'Vitromex': 'Vitromex',
            'Varios': 'Varios',
            'Tenerife': 'Tenerife',
            'Tendenzza': 'Tendenzza'
        }

        # Convertir nombres de clientes a formato estándar
        df['Cliete'] = df['Cliete'].str.strip().str.title()
        df['Cliete'] = df['Cliete'].map(cliente_mapeo).fillna(df['Cliete'])

        # Asegurarse de que las columnas Año y Mes sean de tipo string
        df["Año"] = df["Año"].astype(str)
        df["Mes"] = df["Mes"].astype(str)

        # Asegurarse de que la columna Importe sea numérica
        df["Importe"] = pd.to_numeric(df["Importe"], errors='coerce').fillna(0)

        # Formatear la columna Importe con comas como separadores de miles sin decimales
        df["Importe_formateado"] = df["Importe"].apply(lambda x: "{:,.0f}".format(x))

        # Normalización de SKUs
        def normalizar_sku(sku):
            if isinstance(sku, str):  # Asegurarse de que el SKU sea una cadena
                return sku.strip().upper()
            return sku

        df['SKU'] = df['SKU'].apply(normalizar_sku)

        # Encontrar el último año y mes en el conjunto de datos
        ultimo_año = df["Año"].max()
        ultimo_mes = df[df["Año"] == ultimo_año]["Mes"].max()


# Título de la aplicación
st.title("ANÁLISIS DE VENTAS MANUFACTURA KONCEPT")

# Barra lateral para la selección de pestañas
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una pestaña:",
    ["Análisis Ventas", "Análisis Productos"]
)

# Subir archivo CSV solo si se seleccionó una opción
if opcion in ["Análisis Ventas", "Análisis Productos"]:
    st.markdown(f"#### Subir archivo CSV para {opcion}")
    uploaded_file = st.file_uploader("Elige un archivo CSV", type="csv")

    if uploaded_file is not None:
        try:
            # Intentar cargar datos con utf-8
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Si hay un error, intentar con otro encoding
            df = pd.read_csv(uploaded_file, encoding='latin1')

        # Manejo de datos faltantes
        df.fillna(0, inplace=True)  # Rellena los valores nulos con 0

        # Normalización de nombres de clientes
        cliente_mapeo = {
            'Interceramic': 'Interceramic',
            'Home Depot': 'Home Depot',
            'Daltile': 'Daltile',
            'Kolher': 'Kolher',
            'Cesantoni': 'Cesantoni',
            'USA': 'USA',
            'Lamosa': 'Lamosa',
            'Vitromex': 'Vitromex',
            'Varios': 'Varios',
            'Tenerife': 'Tenerife',
            'Tendenzza': 'Tendenzza'
        }

        # Convertir nombres de clientes a formato estándar
        df['Cliete'] = df['Cliete'].str.strip().str.title()
        df['Cliete'] = df['Cliete'].map(cliente_mapeo).fillna(df['Cliete'])

        # Asegurarse de que las columnas Año y Mes sean de tipo string
        df["Año"] = df["Año"].astype(str)
        df["Mes"] = df["Mes"].astype(str)

        # Asegurarse de que la columna Importe sea numérica
        df["Importe"] = pd.to_numeric(df["Importe"], errors='coerce').fillna(0)

        # Formatear la columna Importe con comas como separadores de miles sin decimales
        df["Importe_formateado"] = df["Importe"].apply(lambda x: "{:,.0f}".format(x))

        # Normalización de SKUs
        def normalizar_sku(sku):
            if isinstance(sku, str):  # Asegurarse de que el SKU sea una cadena
                return sku.strip().upper()
            return sku

        df['SKU'] = df['SKU'].apply(normalizar_sku)

        # Encontrar el último año y mes en el conjunto de datos
        ultimo_año = df["Año"].max()
        ultimo_mes = df[df["Año"] == ultimo_año]["Mes"].max()