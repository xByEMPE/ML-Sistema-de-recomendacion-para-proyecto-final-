import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Modelo de ML", layout="wide")

# URL de la imagen de fondo
background_image = "https://cdn.pixabay.com/photo/2016/10/04/05/21/bar-1713610_1280.jpg"

# Inyección de CSS para mejorar visibilidad
custom_css = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: url("{background_image}") no-repeat center center fixed;
    background-size: cover;
}}
.result-container {{
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: white;
}}
h1, h2, h3 {{ color: white !important; }}
[data-testid="stSidebar"] {{
    background: rgba(0, 0, 0, 0.8) !important;
    color: white;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

CSV_PATH = "datos_preprocesados (1).csv"

state_mapping = {
    "AZ": "Arizona", "PA": "Pennsylvania", "LA": "Louisiana", "CA": "California",
    "MO": "Missouri", "AB": "Alberta", "IN": "Indiana", "NV": "Nevada",
    "NJ": "New Jersey", "FL": "Florida", "TN": "Tennessee", "IL": "Illinois",
    "DE": "Delaware", "ID": "Idaho", "CO": "Colorado", "HI": "Hawaii",
    "MI": "Michigan", "TX": "Texas", "VT": "Vermont", "WA": "Washington",
    "VI": "Virgin Islands"
}

@st.cache_data
def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        st.error("El archivo CSV no se encontró. Ejecuta primero el notebook para generar el CSV.")
        return None

def recommend_restaurants(df, food_types=None, min_rating=None, states=None, cities=None, top_n=10):
    df_filter = df.copy()
    
    if food_types:
        df_filter = df_filter[
            df_filter["food_subcategory"].str.lower().apply(
                lambda x: any(ft.lower() in x for ft in food_types)
            )
        ]
    
    if min_rating is not None:
        df_filter = df_filter[df_filter["avg_rating"] >= min_rating]
    
    if states:
        df_filter = df_filter[
            df_filter["state"].str.upper().isin([s.upper() for s in states])
        ]
    
    if cities:
        df_filter = df_filter[
            df_filter["city"].str.lower().isin([c.lower() for c in cities])
        ]
    
    df_filter = df_filter.sort_values("combined_score", ascending=False)
    columns = ["name", "state", "city", "address", "combined_score", "food_subcategory"]
    return df_filter[columns].head(top_n)

def main():
    if "results" not in st.session_state:
        st.session_state.results = None
    if "selected_food_types" not in st.session_state:
        st.session_state.selected_food_types = []
    if "selected_states" not in st.session_state:
        st.session_state.selected_states = []
    if "selected_cities" not in st.session_state:
        st.session_state.selected_cities = []
    if "min_rating" not in st.session_state:
        st.session_state.min_rating = 3.0

    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=150)
    st.title("🍽️ Encuentra la mejor opción para tu paladar")
    st.markdown("### Encuentra el mejor restaurante y tipo de comida que mejor te guste")
    st.markdown("Utiliza los filtros en la barra lateral para especificar el tipo de comida, la calificación mínima, el estado y la ciudad.")
    
    df = load_data()
    if df is not None:
        st.sidebar.header("Filtros de Búsqueda")
        
        available_food_types = sorted(df["food_subcategory"].dropna().unique())
        selected_food_types = st.sidebar.multiselect("Tipos de comida disponibles", options=available_food_types, default=st.session_state.selected_food_types)
        
        min_rating = st.sidebar.number_input("Calificación mínima (1 a 5)", min_value=1.0, max_value=5.0, value=st.session_state.min_rating, step=0.5)
        
        available_states = sorted(df["state"].unique())
        selected_states = st.sidebar.multiselect("Estados disponibles", options=available_states, default=st.session_state.selected_states, format_func=lambda s: state_mapping.get(s, s))
        
        available_cities = sorted(df[df["state"].isin(selected_states)]["city"].unique()) if selected_states else sorted(df["city"].unique())
        selected_cities = st.sidebar.multiselect("Ciudades disponibles", options=available_cities, default=st.session_state.selected_cities)
        
        if st.sidebar.button("Buscar Recomendaciones"):
            st.session_state.results = recommend_restaurants(df, selected_food_types, min_rating, selected_states, selected_cities, top_n=10)
            st.session_state.selected_food_types = selected_food_types
            st.session_state.selected_states = selected_states
            st.session_state.selected_cities = selected_cities
            st.session_state.min_rating = min_rating
        
        if st.sidebar.button("Limpiar resultados"):
            st.session_state.results = None
            st.session_state.selected_food_types = []
            st.session_state.selected_states = []
            st.session_state.selected_cities = []
            st.session_state.min_rating = 3.0
        
        if st.session_state.results is not None:
            st.markdown("### Top 10 Recomendaciones")
            for idx, row in st.session_state.results.iterrows():
                st.markdown(
                    f"""
                    <div class='result-container'>
                        <h4>{row['name']}</h4>
                        <p><b>Estado:</b> {state_mapping.get(row['state'], row['state'])}</p>
                        <p><b>Ciudad:</b> {row['city']}</p>
                        <p><b>Dirección:</b> {row['address']}</p>
                        <p><b>Score:</b> {row['combined_score']:.2f}</p>
                        <p><b>Tipo de comida:</b> {row['food_subcategory']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    main()
