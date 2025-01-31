import streamlit as st
import pandas as pd
import altair as alt
from sklearn.linear_model import LinearRegression
from datetime import datetime
import numpy as np
import sqlite3
import seaborn as sns
import io 
import calendar



# Función para cargar el nombre real del cliente desde secrets sin mostrar un error en pantalla
def get_cliente_name(identifier):
    try:
        return st.secrets["clientes"][identifier]
    except KeyError:
        # Registra un mensaje de error solo en los logs y retorna un valor por defecto
        return "Cliente desconocido"

# Título de la aplicación
st.title("ANÁLISIS MK")

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
        
       # Código original: Comparativa de ventas entre años
        st.subheader("COMPARATIVA DE VENTAS ENTRE AÑOS:signal_strength:")
        cliente_comparativa = st.selectbox("Selecciona el cliente para la comparativa", df["Cliente"].unique(), key="comparativa_cliente")
        años_disponibles = df["Año"].unique()
        año_seleccionado_1 = st.selectbox("Selecciona el primer año", años_disponibles, key="año_1")
        año_seleccionado_2 = st.selectbox("Selecciona el segundo año", años_disponibles, key="año_2")

        if año_seleccionado_1 and año_seleccionado_2:
            # Filtrar datos por cliente seleccionado para comparación
            df_comparativa_cliente = df[df["Cliente"] == cliente_comparativa]

            # Filtrar datos por años seleccionados
            df_año_1 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_1].groupby("Cliente")["Importe"].sum().reset_index()
            df_año_2 = df_comparativa_cliente[df_comparativa_cliente["Año"] == año_seleccionado_2].groupby("Cliente")["Importe"].sum().reset_index()

            # Crear un DataFrame para la comparación con columnas Año1 y Año2
            df_comparativa = pd.DataFrame({
                'Cliente': [cliente_comparativa],
                f'Año1 ({año_seleccionado_1})': [df_año_1['Importe'].sum()],
                f'Año2 ({año_seleccionado_2})': [df_año_2['Importe'].sum()]
            })

            # Mostrar DataFrame comparativo
            st.dataframe(df_comparativa)

            # Botón para descargar el DataFrame en Excel
            import io  # Importamos io para trabajar con el buffer
            buffer = io.BytesIO()  # Creamos un buffer en memoria
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:  # Usamos ExcelWriter explícitamente
                df_comparativa.to_excel(writer, index=False, sheet_name='Comparativa Ventas')  # Escribimos en el buffer
            buffer.seek(0)  # Movemos el puntero al inicio del buffer

            st.download_button(
                label="Descargar en Excel",
                data=buffer,  # Pasamos el buffer como archivo
                file_name="comparativa_ventas.xlsx",  # Nombre del archivo de descarga
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.write("---")

        # Nueva sección: Multiselect por clientes y años
        st.subheader("Datos de Ventas: Multiselect por Clientes y Años")
        clientes_seleccionados = st.multiselect(
            "Selecciona los clientes",
            df["Cliente"].unique(),
            default=df["Cliente"].unique(),
            key="clientes_multiselect"
        )
        años_seleccionados = st.multiselect(
            "Selecciona los años",
            df["Año"].unique(),
            default=df["Año"].unique(),
            key="años_multiselect"
        )

        if clientes_seleccionados and años_seleccionados:
            # Filtrar datos por clientes y años seleccionados
            df_filtrado = df[(df["Cliente"].isin(clientes_seleccionados)) & (df["Año"].isin(años_seleccionados))]

            # Crear un DataFrame con columnas dinámicas según los años seleccionados
            df_resumen = df_filtrado.pivot_table(
                index="Cliente",
                columns="Año",
                values="Importe",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            # Renombrar columnas para incluir "Año"
            df_resumen.columns = ["Cliente"] + [f"Año ({col})" for col in df_resumen.columns[1:]]

            # Mostrar DataFrame filtrado
            st.dataframe(df_resumen)

            # Botón para descargar el DataFrame filtrado en Excel
            buffer = io.BytesIO()  # Creamos un buffer en memoria
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:  # Usamos ExcelWriter explícitamente
                df_resumen.to_excel(writer, index=False, sheet_name='Ventas Filtradas')  # Escribimos en el buffer
            buffer.seek(0)  # Movemos el puntero al inicio del buffer

            st.download_button(
                label="Descargar en Excel",
                data=buffer,  # Pasamos el buffer como archivo
                file_name="ventas_filtradas.xlsx",  # Nombre del archivo de descarga
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


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

             # Calcular el cambio porcentual mensual
            if not df_completo.empty:
                # Asegurarse de que el cambio porcentual se calcule dentro de cada año
                df_completo['Cambio_Porcentual'] = df_completo.groupby('Año')['Importe'].pct_change() * 100

                # Solo mostrar el gráfico si hay datos
                if len(df_completo) > 0:
                    # Filtrar los datos según los años seleccionados en el multiselect
                    df_filtrado = df_completo[df_completo['Año'].isin(años_elegidos)]
                    
                    # Crear gráfico de línea para mostrar el cambio porcentual por mes
                    line_chart_percentual = alt.Chart(df_filtrado).mark_line().encode(
                        x=alt.X('Mes:O', title='Mes', axis=alt.Axis(format='d')),
                        y=alt.Y('Cambio_Porcentual:Q', title='Cambio Porcentual', scale=alt.Scale(domain=[-100, 100])),
                        color=alt.Color('Año:N', title='Año'),
                        tooltip=['Año', 'Mes', 'Cambio_Porcentual']
                    ).properties(
                        title="Cambio Porcentual de Ventas por Mes" if año_seleccionado == "Todos los años" else f'Cambio Porcentual de Ventas por Mes en {año_seleccionado}'
                    )

                    # Añadir puntos en las líneas
                    line_points_percentual = line_chart_percentual.mark_point(size=50)

                    # Mostrar gráfico de líneas
                    st.altair_chart(line_chart_percentual + line_points_percentual, use_container_width=True)
                
        # Nueva sección: Ventas mensuales promedio
        st.write("---")
        st.subheader("Ventas mensuales promedio")

        # Multiselect para seleccionar clientes y años
        clientes_promedio = st.multiselect("Selecciona los clientes", df["Cliente"].unique(), key="clientes_promedio")
        años_promedio = st.multiselect("Selecciona los años", df["Año"].unique(), key="años_promedio")

        if clientes_promedio and años_promedio:
            # Filtrar datos por clientes y años seleccionados
            df_promedio = df[(df["Cliente"].isin(clientes_promedio)) & (df["Año"].isin(años_promedio))]
            
            # Calcular la venta promedio mensual
            ventas_mensuales = df_promedio.groupby(["Cliente", "Año", "Mes"])['Importe'].sum().reset_index()
            promedio_mensual = ventas_mensuales.groupby(["Cliente", "Año"])['Importe'].mean().reset_index()
            
            # Formatear los valores de importe
            promedio_mensual["Importe_formateado"] = promedio_mensual["Importe"].apply(lambda x: "{:,.2f}".format(x))
            
            # Mostrar los resultados en una tabla solo con la columna formateada
            col1, col2 = st.columns([3, 1])
            with col1:
                st.dataframe(promedio_mensual[["Cliente", "Año", "Importe_formateado"]], hide_index=True, width=700)
            
            # Calcular el promedio total de los años seleccionados
            promedio_total = promedio_mensual["Importe"].mean()
            promedio_total_formateado = "{:,.2f}".format(promedio_total)
            
            with col2:
                st.metric(label="Promedio total de los años seleccionados", value=promedio_total_formateado)
            
            # Botón para descargar los datos
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                promedio_mensual[["Cliente", "Año", "Importe_formateado"]].to_excel(writer, index=False, sheet_name='Promedio Mensual Ventas')
            buffer.seek(0)

            st.download_button(
                label="Descargar en Excel",
                data=buffer,
                file_name="promedio_mensual_ventas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


                

#% VENTAS
        # Selección de un solo año para analizar el porcentaje de ventas por cliente
        st.subheader("Porcentaje de Ventas por Cliente")

        # Verificar si el archivo se ha cargado y 'df' está definido
        if 'df' in locals():
            año_seleccionado = st.selectbox("Selecciona el año para el análisis", df["Año"].unique())

            # Filtrar los datos según el año seleccionado
            df_filtrado = df[df["Año"] == año_seleccionado]

            # Verificar que el DataFrame no esté vacío
            if df_filtrado.empty:
                st.warning("No hay datos disponibles para el año seleccionado.")
            else:
                # Calcular el total de ventas por cliente y el total del año
                ventas_por_cliente = df_filtrado.groupby("Cliente")["Importe"].sum().reset_index()
                total_ventas_año = ventas_por_cliente["Importe"].sum()
                ventas_por_cliente["Porcentaje"] = (ventas_por_cliente["Importe"] / total_ventas_año) * 100

                # Ordenar los clientes por porcentaje de mayor a menor
                ventas_por_cliente = ventas_por_cliente.sort_values(by="Porcentaje", ascending=False)

                # Crear columna con nombre y porcentaje para la leyenda y tooltip
                ventas_por_cliente["Cliente con %"] = ventas_por_cliente.apply(
                    lambda x: f"{x['Cliente']} ({x['Porcentaje']:.2f}%)", axis=1
                )

                # Generar colores automáticos usando Seaborn
                unique_clients = ventas_por_cliente["Cliente con %"].unique()
                palette = sns.color_palette("tab10", len(unique_clients)).as_hex()
                color_scale = alt.Scale(domain=unique_clients, range=palette)

                # Mostrar el total de ventas del año a la izquierda de la gráfica
                st.markdown(f"#### Total de Ventas en {año_seleccionado}: ${total_ventas_año:,.2f}")

                # Crear gráfica de barras horizontales para mostrar el porcentaje de ventas por cliente, con colores y leyenda
                bar_chart = alt.Chart(ventas_por_cliente).mark_bar().encode(
                    y=alt.Y("Cliente:N", sort='-x', title="Cliente"),  # Solo nombre del cliente en el eje y (izquierda)
                    x=alt.X("Importe:Q", title="Importe Total"),
                    color=alt.Color("Cliente con %:N", scale=color_scale, title="Cliente"),
                    tooltip=[
                        alt.Tooltip("Cliente con %:N", title="Cliente"),
                        alt.Tooltip("Porcentaje:Q", format=".2f", title="% de Ventas"),
                        alt.Tooltip("Importe:Q", format="$,.2f", title="Importe Total")
                    ]
                ).properties(
                    title=f"Distribución de Ventas por Cliente en {año_seleccionado}"
                )

                # Mostrar gráfico de barras horizontales
                st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.warning("Por favor, sube un archivo CSV para continuar.")
        


    elif opcion == "SKU's Analysis":
        st.markdown("## PRODUCTOS VENDIDOS :gear:")
        # Agregar opción "Todos los clientes" al selectbox de cliente
        clientes_unicos = list(df["Cliente"].unique())
        clientes_unicos.insert(0, "Todos los clientes")

        # Selección de cliente para análisis de productos
        cliente_seleccionado_producto = st.selectbox("Selecciona un cliente para el análisis de productos", clientes_unicos)

        # Selección de año para análisis de productos
        año_seleccionado_producto = st.selectbox("Selecciona el año para el análisis de productos", df["Año"].unique())

        # Ingresar cantidad de productos a mostrar, permitiendo la opción de "todos"
        cantidad_productos = st.number_input(
            "Cantidad de productos a mostrar (ingresa 0 para mostrar todos)", 
            min_value=0, max_value=50, value=20, step=1
        )

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

            # Agregar columna de precio promedio usado ese año (Importe / Cantidad)
            ventas_producto["Precio Promedio"] = ventas_producto["Importe"] / ventas_producto["Cantidad"]
            ventas_producto["Precio Promedio"] = ventas_producto["Precio Promedio"].fillna(0).round(2)

            # Ordenar y seleccionar la cantidad de productos más vendidos especificados por el usuario
            ventas_producto = ventas_producto.sort_values(by="Importe", ascending=False)
            if cantidad_productos > 0:  # Si cantidad_productos es 0, se muestran todos
                ventas_producto = ventas_producto.head(cantidad_productos)

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

            # Determinar el nombre del archivo según el cliente seleccionado
            if cliente_seleccionado_producto == "Todos los clientes":
                nombre_archivo = "detalle_productos_vendidos_todos_los_clientes.xlsx"
            else:
                # Reemplazar espacios por guiones bajos y convertir a minúsculas para el nombre del archivo
                nombre_archivo = f"detalle_productos_vendidos_{cliente_seleccionado_producto.replace(' ', '_').lower()}.xlsx"

            # Mostrar gráfico
            st.altair_chart(bars_producto + text_producto, use_container_width=True)

            # Mostrar tabla con SKU, Cantidad, Importe, Precio Promedio y Porcentaje
            st.write(f"### Ventas: {suma_ventas_top_formateado} - {cliente_seleccionado_producto}   ({porcentaje_ventas_top_formateado})")
            st.dataframe(ventas_producto[['SKU', 'Producto', 'Cantidad', 'Importe_formateado', 'Porcentaje_formateado', 'Precio Promedio']])

            # Botón para descargar el DataFrame en Excel
            import io  # Importamos io para trabajar con el buffer
            buffer = io.BytesIO()  # Creamos un buffer en memoria
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:  # Usamos ExcelWriter explícitamente
                ventas_producto.to_excel(writer, index=False, sheet_name='Productos Vendidos')  # Escribimos en el buffer
            buffer.seek(0)  # Movemos el puntero al inicio del buffer

            st.download_button(
                label="Descargar en Excel",
                data=buffer,  # Pasamos el buffer como archivo
                file_name=nombre_archivo,  # Nombre del archivo de descarga
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # NUEVA SECCIÓN
            st.write("---")

            st.markdown("## PRODUCTOS VENDIDOS POR MES :chart_with_upwards_trend:")

            # Selección de cliente
            clientes_unicos = list(df["Cliente"].unique())
            clientes_unicos.insert(0, "Todos los clientes")
            cliente_seleccionado = st.selectbox("Selecciona un cliente", clientes_unicos)

            # Selección de año
            años_unicos = list(df["Año"].unique())
            año_seleccionado = st.selectbox("Selecciona un año", años_unicos)

            # Filtrar el DataFrame según el cliente y año seleccionados
            if cliente_seleccionado == "Todos los clientes":
                df_producto = df[df["Año"] == año_seleccionado]
            else:
                df_producto = df[(df["Cliente"] == cliente_seleccionado) & (df["Año"] == año_seleccionado)]

            # Asegurarse de que la columna "Cantidad" y "Importe" sean numéricas
            df_producto["Cantidad"] = pd.to_numeric(df_producto["Cantidad"], errors="coerce").fillna(0)
            df_producto["Importe"] = pd.to_numeric(df_producto["Importe"], errors="coerce").fillna(0)

            # Calcular el precio promedio por SKU/Producto
            ventas_producto = df_producto.groupby(["SKU", "Producto"], as_index=False).agg(
                {"Cantidad": "sum", "Importe": "sum"}
            )
            ventas_producto["Precio Promedio"] = ventas_producto["Importe"] / ventas_producto["Cantidad"]
            ventas_producto["Precio Promedio"] = ventas_producto["Precio Promedio"].fillna(0).round(2)

            # Calcular las ventas por mes
            df_producto["Fecha"] = pd.to_datetime(df_producto["Fecha"], errors="coerce")
            df_producto = df_producto.dropna(subset=["Fecha"])  # Eliminar filas con fechas inválidas
            df_producto["Mes"] = df_producto["Fecha"].dt.month

            ventas_mensuales = df_producto.groupby(["SKU", "Producto", "Mes"], as_index=False).agg(
                {"Cantidad": "sum", "Importe": "sum"}
            )

            # Pivotear los datos para obtener columnas por mes
            ventas_pivot = ventas_mensuales.pivot_table(
                index=["SKU", "Producto"],
                columns="Mes",
                values=["Cantidad", "Importe"],
                aggfunc="sum",
                fill_value=0
            )

            # Nombres de columnas en español y alternar orden
            meses_espanol = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]

            ventas_pivot.columns = [
                f"Importe {meses_espanol[col[1]-1]}" if col[0] == "Importe" else f"Cantidad {meses_espanol[col[1]-1]}"
                for col in ventas_pivot.columns
            ]
            ventas_pivot = ventas_pivot.reset_index()

            # Asegurar que todas las columnas de meses están presentes en el orden correcto
            columnas_ordenadas = []
            for mes in meses_espanol:
                columnas_ordenadas.append(f"Importe {mes}")
                columnas_ordenadas.append(f"Cantidad {mes}")

            for columna in columnas_ordenadas:
                if columna not in ventas_pivot.columns:
                    ventas_pivot[columna] = 0

            # Combinar los datos de ventas por producto con los datos mensuales
            resultado_final = pd.merge(ventas_producto, ventas_pivot, on=["SKU", "Producto"], how="left")

            # Calcular Cantidad Total e Importe Total de manera robusta
            resultado_final["Cantidad Total"] = resultado_final[[col for col in columnas_ordenadas if "Cantidad" in col]].sum(axis=1)
            resultado_final["Importe Total"] = resultado_final[[col for col in columnas_ordenadas if "Importe" in col]].sum(axis=1)

            # Reorganizar las columnas en el orden deseado
            columnas_finales = ["SKU", "Producto", "Cantidad Total", "Importe Total", "Precio Promedio"] + columnas_ordenadas
            resultado_final = resultado_final[columnas_finales]

            # Mostrar tabla con los datos por mes
            st.write(f"#### Detalle Mensual de Productos Vendidos para {cliente_seleccionado} en {año_seleccionado}")
            st.dataframe(resultado_final)

            # Descargar el DataFrame en Excel
            buffer_mensual = io.BytesIO()
            with pd.ExcelWriter(buffer_mensual, engine="openpyxl") as writer:
                resultado_final.to_excel(writer, index=False, sheet_name="Productos Mensuales")
            buffer_mensual.seek(0)

            st.download_button(
                label="Descargar en Excel",
                data=buffer_mensual,
                file_name=f"detalle_mensual_productos_{cliente_seleccionado.replace(' ', '_').lower()}_{año_seleccionado}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )





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

