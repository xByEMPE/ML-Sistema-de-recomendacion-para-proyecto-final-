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
# ... (código previo sin cambios)

def recommend_restaurants(df, food_types=None, min_rating=None, states=None, cities=None, top_n=10):
    df_filter = df.copy()
    
    # Filtrar por tipos de comida
    if food_types:
        df_filter = df_filter[
            df_filter["food_subcategory"].str.lower().apply(
                lambda x: any(ft.lower() in x for ft in food_types)
            )
        ]
    
    # Filtrar por calificación mínima
    if min_rating is not None:
        df_filter = df_filter[df_filter["avg_rating"] >= min_rating]
    
    # Filtrar por estados
    if states:
        df_filter = df_filter[df_filter["state"].str.upper().isin([s.upper() for s in states])]
    
    # Filtrar por ciudades (nuevo filtro)
    if cities:
        df_filter = df_filter[df_filter["city"].str.upper().isin([c.upper() for c in cities])]
    
    # Ordenar y seleccionar columnas (incluir "address")
    df_filter = df_filter.sort_values("combined_score", ascending=False)
    columns = ["name", "state", "city", "address", "combined_score", "food_subcategory"]
    return df_filter[columns].head(top_n)

def main():
    # Inicializar variables de sesión para ciudades
    if "selected_cities" not in st.session_state:
        st.session_state.selected_cities = []
    # ... (resto de inicializaciones sin cambios)

    if df is not None:
        # ... (código previo sin cambios hasta la sección de filtros)
        
        # Aplicar filtros de comida y calificación para actualizar estados/ciudades
        filtered_df = df.copy()
        if selected_food_types:
            filtered_df = filtered_df[
                filtered_df["food_subcategory"].str.lower().apply(
                    lambda x: any(ft.lower() in x for ft in selected_food_types)
                )
            ]
        if min_rating is not None:
            filtered_df = filtered_df[filtered_df["avg_rating"] >= min_rating]

        # Selector de estados (actualizado para usar filtered_df)
        available_states = sorted(filtered_df["state"].unique())
        selected_states = st.sidebar.multiselect(
            "Estados disponibles",
            options=available_states,
            default=st.session_state.selected_states,
            format_func=lambda s: state_mapping.get(s, s)
        )

        # Filtrar ciudades basadas en estados seleccionados
        if selected_states:
            filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
        available_cities = sorted(filtered_df["city"].unique())

        # Selector de ciudades (nuevo)
        selected_cities = st.sidebar.multiselect(
            "Ciudades disponibles",
            options=available_cities,
            default=st.session_state.selected_cities
        )

        # Botón de búsqueda (actualizado para incluir ciudades)
        if st.sidebar.button("Buscar Recomendaciones"):
            st.session_state.results = recommend_restaurants(
                df, selected_food_types, min_rating, selected_states, selected_cities, top_n=10
            )
            st.session_state.selected_cities = selected_cities  # Guardar en sesión
            # ... (resto de variables de sesión sin cambios)

        # Botón de limpiar (actualizado para resetear ciudades)
        if st.sidebar.button("Limpiar resultados"):
            st.session_state.results = None
            st.session_state.selected_cities = []  # Limpiar ciudades
            # ... (resto de limpieza sin cambios)

        # Mostrar resultados con dirección
        if st.session_state.results is not None:
            st.markdown("### Top 10 Recomendaciones")
            for idx, row in st.session_state.results.iterrows():
                st.markdown(
                    f"""
                    <div class='result-container'>
                        <h4>{row['name']}</h4>
                        <p><b>Estado:</b> {state_mapping.get(row['state'], row['state'])}</p>
                        <p><b>Ciudad:</b> {row['city']}</p>
                        <p><b>Dirección:</b> {row['address']}</p>  <!-- Nueva línea -->
                        <p><b>Score:</b> {row['combined_score']:.2f}</p>
                        <p><b>Tipo de comida:</b> {row['food_subcategory']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
if __name__ == "__main__":
    main()
