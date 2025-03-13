import streamlit as st
import pandas as pd
import os
from google.cloud import bigquery
from textblob import TextBlob
import numpy as np

# Configuración del proyecto y dataset (los datos son públicos, no se requiere autenticación especial)
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
# Interfaz de la app con Streamlit
# ---------------------------------------------------------------------
def main():
    st.title("Recomendador de Restaurantes")
    st.write("Encuentra el mejor restaurante de comida basado en reseñas y calificaciones.")
    
    # Cargar y procesar los datos (se cachea para mayor velocidad)
    df_sentiment = load_and_process_data()
    
    st.sidebar.header("Filtros de búsqueda")
    food_type = st.sidebar.text_input("Tipo de comida (ej: Seafood, Asiática, Vegetariana, etc.)", "")
    min_rating = st.sidebar.number_input("Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
    state = st.sidebar.text_input("Estado (ej: CA, NY, TX)", "")
    
    if st.sidebar.button("Buscar Recomendaciones"):
        results = recommend_restaurants(df_sentiment, food_type, min_rating, state, top_n=5)
        if not results.empty:
            st.write("### Top 5 Recomendaciones")
            st.dataframe(results)
        else:
            st.write("No se encontraron restaurantes que cumplan con esos filtros.")

if __name__ == "__main__":
    main()
