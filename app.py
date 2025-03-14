import streamlit as st
import pandas as pd
import os

# URL directa de la imagen de fondo
background_image = "https://i.pinimg.com/736x/b8/57/f6/b857f6eeed86bc1eda743afec402b194.jpg"

# Inyectar CSS para cambiar el fondo
page_bg_img = f"""
<style>
body {{
    background-image: url("{background_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)
st.title("Aplicación con fondo personalizado")


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
def recommend_restaurants(df, food_types=None, min_rating=None, states=None, top_n=5):
    df_filter = df.copy()
    
    # Filtrar por tipos de comida (si se seleccionó al menos uno)
    if food_types:
        df_filter = df_filter[
            df_filter["food_subcategory"].str.lower().apply(
                lambda x: any(ft.lower() in x for ft in food_types)
            )
        ]
    
    # Filtrar por calificación mínima
    if min_rating is not None:
        df_filter = df_filter[df_filter["avg_rating"] >= min_rating]
    
    # Filtrar por estados (si se seleccionó al menos uno)
    if states:
        df_filter = df_filter[
            df_filter["state"].str.upper().isin([s.upper() for s in states])
        ]
    
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
        
        # Lista de tipos de comida disponibles
        available_food_types = [
            "Bakeries", "Seafood", "Mexicana/Latina", "Coffee & Tea", "Bars", 
            "General Food", "Asiática", "Restaurants", "Vegetariana/Vegana", 
            "Juice Bars & Smoothies", "Fast Food", "Food Trucks", "Pizza", 
            "Ice Cream & Frozen Yogurt", "Italiana", "Bubble Tea", 
            "Mediterránea/Medio Oriente", "Shopping", "Caribeña", "Europea", 
            "Gluten-Free", "Halal", "Hawaiana", "Kosher"
        ]
        
        # Selector múltiple para tipos de comida (máximo 3)
        selected_food_types = st.sidebar.multiselect(
            "Tipos de comida disponibles (máximo 3)",
            options=available_food_types,
            default=[]
        )
        
        if len(selected_food_types) > 3:
            st.sidebar.error("Por favor, selecciona máximo 3 tipos de comida.")
        
        # Selector para calificación mínima
        min_rating = st.sidebar.number_input(
            "Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=3.0, step=0.5
        )
        
        # Definir los estados disponibles basados en los tipos de comida seleccionados
        if selected_food_types:
            filtered_df = df[
                df["food_subcategory"].str.lower().apply(
                    lambda x: any(ft.lower() in x for ft in selected_food_types)
                )
            ]
            available_states = sorted(filtered_df["state"].unique())
        else:
            available_states = sorted(df["state"].unique())
        
        # Selector múltiple para estados
        selected_states = st.sidebar.multiselect(
            "Estados disponibles",
            options=available_states,
            default=available_states
        )
        
        if st.sidebar.button("Buscar Recomendaciones"):
            results = recommend_restaurants(df, selected_food_types, min_rating, selected_states, top_n=5)
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
