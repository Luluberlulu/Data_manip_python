import streamlit as st
import pandas as pd


@st.cache_data
def load_data():
    # Chargement des fichiers CSV
    df_weather = pd.read_csv('sumweather.csv', low_memory=False)
    df_stations = pd.read_csv('weatherstation.csv')
    
    # Fusion (Merge) des deux tables
    # sumweather utilise 'STA' et weatherstation utilise 'WBAN' comme identifiant
    # C'est cette fusion qui permet d'ajouter la colonne 'STATE/COUNTRY ID' à vos données météo
    df_final = pd.merge(df_weather, df_stations, left_on='STA', right_on='WBAN')
    
    # Nettoyage de la colonne Precip (remplace les 'T' par 0 pour permettre les calculs)
    df_final['Precip'] = pd.to_numeric(df_final['Precip'].replace('T', '0'), errors='coerce').fillna(0)
    
    st.map(data=df_final, latitude="Latitude", longitude="Longitude", color="#8b0000", size=None, zoom=None, width="stretch", height=500, use_container_width=None)

    return df_final

# Initialisation du DataFrame global
df = load_data()

# Interface Streamlit
st.title("Analyse météo pendant la seconde guerre mondiale")

# Utilisation de la colonne issue de la fusion dans la sidebar
pays_disponibles = df['STATE/COUNTRY ID'].unique()
pays_selectionnes = st.sidebar.multiselect("Choisir un pays", pays_disponibles)

# Filtrage et affichage
if pays_selectionnes:
    df_filtre = df[df['STATE/COUNTRY ID'].isin(pays_selectionnes)]
    st.write(f"Affichage des données pour : {', '.join(pays_selectionnes)}")

    st.dataframe(df_filtre)
else:
    st.write("Veuillez sélectionner un pays dans la barre latérale.")
    st.dataframe(df.head())
    
