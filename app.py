import streamlit as st
import pandas as pd
import os

# Configuración de la página: debe ejecutarse antes de cualquier otro comando de Streamlit
st.set_page_config(page_title="Modelo de ML", layout="wide")

# URL de la imagen de fondo
background_image = "https://cdn.pixabay.com/photo/2016/10/04/05/21/bar-1713610_1280.jpg"

# Inyección de CSS para mejorar visibilidad
custom_css = f"""
<style>
/* Fondo de la aplicación */
[data-testid="stAppViewContainer"] {{
    background: url("{background_image}") no-repeat center center fixed;
    background-size: cover;
}}

/* Agrega un fondo semitransparente a los resultados */
.result-container {{
    background: rgba(0, 0, 0, 0.7);  /* Fondo negro semitransparente */
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: white;
}}

/* Ajustar el color del título y subtítulos */
h1, h2, h3 {{
    color: white !important;
}}

/* Mejorar visibilidad de la barra lateral */
[data-testid="stSidebar"] {{
    background: rgba(0, 0, 0, 0.8) !important;
    color: white;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Ruta del CSV con datos preprocesados
CSV_PATH = "datos_preprocesados (1).csv"

# Diccionario de mapeo de abreviaturas a nombres completos
state_mapping = {
    "AZ": "Arizona", "PA": "Pennsylvania", "LA": "Louisiana", "CA": "California",
    "MO": "Missouri", "AB": "Alberta", "IN": "Indiana", "NV": "Nevada",
    "NJ": "New Jersey", "FL": "Florida", "TN": "Tennessee", "IL": "Illinois",
    "DE": "Delaware", "ID": "Idaho", "CO": "Colorado", "HI": "Hawaii",
    "MI": "Michigan", "TX": "Texas", "VT": "Vermont", "WA": "Washington",
    "VI": "Virgin Islands"
}

# Función para cargar los datos desde el CSV
@st.cache_data
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        st.error("El archivo CSV no se encontró. Ejecuta primero el notebook para generar el CSV.")
        return None

# Función de recomendación que aplica filtros a los datos
def recommend_restaurants(df, food_types=None, min_rating=None, states=None, cities=None, top_n=10):  # <-- NUEVO (cities=None)
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
    
    # Filtrar por ciudades (si se seleccionó al menos una)  # <-- NUEVO
    if cities:
        df_filter = df_filter[df_filter["city"].isin(cities)]
    
    # Ordenar por score combinado descendente
    df_filter = df_filter.sort_values("combined_score", ascending=False)
    
    # Seleccionar columnas de interés e incluir "address"  # <-- NUEVO
    columns = ["name", "state", "city", "address", "combined_score", "food_subcategory"]
    return df_filter[columns].head(top_n)

def main():
    # Inicializar variables de sesión si no existen
    if "results" not in st.session_state:
        st.session_state.results = None
    if "selected_food_types" not in st.session_state:
        st.session_state.selected_food_types = []
    if "selected_states" not in st.session_state:
        st.session_state.selected_states = []
    if "selected_cities" not in st.session_state:  # <-- NUEVO
        st.session_state.selected_cities = []
    if "min_rating" not in st.session_state:
        st.session_state.min_rating = 3.0

    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=150)
    st.title("🍽️ Encuentra la mejor opción para tu paladar")
    st.markdown("### Encuentra el mejor restaurante y tipo de comida que mejor te guste")
    st.markdown("Utiliza los filtros en la barra lateral para especificar el tipo de comida, la calificación mínima y el estado (y ciudad).")
    
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
            default=st.session_state.selected_food_types
        )
        
        if len(selected_food_types) > 3:
            st.sidebar.error("Por favor, selecciona máximo 3 tipos de comida.")
        
        # Selector para calificación mínima
        min_rating = st.sidebar.number_input(
            "Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=st.session_state.min_rating, step=0.5
        )
        
        # Filtrar el DataFrame en base a los tipos de comida (si se han seleccionado) para determinar estados disponibles
        if selected_food_types:
            filtered_df = df[
                df["food_subcategory"].str.lower().apply(
                    lambda x: any(ft.lower() in x for ft in selected_food_types)
                )
            ]
        else:
            filtered_df = df
        
        # Determinar estados disponibles
        available_states = sorted(filtered_df["state"].unique())
        
        # Selector múltiple para estados usando el mapeo para mostrar nombres completos
        selected_states = st.sidebar.multiselect(
            "Estados disponibles",
            options=available_states,
            default=st.session_state.selected_states,
            format_func=lambda s: state_mapping.get(s, s)
        )
        
        # Filtrar también por los estados seleccionados para determinar ciudades disponibles  # <-- NUEVO
        if selected_states:
            filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
        
        # Determinar ciudades disponibles  # <-- NUEVO
        available_cities = sorted(filtered_df["city"].unique())
        
        # Selector múltiple para ciudades  # <-- NUEVO
        selected_cities = st.sidebar.multiselect(
            "Ciudades disponibles",
            options=available_cities,
            default=st.session_state.selected_cities
        )
        
        # Botón para buscar recomendaciones
        if st.sidebar.button("Buscar Recomendaciones"):
            st.session_state.results = recommend_restaurants(
                df,
                food_types=selected_food_types,
                min_rating=min_rating,
                states=selected_states,
                cities=selected_cities,  # <-- NUEVO
                top_n=10
            )
            st.session_state.selected_food_types = selected_food_types
            st.session_state.selected_states = selected_states
            st.session_state.selected_cities = selected_cities  # <-- NUEVO
            st.session_state.min_rating = min_rating
        
        # Botón para limpiar resultados y filtros
        if st.sidebar.button("Limpiar resultados"):
            st.session_state.results = None
            st.session_state.selected_food_types = []
            st.session_state.selected_states = []
            st.session_state.selected_cities = []  # <-- NUEVO
            st.session_state.min_rating = 3.0
        
        # Mostrar resultados con fondo semitransparente
        if st.session_state.results is not None:
            st.markdown("### Top 10 Recomendaciones")
            for idx, row in st.session_state.results.iterrows():
                st.markdown(
                    f"""
                    <div class='result-container'>
                        <h4>{row['name']}</h4>
                        <p><b>Estado:</b> {state_mapping.get(row['state'], row['state'])}</p>
                        <p><b>Ciudad:</b> {row['city']}</p>
                        <p><b>Dirección:</b> {row['address']}</p>  <!-- NUEVO -->
                        <p><b>Score:</b> {row['combined_score']:.2f}</p>
                        <p><b>Tipo de comida:</b> {row['food_subcategory']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    main()
