import streamlit as st
import pandas as pd
import altair as alt
from sklearn.linear_model import LinearRegression
from datetime import datetime
import numpy as np
import sqlite3



# Título de la aplicación
st.title("ANÁLISIS MANUFACTURA KONCEPT")

# Barra lateral para la selección de pestañas
st.sidebar.title("Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una pestaña:",
    ["Sales Analysis", "SKU's Analysis", "Investor Analysis"]
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
        df["Año"] = df["Año"].astype(int).astype(str)
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

        # Selección de cliente
        st.subheader("FLUCTUACIONES DE VENTAS POR CLIENTE:bar_chart:")
        cliente_seleccionado = st.selectbox("Selecciona un cliente", df["Cliete"].unique())

        # Filtrar datos por cliente seleccionado
        df_cliente = df[df["Cliete"] == cliente_seleccionado]

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

        # Selección de años para comparación
        st.subheader("COMPARATIVA DE VENTAS ENTRE AÑOS:signal_strength:")
        cliente_comparativa = st.selectbox("Selecciona el cliente para la comparativa", df["Cliete"].unique())
        años_disponibles = df["Año"].unique()
        año_seleccionado_1 = st.selectbox("Selecciona el primer año", años_disponibles)
        año_seleccionado_2 = st.selectbox("Selecciona el segundo año", años_disponibles)

        if año_seleccionado_1 and año_seleccionado_2:
            # Filtrar datos por cliente seleccionado para comparación
            df_comparativa_cliente = df[df["Cliete"] == cliente_comparativa]

            # Filtrar datos por años seleccionados
            df_año_1 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_1].groupby("Cliete")["Importe"].sum().reset_index()
            df_año_2 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_2].groupby("Cliete")["Importe"].sum().reset_index()

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

        # Selección de año para ventas por mes
        st.subheader("VENTAS POR MES EN UN AÑO:calendar:")
        año_seleccionado = st.selectbox("Selecciona el año para comparar", df["Año"].unique())

        if año_seleccionado:
            # Filtrar datos por el año seleccionado
            df_mes = df[df["Año"] == año_seleccionado]

            # Asegurarse de que la columna Mes esté en formato numérico
            df_mes["Mes"] = pd.to_numeric(df_mes["Mes"], errors='coerce')

            # Agrupar ventas por mes
            ventas_mes = df_mes.groupby("Mes", as_index=False)["Importe"].sum()

            # Asegurarse de que todos los meses estén presentes, incluso si no hay datos
            meses_completos = pd.DataFrame({
                'Mes': list(range(1, 13))  # Meses del 1 al 12
            })

            # Hacer un merge para unir los meses completos con las ventas, llenando con 0 los meses faltantes
            ventas_mes = pd.merge(meses_completos, ventas_mes, on='Mes', how='left').fillna(0)

            # Asegurarse de que la columna Importe sea de tipo numérico
            ventas_mes["Importe"] = ventas_mes["Importe"].astype(float)

            # Ordenar los meses (esto debería ser redundante pero lo incluimos por seguridad)
            ventas_mes = ventas_mes.sort_values(by='Mes')

            # Formatear la columna Importe
            ventas_mes["Importe_formateado"] = ventas_mes["Importe"].apply(lambda x: "{:,.0f}".format(x))

            # Calcular el total de ventas para el año seleccionado
            total_ventas = ventas_mes["Importe"].sum()
            total_ventas_formateado = "{:,.0f}".format(total_ventas)

            # Crear gráfico de barras para mostrar ventas por mes
            bars_mes = alt.Chart(ventas_mes).mark_bar(color='#FFA07A').encode(
                x=alt.X('Mes:O', title='Mes', axis=alt.Axis(format='d')),
                y=alt.Y('Importe:Q', title='Importe Total'),
                color=alt.Color('Mes:O', legend=None),
                text='Importe_formateado:N'
            ).properties(
                title=f'Ventas por Mes en {año_seleccionado} (Total: {ventas_mes["Importe"].sum():,.0f})'
            )

            # Añadir etiquetas de texto en las barras
            text_mes = bars_mes.mark_text(
                align='center',
                baseline='middle',
                dy=-10  # Desplaza el texto hacia arriba
            ).encode(
                text='Importe_formateado:N'
            )

            # Mostrar gráfico
            st.altair_chart(bars_mes + text_mes, use_container_width=True)


    elif opcion == "SKU's Analysis":
        # Agregar opción "Todos los clientes" al selectbox de cliente
        clientes_unicos = list(df["Cliete"].unique())
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
                df_producto = df[(df["Cliete"] == cliente_seleccionado_producto) & (df["Año"] == año_seleccionado_producto)]

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

            # Comparativa por año
            st.write("## Comparativa por año")

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
                    df_comparativa = df[(df["Cliete"] == cliente_comparativa) & (df["Año"].isin(años_comparativa)) & (df["SKU"].isin(skus_seleccionados))]

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

    st.markdown("## PRECIO UNITARIO POR CLIENTE")

    # Selección de cliente para comparativa por año
    cliente_precio_unitario = st.selectbox("Selecciona un cliente para el análisis del precio unitario", clientes_unicos, key="cliente_precio_unitario")

    if cliente_precio_unitario:
        if cliente_precio_unitario == "Todos los clientes":
            # Filtrar datos para todos los clientes
            df_precio_unitario = df
        else:
            # Filtrar datos por el cliente seleccionado
            df_precio_unitario = df[df["Cliete"] == cliente_precio_unitario]

        # Agrupar por producto y calcular el precio unitario
        precio_unitario = df_precio_unitario.groupby(["SKU", "Producto"], as_index=False).agg(
            {
                "PrecioU": "mean",  # Puedes cambiar a "sum" si deseas sumar los precios
                "Cantidad": "sum"
            }
        )
        precio_unitario["PrecioU_formateado"] = precio_unitario["PrecioU"].apply(lambda x: "{:,.2f}".format(x))

        # Mostrar el DataFrame con el precio unitario
        st.write(f"### Precio Unitario por Producto para {cliente_precio_unitario}")
        st.dataframe(precio_unitario[['SKU', 'Producto', 'Cantidad', 'PrecioU_formateado']])




if opcion == "Investor Analysis":
    st.markdown(f"#### Subir datos de Odoo Actual")

    # Selector de mes
    mes = st.selectbox("Selecciona el mes de Odoo:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])

    # Cargar archivo de Odoo (CSV)
    uploaded_odoo = st.file_uploader("Subir archivo Odoo Actual (CSV)", type="csv")

    if uploaded_odoo is not None:
        try:
            df_odoo = pd.read_csv(uploaded_odoo, encoding='utf-8')
            df_odoo.columns = ["Cuenta", "Concepto", "Importe"]  # Renombrar columnas
            df_odoo = df_odoo.dropna()

            st.write("Datos limpios de Odoo Actual:")
            st.dataframe(df_odoo)

        except UnicodeDecodeError:
            st.error("Error de codificación al cargar el archivo Odoo. Intenta con otro archivo o revisa el formato.")
        except KeyError:
            st.error("Error: Las columnas 'Cuenta', 'Concepto' o 'Importe' no se encontraron en el archivo.")
        except pd.errors.EmptyDataError:
            st.error("Error: El archivo Odoo Actual está vacío.")
        except Exception as e:
            st.error(f"Error inesperado al cargar el archivo Odoo: {e}")

    st.markdown(f"#### Subir Presupuesto Anual")
    
    # Cargar archivo de Presupuesto (Excel)
    uploaded_presupuesto = st.file_uploader("Subir archivo de Presupuesto Anual (Excel)", type=["xlsx", "xls"])

    if uploaded_presupuesto is not None:
        try:
            # Cargar el archivo de presupuesto usando el motor 'openpyxl' para archivos Excel
            df_presupuesto = pd.read_excel(uploaded_presupuesto, engine='openpyxl')

            # Eliminar columnas completamente vacías
            df_presupuesto = df_presupuesto.dropna(how='all', axis=1)

            # Eliminar filas completamente vacías
            df_presupuesto = df_presupuesto.dropna(how='all', axis=0)

            # Renombrar columnas
            column_names = ["Cuenta", "Concepto", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            df_presupuesto.columns = column_names[:df_presupuesto.shape[1]]

            st.write("Datos limpios del Presupuesto Anual:")
            st.dataframe(df_presupuesto)

        except pd.errors.EmptyDataError:
            st.error("Error: El archivo de Presupuesto está vacío.")
        except Exception as e:
            st.error(f"Error inesperado al cargar el archivo de Presupuesto: {e}")