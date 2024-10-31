import streamlit as st
import pandas as pd
import altair as alt
from sklearn.linear_model import LinearRegression
from datetime import datetime
import numpy as np
import sqlite3


# Función para cargar el nombre real del cliente desde secrets sin mostrar un error en pantalla
def get_cliente_name(identifier):
    try:
        return st.secrets["clientes"][identifier]
    except KeyError:
        # Registra un mensaje de error solo en los logs y retorna un valor por defecto
        return "Cliente desconocido"

# Título de la aplicación
st.title("ANÁLISIS MKkkk")

# Barra lateral para la selección de pestañas
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una pestaña:",
    ["Sales Analysis", "SKU's Analysis"]
)

# Mostrar la opción de subir archivo solo si se seleccionó una opción válida
if opcion in ["Sales Analysis", "SKU's Analysis"]:
    st.markdown(f"#### Subir archivo CSV para {opcion}")
    uploaded_file = st.file_uploader("Elige un archivo CSV", type="csv")
    
    # Procesar el archivo si se ha subido
    if uploaded_file is not None:
        try:
            # Intentar cargar datos con utf-8
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Si hay un error, intentar con otro encoding
            df = pd.read_csv(uploaded_file, encoding='latin1')

        # Manejo de datos faltantes
        df.fillna(0, inplace=True)  # Rellena los valores nulos con 0

        # Generar el mapeo dinámicamente desde secrets
        cliente_mapeo = {f'C{i+1}': get_cliente_name(f'C{i+1}') for i in range(11)}

        # Convertir nombres de clientes en el DataFrame a formato estándar
        df['Cliente'] = df['Cliente'].str.strip().str.title()  # Normaliza espacios y mayúsculas
        df['Cliente'] = df['Cliente'].map(cliente_mapeo).fillna(df['Cliente'])

        # Asegurarse de que las columnas Año y Mes sean de tipo string
        # Convertir la columna "Año" a numérico, ignorando errores y manejando valores nulos
        df["Año"] = pd.to_numeric(df["Año"], errors='coerce').fillna(0).astype(int).astype(str)
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

    st.write("---")
    if opcion == "Sales Analysis":
        # Gráfico de líneas de ventas totales por año
        st.subheader(f"VENTAS TOTALES POR AÑO:chart_with_upwards_trend:")
        ventas_totales = df.groupby("Año", as_index=False)["Importe"].sum()
        ventas_totales["Importe_formateado"] = ventas_totales["Importe"].apply(lambda x: "{:,.0f}".format(x))

        line_chart = alt.Chart(ventas_totales).mark_line(color='green').encode(
            x=alt.X('Año:O', title='Año'),
            y=alt.Y('Importe:Q', title='Importe Total'),
            tooltip=['Año', 'Importe_formateado']
        ).properties(
            title=(f"(Hasta {ultimo_mes}/{ultimo_año})")
        )

        # Añadir puntos en la gráfica de líneas
        line_points = line_chart.mark_point(color='green', size=60)

        # Añadir etiquetas de texto en los puntos
        line_text = line_chart.mark_text(
            align='left',
            baseline='middle',
            dx=7  # Desplaza el texto hacia la derecha
        ).encode(
            text='Importe_formateado:N'
        )

        # Mostrar gráfico
        st.altair_chart(line_chart + line_points + line_text, use_container_width=True)

        st.write("---")
        # Selección de cliente
        st.subheader("FLUCTUACIONES DE VENTAS POR CLIENTE:bar_chart:")
        cliente_seleccionado = st.selectbox("Selecciona un cliente", df["Cliente"].unique())

        # Filtrar datos por cliente seleccionado
        df_cliente = df[df["Cliente"] == cliente_seleccionado]

        # Agrupar las ventas por año utilizando la columna Importe
        ventas_cliente = df_cliente.groupby("Año", as_index=False)["Importe"].sum()
        ventas_cliente["Importe_formateado"] = ventas_cliente["Importe"].apply(lambda x: "{:,.0f}".format(x))

        # Crear gráfico de barras para mostrar la fluctuación anual de ventas
        bars = alt.Chart(ventas_cliente).mark_bar().encode(
            x=alt.X('Año:O', title='Año'),
            y=alt.Y('Importe:Q', title='Importe Total'),
            color=alt.Color('Año:O', legend=None)
        ).properties(
            title=f'Fluctuación de Ventas de {cliente_seleccionado} por Año'
        )

        # Añadir etiquetas de texto en las barras
        text = bars.mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Desplaza el texto hacia arriba
        ).encode(
            text='Importe_formateado:N'
        )

        # Mostrar gráfico
        st.altair_chart(bars + text, use_container_width=True)

        st.write("---")
        # Selección de años para comparación
        st.subheader("COMPARATIVA DE VENTAS ENTRE AÑOS:signal_strength:")
        cliente_comparativa = st.selectbox("Selecciona el cliente para la comparativa", df["Cliente"].unique())
        años_disponibles = df["Año"].unique()
        año_seleccionado_1 = st.selectbox("Selecciona el primer año", años_disponibles)
        año_seleccionado_2 = st.selectbox("Selecciona el segundo año", años_disponibles)

        if año_seleccionado_1 and año_seleccionado_2:
            # Filtrar datos por cliente seleccionado para comparación
            df_comparativa_cliente = df[df["Cliente"] == cliente_comparativa]

            # Filtrar datos por años seleccionados
            df_año_1 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_1].groupby("Cliente")["Importe"].sum().reset_index()
            df_año_2 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_2].groupby("Cliente")["Importe"].sum().reset_index()

            # Crear un DataFrame para la comparación
            df_comparativa = pd.DataFrame({
                'Cliente': [cliente_comparativa] * 2,
                'Año': [año_seleccionado_1, año_seleccionado_2],
                'Importe': [df_año_1['Importe'].sum(), df_año_2['Importe'].sum()]
            })

            # Formatear la columna Importe
            df_comparativa["Importe_formateado"] = df_comparativa["Importe"].apply(lambda x: "{:,.0f}".format(x))

            # Crear gráfico de barras para la comparativa de ventas entre dos años
            comparativa_barras = alt.Chart(df_comparativa).mark_bar().encode(
                x=alt.X('Año:O', title='Año'),
                y=alt.Y('Importe:Q', title='Importe Total'),
                color=alt.Color('Año:O', legend=None),
                text='Importe_formateado:N'
            ).properties(
                title=f'Comparativa de Ventas entre {año_seleccionado_1} y {año_seleccionado_2}'
            )

            # Añadir etiquetas de texto en las barras
            comparativa_text = comparativa_barras.mark_text(
                align='center',
                baseline='middle',
                dy=-10  # Desplaza el texto hacia arriba
            ).encode(
                text='Importe_formateado:N'
            )

            # Mostrar gráficos comparativos
            st.altair_chart(comparativa_barras + comparativa_text, use_container_width=True)

        st.write("---")
        # Selección de año para ventas por mes
        st.subheader("VENTAS POR MES:calendar:")

        # Añadir la opción "Todos los años" al selectbox
        años_disponibles = ["Todos los años"] + list(df["Año"].unique())
        año_seleccionado = st.selectbox("Selecciona el año para comparar", años_disponibles)

        if año_seleccionado:
            if año_seleccionado == "Todos los años":
                # Multiselect para elegir los años específicos a mostrar
                años_elegidos = st.multiselect("Selecciona los años que deseas visualizar", df["Año"].unique(), default=df["Año"].unique())

                # Filtrar el DataFrame según los años seleccionados
                df_mes = df[df["Año"].isin(años_elegidos)]
            else:
                # Filtrar datos por el año seleccionado
                df_mes = df[df["Año"] == año_seleccionado]

            # Asegurarse de que la columna Mes esté en formato numérico
            df_mes["Mes"] = pd.to_numeric(df_mes["Mes"], errors='coerce')

            # Agrupar ventas por mes y año
            ventas_mes = df_mes.groupby(["Año", "Mes"], as_index=False)["Importe"].sum()

            # Asegurarse de que todos los meses estén presentes para cada año, incluso si no hay datos
            meses_completos = pd.DataFrame({
                'Mes': list(range(1, 13))  # Meses del 1 al 12
            })

            # Crear una lista para almacenar los DataFrames de cada año con los meses completos
            df_completo = pd.DataFrame()
            for año in ventas_mes["Año"].unique():
                ventas_año = ventas_mes[ventas_mes["Año"] == año]
                ventas_año = pd.merge(meses_completos, ventas_año, on="Mes", how="left").fillna({"Importe": 0})
                ventas_año["Año"] = año  # Asegurar que la columna "Año" esté presente
                df_completo = pd.concat([df_completo, ventas_año], ignore_index=True)

            # Asegurarse de que la columna Importe sea de tipo numérico
            df_completo["Importe"] = df_completo["Importe"].astype(float)

            # Formatear la columna Importe
            df_completo["Importe_formateado"] = df_completo["Importe"].apply(lambda x: "{:,.0f}".format(x))

            # Crear gráfico de líneas para mostrar ventas por mes, con una línea por cada año
            line_chart = alt.Chart(df_completo).mark_line().encode(
                x=alt.X('Mes:O', title='Mes', axis=alt.Axis(format='d')),
                y=alt.Y('Importe:Q', title='Importe Total'),
                color=alt.Color('Año:N', title='Año'),  # Diferenciar las líneas por color según el año
                tooltip=['Año', 'Mes', 'Importe_formateado']
            ).properties(
                title="Ventas por Mes" if año_seleccionado == "Todos los años" else f'Ventas por Mes en {año_seleccionado}'
            )

            # Añadir puntos en las líneas
            line_points = line_chart.mark_point(size=50)

            # Añadir etiquetas de texto en los puntos
            line_text = line_chart.mark_text(
                align='left',
                baseline='middle',
                dx=7  # Desplaza el texto hacia la derecha
            ).encode(
                text='Importe_formateado:N'
            )

            # Mostrar gráfico
            st.altair_chart(line_chart + line_points + line_text, use_container_width=True)
            

        # Selección de años para analizar porcentaje de ventas por cliente
        st.subheader("Porcentaje de Ventas por Cliente :pie_chart:")
        años_seleccionados = st.multiselect("Selecciona el/los año(s) para el análisis", df["Año"].unique(), default=df["Año"].unique())

        # Filtrar los datos según los años seleccionados
        df_filtrado = df[df["Año"].isin(años_seleccionados)]

        # Calcular el total de ventas por cliente
        ventas_por_cliente = df_filtrado.groupby("Cliente")["Importe"].sum().reset_index()
        ventas_por_cliente["Porcentaje"] = (ventas_por_cliente["Importe"] / ventas_por_cliente["Importe"].sum()) * 100

        # Crear gráfica de pastel para mostrar el porcentaje de ventas por cliente
        pie_chart = alt.Chart(ventas_por_cliente).mark_arc().encode(
            theta=alt.Theta(field="Importe", type="quantitative"),
            color=alt.Color(field="Cliente", type="nominal", title="Cliente"),
            tooltip=[alt.Tooltip("Cliente:N", title="Cliente"), alt.Tooltip("Porcentaje:Q", format=".2f", title="% de Ventas")]
        ).properties(
            title="Distribución de Ventas por Cliente"
        )

        # Mostrar gráfico
        st.altair_chart(pie_chart, use_container_width=True)


    elif opcion == "SKU's Analysis":
        st.markdown("## PRODUCTOS VENDIDOS :gear:")
        # Agregar opción "Todos los clientes" al selectbox de cliente
        clientes_unicos = list(df["Cliente"].unique())
        clientes_unicos.insert(0, "Todos los clientes")

        # Selección de cliente para análisis de productos
        cliente_seleccionado_producto = st.selectbox("Selecciona un cliente para el análisis de productos", clientes_unicos)

        # Selección de año para análisis de productos
        año_seleccionado_producto = st.selectbox("Selecciona el año para el análisis de productos", df["Año"].unique())

        # Ingresar cantidad de productos a mostrar
        cantidad_productos = st.number_input("Cantidad de productos a mostrar", min_value=1, max_value=50, value=20, step=1)

        if cliente_seleccionado_producto and año_seleccionado_producto:
            if cliente_seleccionado_producto == "Todos los clientes":
                # Filtrar datos solo por año seleccionado
                df_producto = df[df["Año"] == año_seleccionado_producto]
            else:
                # Filtrar datos por cliente y año seleccionados
                df_producto = df[(df["Cliente"] == cliente_seleccionado_producto) & (df["Año"] == año_seleccionado_producto)]

            # Asegurarse de que la columna "Cantidad" sea numérica
            df_producto["Cantidad"] = pd.to_numeric(df_producto["Cantidad"], errors='coerce')

            # Calcular el total de ventas del año seleccionado
            total_ventas = df_producto["Importe"].sum()
            total_ventas_formateado = "{:,.0f}".format(total_ventas)

            # Agrupar ventas por SKU y Producto, uniendo productos con el mismo SKU y sumando cantidades correctamente
            ventas_producto = df_producto.groupby(["SKU", "Producto"], as_index=False).agg(
                {"Cantidad": "sum", "Importe": "sum"}
            )
            ventas_producto["Importe_formateado"] = ventas_producto["Importe"].apply(lambda x: "{:,.0f}".format(x))

            # Ordenar y seleccionar la cantidad de productos más vendidos especificados por el usuario
            ventas_producto = ventas_producto.sort_values(by="Importe", ascending=False).head(cantidad_productos)

            # Calcular la suma de ventas de los productos seleccionados
            suma_ventas_top = ventas_producto["Importe"].sum()
            suma_ventas_top_formateado = "{:,.0f}".format(suma_ventas_top)

            # Calcular el porcentaje de la suma de ventas top respecto al total
            porcentaje_ventas_top = (suma_ventas_top / total_ventas) * 100
            porcentaje_ventas_top_formateado = "{:.2f}%".format(porcentaje_ventas_top)

            # Calcular el porcentaje de ventas que representan del total
            ventas_producto["Porcentaje"] = (ventas_producto["Importe"] / total_ventas) * 100
            ventas_producto["Porcentaje_formateado"] = ventas_producto["Porcentaje"].apply(lambda x: "{:.2f}%".format(x))

            # Crear gráfico de barras para mostrar ventas por SKU y Producto
            bars_producto = alt.Chart(ventas_producto).mark_bar().encode(
                x=alt.X('Producto:O', title='Producto (SKU)', sort='-y'),
                y=alt.Y('Importe:Q', title='Importe Total'),
                color=alt.Color('Producto:O', legend=None),
                tooltip=['SKU:N', 'Producto:N', 'Cantidad:Q', 'Importe_formateado:N', 'Porcentaje_formateado:N']
            ).properties(
                title=f'Ventas por Producto en {año_seleccionado_producto} para {cliente_seleccionado_producto} - Total: {total_ventas_formateado}'
            )

            # Añadir etiquetas de texto en las barras
            text_producto = bars_producto.mark_text(
                align='center',
                baseline='middle',
                dy=-10  # Desplaza el texto hacia arriba
            ).encode(
                text='Importe_formateado:N'
            )

            # Mostrar gráfico
            st.altair_chart(bars_producto + text_producto, use_container_width=True)

            # Mostrar tabla con SKU, Cantidad, Importe y Porcentaje
            st.write(f"### Detalle de Productos Vendidos - Suma de Ventas: {suma_ventas_top_formateado} ({porcentaje_ventas_top_formateado})")
            st.dataframe(ventas_producto[['SKU', 'Producto', 'Cantidad', 'Importe_formateado', 'Porcentaje_formateado']])

            st.write("---")
            # Comparativa por año
            st.write("## COMPARATIVA POR AÑO	:clipboard:")

            # Selección de cliente para comparativa por año
            cliente_comparativa = st.selectbox("Selecciona un cliente para la comparativa por año", clientes_unicos, key="cliente_comparativa")

            # Selección de años para comparativa
            años_comparativa = st.multiselect("Selecciona los años para la comparativa", sorted(df["Año"].unique()), key="años_comparativa")

            # Selección de SKUs para comparativa
            # Normalizar SKUs: convertir a mayúsculas y eliminar espacios en blanco
            skus_comparativa = df["SKU"].astype(str).apply(normalizar_sku).unique()
            skus_comparativa = sorted(set(skus_comparativa))  # Eliminar duplicados
            skus_seleccionados = st.multiselect("Selecciona los SKUs para la comparativa", skus_comparativa, key="skus_comparativa")

            if cliente_comparativa and años_comparativa and skus_seleccionados:
                if cliente_comparativa == "Todos los clientes":
                    # Filtrar datos solo por los años seleccionados y SKUs especificados
                    df_comparativa = df[(df["Año"].isin(años_comparativa)) & (df["SKU"].isin(skus_seleccionados))]
                else:
                    # Filtrar datos por cliente, años seleccionados y SKUs especificados
                    df_comparativa = df[(df["Cliente"] == cliente_comparativa) & (df["Año"].isin(años_comparativa)) & (df["SKU"].isin(skus_seleccionados))]

                # Agrupar ventas por año y SKU, sumando importe correctamente
                ventas_comparativa = df_comparativa.groupby(["Año", "SKU"], as_index=False).agg(
                    {"Importe": "sum"}
                )
                ventas_comparativa["Importe_formateado"] = ventas_comparativa["Importe"].apply(lambda x: "{:,.0f}".format(x))

                # Crear un DataFrame con todos los SKUs y años seleccionados para evitar valores faltantes
                skus_años = pd.MultiIndex.from_product([skus_seleccionados, años_comparativa], names=["SKU", "Año"])
                ventas_comparativa = ventas_comparativa.set_index(["SKU", "Año"]).reindex(skus_años, fill_value=0).reset_index()

                # Pivotar los datos para comparación
                comparativa_pivot = ventas_comparativa.pivot(index="SKU", columns="Año", values="Importe").reset_index()

                # Calcular diferencia porcentual entre años seleccionados
                if len(años_comparativa) > 1:
                    años_seleccionados = sorted(años_comparativa)
                    comparativa_pivot["Diferencia %"] = 0
                    for i in range(len(años_seleccionados) - 1):
                        año_1 = años_seleccionados[i]
                        año_2 = años_seleccionados[i + 1]
                        if año_1 in comparativa_pivot.columns and año_2 in comparativa_pivot.columns:
                            comparativa_pivot["Diferencia %"] = (
                                (comparativa_pivot[año_2] - comparativa_pivot[año_1]) / comparativa_pivot[año_1] * 100
                            ).fillna(0).apply(lambda x: "{:.2f}%".format(x))

                    # Renombrar columnas
                    comparativa_pivot.columns = [f'Importe {col}' if col in años_seleccionados else col for col in comparativa_pivot.columns]
                    comparativa_pivot = comparativa_pivot[['SKU'] + [f'Importe {año}' for año in años_seleccionados] + ['Diferencia %']]

                    # Mostrar tabla comparativa
                    st.write("### Tabla Comparativa de Ventas por Año")
                    st.dataframe(comparativa_pivot)
        st.write("---")
        st.markdown("## PRECIO UNITARIO POR CLIENTE	:heavy_dollar_sign:")

        # Selección de cliente para comparativa por año
        cliente_precio_unitario = st.selectbox("Selecciona un cliente para el análisis del precio unitario", clientes_unicos)

        if cliente_precio_unitario:
            # Filtrar datos por el cliente seleccionado
            df_precio_unitario = df[df["Cliente"] == cliente_precio_unitario]

            # Agrupar por SKU y Año, calculando el precio unitario promedio
            precio_unitario = df_precio_unitario.groupby(["SKU", "Año"], as_index=False).agg({"PrecioU": "mean"})

            # Pivotar el DataFrame para tener los años como columnas
            precio_unitario_pivot = precio_unitario.pivot(index='SKU', columns='Año', values='PrecioU')

            # Formatear los valores para que se muestren con el formato deseado
            precio_unitario_pivot = precio_unitario_pivot.fillna(0).applymap(lambda x: "${:,.2f}".format(x) if x > 0 else "$0.00")

            # Mostrar el DataFrame con el precio unitario
            st.write(f"### Precio Unitario por SKU para {cliente_precio_unitario}")
            st.dataframe(precio_unitario_pivot.reset_index())

            # Obtener los SKU únicos para el multiselect
            skus_unicos = precio_unitario['SKU'].unique().tolist()

            # Selección de SKU para ver precios específicos
            skus_seleccionados = st.multiselect("Selecciona uno o más SKU", options=skus_unicos)

            if skus_seleccionados:
                # Filtrar el DataFrame por los SKU seleccionados
                precios_filtrados = precio_unitario_pivot[precio_unitario_pivot.index.isin(skus_seleccionados)]
                
                # Asegurarse de que no se produzca un error por los índices
                precios_filtrados = precios_filtrados.reset_index()
                
                st.write(f"### Precios de los SKU seleccionados para {cliente_precio_unitario}")
                st.dataframe(precios_filtrados)

