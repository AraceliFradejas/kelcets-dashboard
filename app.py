import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re

# Configuración de la página
st.set_page_config(
    page_title="KelceTS - Dashboard de Comunicaciones",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título del dashboard
st.title("📊 Dashboard de Análisis de Comunicaciones - KelceTS")
st.markdown("---")

# Función para cargar comentarios desde el archivo TXT
@st.cache_data
def cargar_comentarios_desde_txt():
    try:
        with open('comentarios.txt', 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Extraer comentarios - buscamos patrones comunes
        comentarios = []
        
        # Intentar varios patrones de extracción
        patrones = [
            r'(?:Comentario|Kommentar|Commentaire|Commento|Opmerking|Komentarz|Comentário|Kommentti|Σχόλιο)\s+(\d+)\s*:\s*(.*?)(?=(?:Comentario|Kommentar|Commentaire|Commento|Opmerking|Komentarz|Comentário|Kommentti|Σχόλιο)\s+\d+\s*:|$)',
            r'(\d+)\s*[.:\)]\s*(.*?)(?=\d+\s*[.:\)]|$)'
        ]
        
        for patron in patrones:
            matches = re.findall(patron, contenido, re.DOTALL)
            if matches:
                # Si encontramos coincidencias con este patrón
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        numero = match[0]
                        texto = match[1].strip()
                        comentarios.append((numero, texto))
                break
        
        if not comentarios:
            # Si no se extrajo nada con los patrones, dividir por líneas
            lineas = contenido.split('\n')
            comentario_actual = ""
            numero_actual = "1"
            
            for linea in lineas:
                if linea.strip():
                    match = re.match(r'^(\d+)[.:\)]?\s*(.*)', linea)
                    if match:
                        # Si encontramos un nuevo número, guardamos el comentario anterior
                        if comentario_actual:
                            comentarios.append((numero_actual, comentario_actual.strip()))
                        
                        numero_actual = match.group(1)
                        comentario_actual = match.group(2)
                    else:
                        # Continuamos con el comentario actual
                        comentario_actual += " " + linea
            
            # Añadir el último comentario
            if comentario_actual:
                comentarios.append((numero_actual, comentario_actual.strip()))
        
        return comentarios
    except Exception as e:
        st.error(f"Error al cargar comentarios: {str(e)}")
        return []

# Función para analizar comentarios
def analizar_comentario(texto):
    """Analiza un comentario y devuelve el resultado estimado"""
    # Detectar idioma (simplificado)
    idioma = "desconocido"
    if re.search(r'[áéíóúüñ¿¡]', texto.lower()):
        idioma = "español"
    elif re.search(r'[àèìòùçé]', texto.lower()):
        idioma = "francés"
    elif re.search(r'[äöüß]', texto.lower()):
        idioma = "alemán"
    elif re.search(r'[ãõê]', texto.lower()):
        idioma = "portugués"
    elif re.search(r'[αβγδε]', texto.lower()):
        idioma = "griego"
    elif re.search(r'[åæø]', texto.lower()):
        idioma = "finlandés"
    
    # Detección simple de sentimiento (muy simplificada)
    palabras_positivas = ['bueno', 'excelente', 'genial', 'perfecto', 'cómodo', 'bien']
    palabras_negativas = ['malo', 'error', 'problema', 'rotura', 'defecto', 'incómodo', 'no']
    
    sentimiento = "neutro"
    texto_lower = texto.lower()
    if any(palabra in texto_lower for palabra in palabras_positivas):
        sentimiento = "positivo"
    if any(palabra in texto_lower for palabra in palabras_negativas):
        sentimiento = "negativo"
    
    # Ejemplo de detección simple de problemas (real necesitaría NLP más avanzado)
    problema_talla = "no" if re.search(r'tall[a|e]|pequeñ[o|a]|grand[e]', texto_lower) else "no mencionado"
    problema_material = "no" if re.search(r'material|calidad|rot[o|a]|desgast[e|a]', texto_lower) else "no mencionado"
    problema_envio = "no" if re.search(r'env[i|í]o|retraso|tard[e|ó]', texto_lower) else "no mencionado"
    
    return {
        "idioma": idioma,
        "valoracion": "positiva" if sentimiento == "positivo" else "negativa" if sentimiento == "negativo" else "neutra",
        "envio_96h": problema_envio,
        "embalaje_danado": "no mencionado",
        "talla_correcta": problema_talla,
        "materiales_calidad": problema_material,
        "tipo_uso": "no mencionado",
        "cumple_expectativas": "sí" if sentimiento == "positivo" else "no" if sentimiento == "negativo" else "parcialmente"
    }

# Función para cargar y analizar datos
@st.cache_data
def cargar_datos():
    # Cargar comentarios desde archivo TXT
    comentarios_raw = cargar_comentarios_desde_txt()
    
    if not comentarios_raw:
        # Si no hay comentarios, generar datos de prueba
        st.warning("No se pudieron cargar comentarios del archivo. Usando datos de ejemplo.")
        return generar_datos_ejemplo()
    
    # Procesar comentarios
    datos = []
    for num, texto in comentarios_raw:
        # Analizar cada comentario
        analisis = analizar_comentario(texto)
        
        datos.append({
            "ID": int(num),
            "Comentario_Original": texto[:200] + "..." if len(texto) > 200 else texto,
            "Idioma": analisis["idioma"],
            "Valoracion": analisis["valoracion"],
            "Envio_96h": analisis["envio_96h"],
            "Embalaje_Danado": analisis["embalaje_danado"],
            "Talla_Correcta": analisis["talla_correcta"],
            "Materiales_Calidad": analisis["materiales_calidad"],
            "Tipo_Uso": analisis["tipo_uso"],
            "Cumple_Expectativas": analisis["cumple_expectativas"]
        })
    
    # Crear DataFrame con los datos procesados
    df = pd.DataFrame(datos)
    df_comunicaciones = df.copy()
    
    # Calcular estadísticas
    metricas = ["Total Comentarios", "Valoraciones Positivas", "Valoraciones Negativas", 
                "Valoraciones Neutras", "Problemas de Calidad Materiales", 
                "Problemas de Talla", "Problemas de Envío", "Problemas de Embalaje",
                "Satisfacción General (%)"]
    
    valores = [
        len(df),
        len(df[df['Valoracion'] == 'positiva']),
        len(df[df['Valoracion'] == 'negativa']),
        len(df[df['Valoracion'] == 'neutra']),
        len(df[df['Materiales_Calidad'] == 'no']),
        len(df[df['Talla_Correcta'] == 'no']),
        len(df[df['Envio_96h'] == 'no']),
        len(df[df['Embalaje_Danado'] == 'sí']),
        round(len(df[df['Cumple_Expectativas'].isin(['sí', 'parcialmente'])]) / len(df) * 100 if len(df) > 0 else 0, 2)
    ]
    
    df_estadisticas = pd.DataFrame({
        'Métrica': metricas,
        'Valor': valores
    })
    
    return df, df_comunicaciones, df_estadisticas, True

# Función para generar datos de ejemplo (fallback)
def generar_datos_ejemplo():
    # Datos simulados para el DataFrame principal
    data_resumen = {
        'ID': list(range(1, 11)),
        'Comentario_Original': ['Ejemplo de comentario 1', 'Ejemplo de comentario 2'] * 5,
        'Idioma': ['español', 'alemán', 'español', 'finés', 'portugués'] * 2,
        'Valoracion': ['positiva', 'negativa', 'positiva', 'negativa', 'neutra'] * 2,
        'Envio_96h': ['sí', 'no', 'sí', 'no', 'no mencionado'] * 2,
        'Embalaje_Danado': ['no', 'sí', 'no', 'no', 'no mencionado'] * 2,
        'Talla_Correcta': ['sí', 'no', 'sí', 'no', 'no mencionado'] * 2,
        'Materiales_Calidad': ['sí', 'no', 'parcialmente', 'no', 'no mencionado'] * 2,
        'Tipo_Uso': ['diario', 'ocasional', 'diario', 'ocasional', 'no mencionado'] * 2,
        'Cumple_Expectativas': ['sí', 'no', 'parcialmente', 'no', 'no mencionado'] * 2
    }
    
    # Datos simulados para estadísticas
    data_estadisticas = {
        'Métrica': [
            'Total Comentarios',
            'Valoraciones Positivas',
            'Valoraciones Negativas',
            'Valoraciones Neutras',
            'Problemas de Calidad Materiales',
            'Problemas de Talla',
            'Problemas de Envío',
            'Problemas de Embalaje',
            'Satisfacción General (%)'
        ],
        'Valor': [10, 4, 4, 2, 4, 4, 4, 2, 60]
    }
    
    # Crear DataFrames
    df = pd.DataFrame(data_resumen)
    df_comunicaciones = pd.DataFrame(data_resumen)
    df_estadisticas = pd.DataFrame(data_estadisticas)
    
    return df, df_comunicaciones, df_estadisticas, True

# Cargar datos
df, df_comunicaciones, df_estadisticas, datos_cargados = cargar_datos()

# Barra lateral para navegación
st.sidebar.title("Navegación")
seccion = st.sidebar.radio(
    "Selecciona una sección:",
    ["Resumen General", "Análisis por Idioma", "Análisis de Satisfacción", 
     "Problemas Detectados", "Datos en Bruto"]
)

if datos_cargados:
    # Sección 1: Resumen General
    if seccion == "Resumen General":
        st.header("📈 Resumen General")
        
        # Mostrar KPIs en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        # Extraer valores de estadísticas
        total_comentarios = df_estadisticas[df_estadisticas["Métrica"] == "Total Comentarios"]["Valor"].values[0]
        valoraciones_positivas = df_estadisticas[df_estadisticas["Métrica"] == "Valoraciones Positivas"]["Valor"].values[0]
        valoraciones_negativas = df_estadisticas[df_estadisticas["Métrica"] == "Valoraciones Negativas"]["Valor"].values[0]
        satisfaccion_general = df_estadisticas[df_estadisticas["Métrica"] == "Satisfacción General (%)"]["Valor"].values[0]
        
        with col1:
            st.metric("Total Comentarios", f"{total_comentarios}")
        
        with col2:
            st.metric("Valoraciones Positivas", f"{valoraciones_positivas}")
        
        with col3:
            st.metric("Valoraciones Negativas", f"{valoraciones_negativas}")
        
        with col4:
            st.metric("Satisfacción General", f"{satisfaccion_general}%")
        
        st.markdown("---")
        
        # Gráfico de distribución de valoraciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Valoraciones")
            fig_valoraciones = px.pie(
                names=df["Valoracion"].value_counts().index, 
                values=df["Valoracion"].value_counts().values,
                color=df["Valoracion"].value_counts().index,
                color_discrete_map={"positiva":"green", "negativa":"red", "neutra":"blue"},
                hole=0.4
            )
            st.plotly_chart(fig_valoraciones, use_container_width=True)
        
        with col2:
            st.subheader("Cumplimiento de Expectativas")
            fig_expectativas = px.pie(
                names=df["Cumple_Expectativas"].value_counts().index,
                values=df["Cumple_Expectativas"].value_counts().values,
                color=df["Cumple_Expectativas"].value_counts().index,
                color_discrete_map={"sí":"green", "no":"red", "parcialmente":"orange", "no mencionado":"gray"},
                hole=0.4
            )
            st.plotly_chart(fig_expectativas, use_container_width=True)
        
        # Problemas detectados
        st.subheader("Principales Problemas Detectados")
        
        problemas_df = pd.DataFrame({
            "Problema": ["Materiales", "Talla", "Envío", "Embalaje"],
            "Cantidad": [
                df_estadisticas[df_estadisticas["Métrica"] == "Problemas de Calidad Materiales"]["Valor"].values[0],
                df_estadisticas[df_estadisticas["Métrica"] == "Problemas de Talla"]["Valor"].values[0],
                df_estadisticas[df_estadisticas["Métrica"] == "Problemas de Envío"]["Valor"].values[0],
                df_estadisticas[df_estadisticas["Métrica"] == "Problemas de Embalaje"]["Valor"].values[0]
            ]
        })
        
        fig_problemas = px.bar(
            problemas_df, 
            x="Problema", 
            y="Cantidad",
            color="Problema"
        )
        st.plotly_chart(fig_problemas, use_container_width=True)
    
    # Sección 2: Análisis por Idioma
    elif seccion == "Análisis por Idioma":
        st.header("🌍 Análisis por Idioma")
        
        # Distribución de idiomas
        st.subheader("Distribución de Comentarios por Idioma")
        fig_idiomas = px.pie(
            names=df["Idioma"].value_counts().index,
            values=df["Idioma"].value_counts().values
        )
        st.plotly_chart(fig_idiomas, use_container_width=True)
    
    # Sección 3: Análisis de Satisfacción
    elif seccion == "Análisis de Satisfacción":
        st.header("😊 Análisis de Satisfacción")
        
        # Ejemplo simple para demostración
        st.subheader("Satisfacción por tipo de problema")
        st.bar_chart(df["Materiales_Calidad"].value_counts())
    
    # Sección 4: Problemas Detectados
    elif seccion == "Problemas Detectados":
        st.header("⚠️ Problemas Detectados")
        
        # Filtro por tipo de problema
        tipo_problema = st.radio(
            "Selecciona el tipo de problema:",
            ["Materiales", "Talla", "Envío", "Embalaje"]
        )
        
        st.write(f"Datos filtrados para problema de {tipo_problema}")
        st.dataframe(df.head(3))
    
    # Sección 5: Datos en Bruto
    else:  # Datos en Bruto
        st.header("📋 Datos en Bruto")
        st.dataframe(df)

else:
    st.error("No se pudieron cargar los datos.")

# Pie de página
st.markdown("---")
st.markdown("Desarrollado para KelceTS S.L. | Dashboard de Análisis de Comentarios de Clientes")
