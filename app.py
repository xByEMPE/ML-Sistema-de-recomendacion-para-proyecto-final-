import streamlit as st
import pandas as pd
import os
from google.cloud import bigquery
from textblob import TextBlob
import numpy as np

# Configuración del proyecto y dataset (datos públicos, no se requiere autenticación especial)
PROJECT_ID = "robotic-aviary-451823-k6"
DATASET_ID = "cargaAzure"

# ---------------------------------------------------------------------
# Función para leer y procesar datos desde BigQuery
# ---------------------------------------------------------------------
@st.cache_data
def load_and_process_data():
    client = bigquery.Client(project=PROJECT_ID)
    
    # Consulta que une la tabla Business con TipYelp para obtener reseñas
    query = f"""
    SELECT
      b.business_id,
      b.name,
      b.state,
      b.city,
      b.stars AS avg_rating,
      b.food_subcategory,
      t.text AS review_text
    FROM `{PROJECT_ID}.{DATASET_ID}.Business` AS b
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.TipYelp` AS t
      ON b.business_id = t.business_id
    LIMIT 1000
    """
    
    df = client.query(query).to_dataframe()
    
    # Calcular sentimiento de cada reseña con TextBlob
    def get_sentiment_polarity(text):
        if pd.isnull(text) or not isinstance(text, str) or text.strip() == "":
            return np.nan
        return TextBlob(text).sentiment.polarity
    
    df["sentiment"] = df["review_text"].apply(get_sentiment_polarity)
    
    # Agrupar por restaurante para obtener el sentimiento promedio
    df_sentiment = (
        df.groupby(["business_id", "name", "state", "city", "avg_rating", "food_subcategory"], as_index=False)
          .agg(avg_sentiment=("sentiment", "mean"))
    )
    
    # Calcular un score combinado: ponderamos la calificación y el sentimiento
    alpha = 1.0  # peso para la calificación
    beta = 0.5   # peso para el sentimiento
    df_sentiment["combined_score"] = alpha * df_sentiment["avg_rating"] + beta * df_sentiment["avg_sentiment"]
    
    # Ordenar por score combinado descendente
    df_sentiment.sort_values("combined_score", ascending=False, inplace=True)
    
    return df_sentiment

# ---------------------------------------------------------------------
# Función de recomendación con filtros
# ---------------------------------------------------------------------
def recommend_restaurants(df_sentiment, food_type=None, min_rating=None, state=None, top_n=5):
    df_filter = df_sentiment.copy()
    
    # Filtrar por tipo de comida (buscando coincidencias en 'food_subcategory')
    if food_type:
        df_filter = df_filter[
            df_filter["food_subcategory"].str.contains(food_type, case=False, na=False)
        ]
    
    # Filtrar por calificación mínima
    if min_rating is not None:
        df_filter = df_filter[df_filter["avg_rating"] >= min_rating]
    
    # Filtrar por estado (comparación en mayúsculas)
    if state:
        df_filter = df_filter[df_filter["state"].str.upper() == state.upper()]
    
    # Ordenar por score combinado y seleccionar columnas de interés
    df_filter = df_filter.sort_values("combined_score", ascending=False)
    columns = ["name", "state", "city", "avg_rating", "avg_sentiment", "combined_score", "food_subcategory"]
    return df_filter[columns].head(top_n)

# ---------------------------------------------------------------------
# Interfaz de la app con Streamlit (más llamativa)
# ---------------------------------------------------------------------
def main():
    # Agregar un banner o imagen (opcional, reemplaza la URL por una propia)
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
    
    st.title("🍽️ Recomendador de Restaurantes")
    st.markdown("### Encuentra el mejor restaurante para ti basado en reseñas y calificaciones")
    st.markdown("Utiliza los filtros de la barra lateral para especificar el tipo de comida, la calificación mínima y el estado.")
    
    # Mostrar un spinner mientras se cargan los datos
    with st.spinner("Cargando y procesando datos desde BigQuery..."):
        df_sentiment = load_and_process_data()
    
    # Crear un contenedor para los filtros usando la barra lateral
    st.sidebar.header("Filtros de Búsqueda")
    food_type = st.sidebar.text_input("Tipo de comida (ej: Seafood, Asiática, Vegetariana)", "")
    min_rating = st.sidebar.number_input("Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
    state = st.sidebar.text_input("Estado (ej: CA, NY, TX)", "")
    
    if st.sidebar.button("Buscar Recomendaciones"):
        results = recommend_restaurants(df_sentiment, food_type, min_rating, state, top_n=5)
        st.markdown("### Top 5 Recomendaciones")
        
        if not results.empty:
            # Usar columnas para mostrar información de cada restaurante
            for index, row in results.iterrows():
                with st.container():
                    st.markdown(f"**{row['name']}**")
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Estado:** {row['state']}")
                    col2.write(f"**Ciudad:** {row['city']}")
                    col3.write(f"**Calificación:** {row['avg_rating']}")
                    st.write(f"**Tipo de comida:** {row['food_subcategory']}")
                    st.write(f"**Score combinado:** {row['combined_score']:.2f}")
                    st.markdown("---")
        else:
            st.warning("No se encontraron restaurantes que cumplan con esos filtros.")

if __name__ == "__main__":
    main()
