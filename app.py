import streamlit as st
import pandas as pd
import os

# Ruta del CSV con datos preprocesados (asegúrate de que esté en el mismo directorio que app.py)
CSV_PATH = "datos_preprocesados (1).csv"

# Función para cargar los datos desde el CSV
@st.cache_data
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        st.error("El archivo CSV no se encontró. Ejecuta primero el notebook para generar el CSV.")
        return None

# Función de recomendación que aplica filtros a los datos
def recommend_restaurants(df, food_type=None, min_rating=None, state=None, top_n=5):
    df_filter = df.copy()
    
    # Filtrar por tipo de comida
    if food_type:
        df_filter = df_filter[df_filter["food_subcategory"].str.contains(food_type, case=False, na=False)]
    
    # Filtrar por calificación mínima
    if min_rating is not None:
        df_filter = df_filter[df_filter["avg_rating"] >= min_rating]
    
    # Filtrar por estado (comparando en mayúsculas)
    if state:
        df_filter = df_filter[df_filter["state"].str.upper() == state.upper()]
    
    # Ordenar por score combinado descendente y seleccionar columnas de interés
    df_filter = df_filter.sort_values("combined_score", ascending=False)
    columns = ["name", "state", "city", "combined_score", "food_subcategory"]
    return df_filter[columns].head(top_n)

def main():
    st.set_page_config(page_title="Recomendador de Restaurantes", layout="wide")
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=150)
    st.title("🍽️ Recomendador de Restaurantes")
    st.markdown("### Encuentra el mejor restaurante basado en reseñas y calificaciones")
    st.markdown("Utiliza los filtros en la barra lateral para especificar el tipo de comida, la calificación mínima y el estado.")

    # Cargar datos preprocesados desde el CSV
    df = load_data()
    if df is not None:
        st.sidebar.header("Filtros de Búsqueda")
        
        # Corrección de texto en text_input y number_input
        food_type = st.sidebar.text_input(
            "Tipos de comida disponibles: (Bakeries, Seafood, Mexicana/Latina, Coffee & Tea, Bars, "
            "General Food, Asiática, Restaurants, Vegetariana/Vegana, "
            "Juice Bars & Smoothies, Fast Food, Food Trucks, Pizza, "
            "Ice Cream & Frozen Yogurt, Italiana, Bubble Tea, "
            "Mediterránea/Medio Oriente, Shopping, Caribeña, Europea, "
            "Gluten-Free, Halal, Hawaiana, Kosher)", 
            ""
        )

        min_rating = st.sidebar.number_input(
            "Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=3.0, step=0.5
        )

        state = st.sidebar.text_input(
            "Estados disponibles: 'AZ', 'PA', 'LA', 'CA', 'MO', 'AB', 'IN', 'NV', 'NJ', 'FL', 'TN', "
            "'IL', 'DE', 'ID', 'CO', 'HI', 'MI', 'TX', 'VT', 'WA', 'VI'", 
            ""
        )

        if st.sidebar.button("Buscar Recomendaciones"):
            results = recommend_restaurants(df, food_type, min_rating, state, top_n=5)
            st.markdown("### Top 5 Recomendaciones")
            
            if not results.empty:
                for idx, row in results.iterrows():
                    with st.container():
                        st.markdown(f"**{row['name']}**")
                        cols = st.columns(3)
                        cols[0].write(f"**Estado:** {row['state']}")
                        cols[1].write(f"**Ciudad:** {row['city']}")
                        cols[2].write(f"**Score:** {row['combined_score']:.2f}")
                        st.write(f"**Tipo de comida:** {row['food_subcategory']}")
                        st.markdown("---")
            else:
                st.warning("No se encontraron restaurantes que cumplan con esos filtros.")

if __name__ == "__main__":
    main()
