import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Meteo WW2", layout="wide")

@st.cache_data
def load_data():
    df_weather = pd.read_csv('sumweather.csv', low_memory=False)
    df_stations = pd.read_csv('weatherstation.csv')
    df_final = pd.merge(df_weather, df_stations, left_on='STA', right_on='WBAN')
    df_final['Precip'] = pd.to_numeric(df_final['Precip'].replace('T', '0'), errors='coerce').fillna(0)
    df_final['Date'] = pd.to_datetime(df_final['Date'], errors='coerce')
    
    if 'Latitude' in df_final.columns and 'Longitude' in df_final.columns:
        df_final = df_final.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})
    
    df_final['lat'] = pd.to_numeric(df_final['lat'], errors='coerce')
    df_final['lon'] = pd.to_numeric(df_final['lon'], errors='coerce')
    return df_final

df = load_data()
df = df.assign(Temp_Amplitude=df.apply(lambda x: x['MaxTemp'] - x['MinTemp'], axis=1))

st.title("Analyse Meteorologique de la Seconde Guerre Mondiale")

pays_disponibles = sorted(df['STATE/COUNTRY ID'].dropna().unique())
pays_selectionnes = st.sidebar.multiselect("Filtrer par pays (Optionnel)", pays_disponibles)

df_map = df[['lat', 'lon', 'NAME', 'STATE/COUNTRY ID']].dropna().drop_duplicates()

st.subheader("1. Cartographie interactive des stations meteorologiques")

if not df_map.empty:
    fig_map = px.scatter_map(
        df_map, 
        lat='lat', 
        lon='lon', 
        hover_name='NAME',
        custom_data=['STATE/COUNTRY ID'],
        color='STATE/COUNTRY ID',
        zoom=1.2,
        map_style="open-street-map"
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    
    map_event = st.plotly_chart(fig_map, width="stretch", on_select="rerun")
else:
    map_event = None
    st.warning("Aucune coordonnee geographique disponible.")

pays_actifs = pays_selectionnes.copy()

if map_event and "selection" in map_event and map_event["selection"]["points"]:
    pays_clique = map_event["selection"]["points"][0]["customdata"][0]
    if pays_clique not in pays_actifs:
        pays_actifs.append(pays_clique)

if pays_actifs:
    df_filtre = df[df['STATE/COUNTRY ID'].isin(pays_actifs)]
    st.write(f"Donnees affichees pour : {', '.join(pays_actifs)}")
else:
    df_filtre = df
    st.write("Analyse globale (Tous les pays - Moyenne Mondiale)")

st.subheader("2. Evolution des temperatures avec contexte historique")

if not pays_actifs:
    df_evolution = df.groupby('Date')['MeanTemp'].mean().reset_index()
    df_evolution['STATE/COUNTRY ID'] = 'Moyenne Mondiale'
else:
    df_evolution = df_filtre.groupby(['Date', 'STATE/COUNTRY ID'])['MeanTemp'].mean().reset_index()

fig_line = px.line(df_evolution, x='Date', y='MeanTemp', color='STATE/COUNTRY ID')

evenements = {
    '1939-09-01': 'Invasion Pologne',
    '1941-06-22': 'Op. Barbarossa',
    '1941-12-07': 'Pearl Harbor',
    '1944-06-06': 'Debarquement',
    '1945-05-08': 'Cap. Allemagne',
    '1945-09-02': 'Cap. Japon'
}

min_date = df_evolution['Date'].min()
max_date = df_evolution['Date'].max()

for date_str, event in evenements.items():
    date_evt = pd.to_datetime(date_str)
    if min_date <= date_evt <= max_date:
        timestamp_ms = date_evt.timestamp() * 1000
        fig_line.add_vline(x=timestamp_ms, line_dash="dash", line_color="red", annotation_text=event)
        
st.plotly_chart(fig_line, width="stretch")

st.subheader("3. Vagues de temperatures extremes (Plus de 4 jours consecutifs)")
df_extremes = df_filtre[(df_filtre['MinTemp'] < 0) | (df_filtre['MaxTemp'] > 35)].copy()

if not df_extremes.empty:
    df_extremes = df_extremes.sort_values(by=['STA', 'Date'])
    
    df_extremes['Diff_Jours'] = df_extremes.groupby('STA')['Date'].diff().dt.days
    df_extremes['Nouveau_Groupe'] = (df_extremes['Diff_Jours'] > 1).cumsum()
    
    vagues_extremes = df_extremes.groupby(['STA', 'Nouveau_Groupe']).agg(
        Date_Debut=('Date', 'min'),
        Date_Fin=('Date', 'max'),
        Duree_Jours=('Date', 'count'),
        MinTemp=('MinTemp', 'min'),
        MaxTemp=('MaxTemp', 'max'),
        MeanTemp=('MeanTemp', 'mean'),
        Ville=('NAME', 'first'),
        Pays=('STATE/COUNTRY ID', 'first')
    ).reset_index()
    
    vagues_filtrees = vagues_extremes[vagues_extremes['Duree_Jours'] > 4].copy()
    
    if not vagues_filtrees.empty:
        vagues_filtrees['Date_Debut'] = vagues_filtrees['Date_Debut'].dt.strftime('%Y-%m-%d')
        vagues_filtrees['Date_Fin'] = vagues_filtrees['Date_Fin'].dt.strftime('%Y-%m-%d')
        
        colonnes_finales = ['Date_Debut', 'Date_Fin', 'Duree_Jours', 'MaxTemp', 'MinTemp', 'MeanTemp', 'Ville', 'Pays']
        vagues_filtrees = vagues_filtrees[colonnes_finales].sort_values(by='Date_Debut')
        
        st.metric(label="Nombre de vagues extremes identifiees", value=len(vagues_filtrees))
        st.dataframe(vagues_filtrees)
    else:
        st.info("Aucune vague de temperatures extremes de plus de 4 jours consecutifs n'a ete enregistree pour cette selection.")
else:
    st.info("Aucun jour de temperature extreme n'a ete enregistre pour cette selection.")