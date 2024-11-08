# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Função de carregamento e processamento de dados com cache
@st.cache_data
def load_data():
    df = pd.read_csv('msss2024.csv', encoding='latin1')
    
    # Lista de colunas numéricas a serem processadas
    numeric_columns = [
        'All Time Rank', 'Track Score', 'Spotify Streams', 'Spotify Playlist Count',
        'Spotify Playlist Reach', 'Spotify Popularity', 'YouTube Views', 'YouTube Likes',
        'TikTok Posts', 'TikTok Likes', 'TikTok Views', 'YouTube Playlist Reach',
        'Apple Music Playlist Count', 'AirPlay Spins', 'SiriusXM Spins',
        'Deezer Playlist Count', 'Deezer Playlist Reach', 'Amazon Playlist Count',
        'Pandora Streams', 'Pandora Track Stations', 'Soundcloud Streams',
        'Shazam Counts', 'TIDAL Popularity'
    ]
    
    # Remover separadores de milhares e converter para numérico
    for column in numeric_columns:
        if column in df.columns:
            # Remover vírgulas e outros caracteres não numéricos, exceto pontos
            df[column] = pd.to_numeric(df[column].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    
    # Converter 'Release Date' para datetime
    if 'Release Date' in df.columns:
        df['Release Date'] = pd.to_datetime(df['Release Date'], errors='coerce')
    
    # Converter 'Explicit Track' para booleano
    if 'Explicit Track' in df.columns:
        df['Explicit Track'] = df['Explicit Track'].astype(str).str.lower().map({
            'yes': True, 'sim': True, 'no': False, 'não': False, 'true': True, 'false': False
        }).fillna(False)  # Preencher NaN com False caso existam
    
    return df

# Função de filtragem de dados com cache
@st.cache_data
def filter_data(df, artists, tracks, start_date, end_date, isrc):
    filtered = df
    if artists:
        filtered = filtered[filtered['Artist'].isin(artists)]
    if tracks:
        filtered = filtered[filtered['Track'].isin(tracks)]
    if start_date and end_date:
        filtered = filtered[
            (filtered['Release Date'] >= pd.to_datetime(start_date)) &
            (filtered['Release Date'] <= pd.to_datetime(end_date))
        ]
    if isrc:
        filtered = filtered[filtered['ISRC'].str.contains(isrc, na=False)]
    return filtered

def main():
    st.set_page_config(
        page_title="Dashboard: Músicas Mais Tocadas no Spotify - 2024",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("Dashboard: Músicas Mais Tocadas no Spotify - 2024")
    st.markdown("Explore os dados de músicas mais tocadas no Spotify em 2024 de forma interativa.")
    
    # Carregar os dados
    df = load_data()
    
    # Filtros principais na barra lateral
    st.sidebar.header("Filtros")
    artists = st.sidebar.multiselect(
        "Escolha o(s) Artista(s)", 
        options=df['Artist'].dropna().unique(),
        default=df['Artist'].dropna().unique()[:5]  # Seleção padrão dos primeiros 5 artistas
    )
    tracks = st.sidebar.multiselect(
        "Escolha a(s) Faixa(s)", 
        options=df['Track'].dropna().unique(),
        default=df['Track'].dropna().unique()[:5]  # Seleção padrão das primeiras 5 faixas
    )
    
    # Filtro por Data de Lançamento
    if 'Release Date' in df.columns:
        release_dates = df['Release Date'].dropna()
        min_date = release_dates.min()
        max_date = release_dates.max()
        start_date, end_date = st.sidebar.date_input(
            "Selecione o Intervalo de Datas de Lançamento",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        start_date, end_date = None, None
    
    # Busca por ISRC
    isrc_search = st.sidebar.text_input("Buscar por ISRC")
    
    # Aplicar filtros
    filtered_df = filter_data(df, artists, tracks, start_date, end_date, isrc_search)
    
    # Navegação por Abas
    tabs = st.tabs(["Visão Geral", "Plataformas", "Redes Sociais", "Playlists", "Detalhes da Faixa"])
    
    with tabs[0]:
        st.write("### Dados Gerais")
        st.dataframe(filtered_df.head())
        
        # KPIs
        total_streams = filtered_df['Spotify Streams'].sum()
        average_streams = filtered_df['Spotify Streams'].mean()
        unique_artists = filtered_df['Artist'].nunique()
        unique_tracks = filtered_df['Track'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Streams", f"{total_streams:,.0f}")
        col2.metric("Média de Streams por Faixa", f"{average_streams:,.2f}")
        col3.metric("Número de Artistas Únicos", unique_artists)
        col4.metric("Número de Faixas Únicas", unique_tracks)
        
        # Gráfico de Distribuição por Álbum (substituindo gênero)
        if 'Album Name' in filtered_df.columns:
            album_distribution = filtered_df['Album Name'].value_counts().reset_index()
            album_distribution.columns = ['Album Name', 'Count']
            fig_album = px.pie(
                album_distribution.head(10), 
                names='Album Name', 
                values='Count', 
                title='Distribuição de Faixas por Álbum'
            )
            st.plotly_chart(fig_album, use_container_width=True)
        else:
            st.info("A coluna 'Album Name' não está disponível para distribuição.")
    
    with tabs[1]:
        st.write("### Análise Multiplataforma de Streams e Engajamento")
        if 'Track' in filtered_df.columns:
            selected_track = st.selectbox(
                "Selecione uma Faixa para Comparar Plataformas", 
                options=filtered_df['Track'].dropna().unique()
            )
            if selected_track:
                track_data = filtered_df[filtered_df['Track'] == selected_track].iloc[0]
                platforms = [
                    'Spotify Streams', 'YouTube Views', 'TikTok Views',
                    'Deezer Playlist Reach', 'Amazon Playlist Count',
                    'Pandora Streams', 'Soundcloud Streams'
                ]
                # Filtrar apenas plataformas presentes no DataFrame
                available_platforms = [p for p in platforms if p in filtered_df.columns]
                values = [track_data.get(platform, 0) for platform in available_platforms]
                
                # Garantir que todos os valores são numéricos e >= 0
                values = [v if v >= 0 else 0 for v in values]
                
                if any(values):
                    fig_radar = go.Figure(
                        data=go.Scatterpolar(r=values, theta=available_platforms, fill='toself'),
                        layout=go.Layout(title=f'Comparação de Plataformas para a Faixa: {selected_track}')
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.info("Nenhuma plataforma disponível para comparação.")
        else:
            st.info("A coluna 'Track' não está disponível para seleção.")
    
    with tabs[2]:
        st.write("### Análise de Engajamento em Redes Sociais")
        # Selecionar quais colunas usar para correlação
        corr_columns = ['Spotify Streams']
        social_columns = ['YouTube Views', 'YouTube Likes', 'TikTok Views', 'TikTok Likes']
        corr_columns += [col for col in social_columns if col in filtered_df.columns]
        
        if len(corr_columns) > 1:
            corr_data = filtered_df[corr_columns].corr()
            fig_corr = px.imshow(
                corr_data,
                text_auto=True,
                color_continuous_scale='RdBu',
                title='Mapa de Calor de Correlação entre Streams e Engajamento nas Redes Sociais'
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Não há colunas suficientes para calcular a correlação.")
    
    with tabs[3]:
        st.write("### Análise de Alcance das Playlists")
        playlist_columns = ['Spotify Playlist Count', 'Spotify Playlist Reach']
        available_playlist_columns = [col for col in playlist_columns if col in filtered_df.columns]
        
        if available_playlist_columns:
            playlist_data = filtered_df[available_playlist_columns + ['Spotify Streams']].dropna()
            if not playlist_data.empty:
                corr_playlists = playlist_data.corr()
                
                fig_corr_playlists = px.imshow(
                    corr_playlists,
                    text_auto=True,
                    color_continuous_scale='RdBu',
                    title='Correlação entre Playlists e Streams no Spotify'
                )
                st.plotly_chart(fig_corr_playlists, use_container_width=True)
                
                # Gráfico de Dispersão: Número de Playlists vs Streams
                # Garantir que 'Spotify Playlist Reach' não contenha NaN
                filtered_df_plot = filtered_df.dropna(subset=['Spotify Playlist Reach'])
                
                if not filtered_df_plot.empty:
                    fig_scatter = px.scatter(
                        filtered_df_plot, 
                        x='Spotify Playlist Count', 
                        y='Spotify Streams',
                        size='Spotify Playlist Reach' if 'Spotify Playlist Reach' in filtered_df_plot.columns else None,
                        color='Artist' if 'Artist' in filtered_df_plot.columns else None,
                        title='Relação entre Número de Playlists e Streams no Spotify',
                        labels={'Spotify Playlist Count': 'Número de Playlists', 'Spotify Streams': 'Streams'},
                        hover_data=['Track', 'Artist'] if 'Track' in filtered_df_plot.columns and 'Artist' in filtered_df_plot.columns else None
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("Nenhum dado disponível para o gráfico de dispersão após remover valores NaN em 'Spotify Playlist Reach'.")
            else:
                st.info("Nenhum dado disponível após a aplicação dos filtros para análise de playlists.")
        else:
            st.info("Colunas de playlist não estão disponíveis para análise.")
    
    with tabs[4]:
        st.write("### Detalhes da Faixa Selecionada")
        if 'Track' in filtered_df.columns:
            selected_track_detail = st.selectbox(
                "Selecione uma Faixa para Ver Detalhes", 
                options=filtered_df['Track'].dropna().unique()
            )
            if selected_track_detail:
                track_details = filtered_df[filtered_df['Track'] == selected_track_detail].iloc[0]
                st.write(f"**Nome da Faixa:** {track_details['Track']}")
                st.write(f"**Artista:** {track_details['Artist']}")
                st.write(f"**Álbum:** {track_details['Album Name']}")
                st.write(f"**Data de Lançamento:** {track_details['Release Date'].strftime('%Y-%m-%d') if pd.notnull(track_details['Release Date']) else 'N/A'}")
                st.write(f"**ISRC:** {track_details['ISRC']}")
                st.write(f"**Classificação Geral:** {track_details['All Time Rank']}")
                st.write(f"**Pontuação da Faixa:** {track_details['Track Score']}")
                st.write(f"**Faixa Explícita:** {'Sim' if track_details['Explicit Track'] else 'Não'}")
                # Outras métricas
                st.write(f"**Spotify Streams:** {track_details['Spotify Streams']:,.0f}")
                st.write(f"**Spotify Playlist Count:** {track_details['Spotify Playlist Count']}")
                st.write(f"**Spotify Playlist Reach:** {track_details['Spotify Playlist Reach']:,.0f}")
                st.write(f"**Spotify Popularity:** {track_details['Spotify Popularity']}")
                if 'YouTube Views' in track_details and pd.notnull(track_details['YouTube Views']):
                    st.write(f"**YouTube Views:** {track_details['YouTube Views']:,.0f}")
                if 'YouTube Likes' in track_details and pd.notnull(track_details['YouTube Likes']):
                    st.write(f"**YouTube Likes:** {track_details['YouTube Likes']:,.0f}")
                if 'TikTok Posts' in track_details and pd.notnull(track_details['TikTok Posts']):
                    st.write(f"**TikTok Posts:** {track_details['TikTok Posts']}")
                if 'TikTok Likes' in track_details and pd.notnull(track_details['TikTok Likes']):
                    st.write(f"**TikTok Likes:** {track_details['TikTok Likes']:,.0f}")
                if 'TikTok Views' in track_details and pd.notnull(track_details['TikTok Views']):
                    st.write(f"**TikTok Views:** {track_details['TikTok Views']:,.0f}")
                if 'YouTube Playlist Reach' in track_details and pd.notnull(track_details['YouTube Playlist Reach']):
                    st.write(f"**YouTube Playlist Reach:** {track_details['YouTube Playlist Reach']:,.0f}")
                if 'Apple Music Playlist Count' in track_details and pd.notnull(track_details['Apple Music Playlist Count']):
                    st.write(f"**Apple Music Playlist Count:** {track_details['Apple Music Playlist Count']}")
                if 'AirPlay Spins' in track_details and pd.notnull(track_details['AirPlay Spins']):
                    st.write(f"**AirPlay Spins:** {track_details['AirPlay Spins']}")
                if 'SiriusXM Spins' in track_details and pd.notnull(track_details['SiriusXM Spins']):
                    st.write(f"**SiriusXM Spins:** {track_details['SiriusXM Spins']}")
                if 'Deezer Playlist Count' in track_details and pd.notnull(track_details['Deezer Playlist Count']):
                    st.write(f"**Deezer Playlist Count:** {track_details['Deezer Playlist Count']}")
                if 'Deezer Playlist Reach' in track_details and pd.notnull(track_details['Deezer Playlist Reach']):
                    st.write(f"**Deezer Playlist Reach:** {track_details['Deezer Playlist Reach']:,.0f}")
                if 'Amazon Playlist Count' in track_details and pd.notnull(track_details['Amazon Playlist Count']):
                    st.write(f"**Amazon Playlist Count:** {track_details['Amazon Playlist Count']}")
                if 'Pandora Streams' in track_details and pd.notnull(track_details['Pandora Streams']):
                    st.write(f"**Pandora Streams:** {track_details['Pandora Streams']:,.0f}")
                if 'Pandora Track Stations' in track_details and pd.notnull(track_details['Pandora Track Stations']):
                    st.write(f"**Pandora Track Stations:** {track_details['Pandora Track Stations']}")
                if 'Soundcloud Streams' in track_details and pd.notnull(track_details['Soundcloud Streams']):
                    st.write(f"**Soundcloud Streams:** {track_details['Soundcloud Streams']:,.0f}")
                if 'Shazam Counts' in track_details and pd.notnull(track_details['Shazam Counts']):
                    st.write(f"**Shazam Counts:** {track_details['Shazam Counts']:,.0f}")
                if 'TIDAL Popularity' in track_details and pd.notnull(track_details['TIDAL Popularity']):
                    st.write(f"**TIDAL Popularity:** {track_details['TIDAL Popularity']}")
        else:
            st.info("A coluna 'Track' não está disponível para seleção.")
    
    # Botão de Download de Dados Filtrados
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')
    
    csv_data = convert_df_to_csv(filtered_df)
    
    st.download_button(
        label="Download dos Dados Filtrados",
        data=csv_data,
        file_name='dados_filtrados_spotify_2024.csv',
        mime='text/csv',
    )
    
if __name__ == "__main__":
    main()
