import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output
import random
import geopandas as gpd
import unicodedata
from shapely.geometry import Point, Polygon


app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    suppress_callback_exceptions=True
)

app.title = "Dashboard de Análise"


df = pd.read_csv('df/dataset_IC_certoV2.csv', sep=';')

def normalizar_nome(nome):
   
        if isinstance(nome, str):
            return ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')
        else:
            
            return nome


df['municipio'] = df['municipio'].apply(normalizar_nome)

df['municipioIBGE'] = df['municipioIBGE'].astype(str).str.zfill(7).fillna('Desconhecido')


app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'
    ),

    html.Div(
        className="header",
        children=[
            html.Img(src='/assets/DotLab.png', className="header-image"),
            "Plataforma interativa para visualização dos dados das notificações de síndrome gripal do estado de Pernambuco."
        ]
    ),

    dbc.Container([
        
        html.Div(className="filters", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Raça:"),
                    dcc.Dropdown(
                        id='filtro-raca',
                        options=[{'label': raca, 'value': raca} for raca in df['racaCor'].dropna().unique()],
                        placeholder="Selecione a raça",
                        className="dropdown"
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Sexo:"),
                    dcc.Dropdown(
                        id='filtro-sexo',
                        options=[{'label': sexo, 'value': sexo} for sexo in df['sexo'].dropna().unique()],
                        placeholder="Selecione o sexo",
                        className="dropdown"
                    )
                ], width=4),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Página 1", id="botao-pagina-1", color="primary", outline=False),
                        dbc.Button("Página 2", id="botao-pagina-2", color="secondary", outline=True),
                    ], className="pagination-buttons")
                ], width=4)
            ])
        ]),

        
        html.Div(id='conteudo-pagina', children=[
            dcc.Loading(
                id="loading-pagina",
                type="circle",
                children=html.Div(id="pagina-conteudo")
            )
        ])
    ], style={'fontFamily': 'Poppins, sans-serif'}, fluid=True)
])


@app.callback(
    Output('pagina-conteudo', 'children'),
    [Input('botao-pagina-1', 'n_clicks'),
     Input('botao-pagina-2', 'n_clicks')]
)
def navegar_paginas(botao1, botao2):
    ctx = dash.callback_context
    pagina = 'pagina1'  

    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == "botao-pagina-2":
            pagina = 'pagina2'

    if pagina == 'pagina1':
        return [
            dbc.Row(dbc.Col(dcc.Graph(id='grafico-classificacao'), width=8, lg={"size": 8, "offset": 2})),
            dbc.Row(dbc.Col(dcc.Graph(id='grafico-evolucao'), width=8, lg={"size": 8, "offset": 2})),
            dbc.Row(dbc.Col(dcc.Graph(id='grafico-condicoes'), width=8, lg={"size": 8, "offset": 2}))
        ]
    
    return [
        dbc.Row(dbc.Col(dcc.Graph(id='grafico-piramide-etaria'), width=12, lg={"size": 8, "offset": 2})),
        dbc.Row(dbc.Col(dcc.Graph(id='grafico-sankey'), width=12, lg={"size": 8, "offset": 2})),
        dbc.Row(dbc.Col(dcc.Graph(id='grafico-mapa-calor'), width=12, lg={"size": 8, "offset": 2}))
    ]

@app.callback(
    [Output('grafico-piramide-etaria', 'figure'),
     Output('grafico-sankey', 'figure'),
     Output('grafico-mapa-calor', 'figure')],
    [Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def criar_graficos(filtro_raca, filtro_sexo):
    
    filtros = pd.Series(True, index=df.index)
    if filtro_raca:
        filtros &= df['racaCor'] == filtro_raca
    if filtro_sexo:
        filtros &= df['sexo'] == filtro_sexo
    
    df_filtrado = df.loc[filtros].copy()

    
    df_filtrado['faixa_etaria'] = df_filtrado['faixa_etaria'].astype(str).fillna('Desconhecido')
    df_filtrado = df_filtrado[df_filtrado['faixa_etaria'] != 'nan']

    def agrupar_idades(faixa):
        if ' a ' in faixa:
            inicio_faixa = int(faixa.split(' a ')[0])
        elif '+' in faixa:
            inicio_faixa = int(faixa.split('+')[0])
        else:
            return faixa
        return '55+' if inicio_faixa >= 55 else faixa

    df_filtrado['faixa_etaria'] = df_filtrado['faixa_etaria'].apply(agrupar_idades)

    
    categorias_ordenadas = sorted(
        df_filtrado['faixa_etaria'].unique(),
        key=lambda x: int(x.split(' a ')[0]) if ' a ' in x and x != '55+' else (float('inf') if x == '55+' else int(x.split('+')[0]))
    )

    df_filtrado['faixa_etaria'] = pd.Categorical(df_filtrado['faixa_etaria'], categories=categorias_ordenadas, ordered=True)

    
    piramide_data = df_filtrado.groupby(['faixa_etaria', 'sexo']).size().reset_index(name='contagem')
    piramide_data['contagem_negativa'] = piramide_data['contagem'] * piramide_data['sexo'].map({'Feminino': -1, 'Masculino': 1})
    piramide_data['percentual'] = piramide_data['contagem'] / piramide_data['contagem'].sum() * 100
    piramide_data['texto'] = piramide_data.apply(lambda row: f"{row['contagem']} ({row['percentual']:.1f}%)", axis=1)

    
    fig_piramide = px.bar(
        piramide_data,
        x='contagem_negativa',
        y='faixa_etaria',
        color='sexo',
        orientation='h',
        title='<b>Pirâmide Etária</b>',
        labels={'faixa_etaria': 'Faixa Etária', 'contagem_negativa': 'Contagem', 'sexo': 'Sexo'},
        color_discrete_map={'Masculino': '#1f77b4', 'Feminino': '#e377c2'},
        text='texto'
    )

    
    fig_piramide.update_layout(
        template='plotly_white',
        height=700,
        bargap=0.1,
        title=dict(x=0.5, xanchor='center', font=dict(size=20, family='Poppins, sans-serif', color="black", weight='bold')),
        xaxis=dict(title=dict(text='População', font=dict(size=14, family='Poppins, sans-serif', color="black")), showgrid=True, zeroline=True, zerolinewidth=1.5, zerolinecolor='gray'),
        yaxis=dict(title=dict(text='Faixa Etária', font=dict(size=14, family='Poppins, sans-serif', color="black")), showgrid=False),
        legend=dict(title='<b>Sexo</b>', font=dict(size=12, family='Poppins, sans-serif'), bgcolor='rgba(240,240,240,0.8)', bordercolor='gray', borderwidth=1),
        transition={'duration': 800, 'easing': 'cubic-in-out'}
    )

   
    fig_piramide.update_traces(marker_line_width=1, marker_line_color='black', textposition='outside')
    fig_piramide.for_each_trace(lambda t: t.update(textposition='outside' if t.name == 'Masculino' else 'inside'))
    
    
    
    df_filtrado.fillna({
        'sintomas': 'Não Informado',
        'evolucaoCaso': 'Desconhecido',
        'classificacaoFinal': 'Não Classificado'
    }, inplace=True)

    
    mapeamento_classificacao = {
        'confirmado laboratorial': 'Confirmado',
        'confirmado clínico-imagem': 'Confirmado',
        'confirmado por critério clínico': 'Confirmado',
        'confirmação laboratorial': 'Confirmado',
        'confirmado clínico-epidemiológico': 'Confirmado',
        'confirmado critério clínico': 'Confirmado'
    }

    df_filtrado['classificacaoFinal'] = (
        df_filtrado['classificacaoFinal'].str.strip().str.lower()
        .replace(mapeamento_classificacao)
        .str.capitalize()
    )

    
    colunas_sankey = ['sintomas', 'classificacaoFinal', 'evolucaoCaso']
    sankey_data = pd.concat([
        df_filtrado.groupby([colunas_sankey[i], colunas_sankey[i + 1]])
        .size()
        .reset_index(name='fluxo')
        .rename(columns={colunas_sankey[i]: 'categoria_origem', colunas_sankey[i + 1]: 'categoria_destino'})
        for i in range(len(colunas_sankey) - 1)
    ], ignore_index=True)

    
    todos_os_nos = list(set(sankey_data['categoria_origem']).union(set(sankey_data['categoria_destino'])))
    indices_nos = {nome: i for i, nome in enumerate(todos_os_nos)}

    
    cores_nos_definidas = {
        'Cura': '#00995E', 'Óbito': '#000000', 'Febre': '#FFC567',
        'Confirmado': '#FD5A46', 'Não Classificado': '#058CD7',
        'Não Informado': '#B0BEC5', 'Desconhecido': '#607D8B'
    }

    def gerar_cor_aleatoria():
        return f'#{random.randint(0, 0xFFFFFF):06x}'

    cores_nos = [cores_nos_definidas.get(categoria, gerar_cor_aleatoria()) for categoria in todos_os_nos]

   
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20, thickness=30, line=dict(color="black", width=0.5),
            label=todos_os_nos, color=cores_nos
        ),
        link=dict(
            source=sankey_data['categoria_origem'].map(indices_nos).tolist(),
            target=sankey_data['categoria_destino'].map(indices_nos).tolist(),
            value=sankey_data['fluxo'].tolist(),
            color="rgba(0, 123, 255, 0.4)",
            line=dict(color="rgba(0, 123, 255, 0.8)", width=1)
        )
    )])

   
    fig_sankey.update_layout(
        title_text="Fluxo de Sintomas, Classificação e Evolução dos Casos",
        title_font=dict(size=22, family='Poppins, sans-serif', color='black'),
        font_size=14, height=700, template="plotly_white", showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        title={'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'}
    )

    
   
    casos_por_municipio = (
        df_filtrado.groupby('municipioNotificacao', as_index=False)
        .agg(casos=('municipioNotificacao', 'count'))
    )

    
    casos_por_municipio['municipioNotificacao'] = casos_por_municipio['municipioNotificacao'].apply(normalizar_nome)

    
    gdf_municipios = gpd.read_file('df/PE_Municipios_2023.shp')
    gdf_mapa = gdf_municipios.merge(casos_por_municipio, left_on='NM_MUN', right_on='municipioNotificacao', how='left')

    
    gdf_mapa['casos'] = gdf_mapa['casos'].fillna(0)

    
    gdf_mapa['latitude'] = gdf_mapa.geometry.centroid.y
    gdf_mapa['longitude'] = gdf_mapa.geometry.centroid.x

    
    fig_mapa_calor = go.Figure()

    
    fig_mapa_calor.add_trace(go.Scattermapbox(
        lat=gdf_mapa['latitude'],
        lon=gdf_mapa['longitude'],
        mode='markers',
        marker=dict(
            size=gdf_mapa['casos'],
            color=gdf_mapa['casos'],
            colorscale='Viridis',
            sizemin=5,
            sizeref=2.0 * max(gdf_mapa['casos']) / 100 ** 2,
            sizemode='area'
        ),
        text=gdf_mapa['NM_MUN'],
        hovertemplate=(
            "<b>Município:</b> %{text}<br>"
            "<b>Casos:</b> %{marker.size:,}<extra></extra>"
        ),
        showlegend=False
    ))

    
    def extrair_coordenadas(geom):
        """ Extrai coordenadas (lat, lon) de um Polygon ou MultiPolygon """
        if geom.geom_type == 'Polygon':
            return [list(zip(*geom.exterior.coords.xy))]
        elif geom.geom_type == 'MultiPolygon':
            return [list(zip(*poly.exterior.coords.xy)) for poly in geom.geoms]
        return []

    
    for _, row in gdf_mapa.iterrows():
        for coords in extrair_coordenadas(row.geometry):
            lons, lats = zip(*coords)
            fig_mapa_calor.add_trace(go.Scattermapbox(
                lat=lats, lon=lons,
                mode='lines',
                line=dict(width=1, color='black'),
                hoverinfo='none',
                showlegend=False
            ))

    
    fig_mapa_calor.update_layout(
        mapbox=dict(
            style='carto-positron',
            zoom=6.5,
            center=dict(lat=-8.5, lon=-37.8),  
        ),
        margin=dict(r=0, t=50, l=0, b=0),
        height=700,
        title=dict(
            text="Mapa de Casos por Município - Síndrome Gripal",
            x=0.5, xanchor='center',
            font=dict(size=20, family='Poppins, sans-serif', color="black")
        )
    )


    return fig_piramide, fig_sankey, fig_mapa_calor 



    

@app.callback(
    [Output('grafico-classificacao', 'figure'),
     Output('grafico-evolucao', 'figure'),
     Output('grafico-condicoes', 'figure')],
    [Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def atualizar_graficos(filtro_raca, filtro_sexo):
    
    filtros = pd.Series(True, index=df.index)

    
    if filtro_raca:
        filtros &= df['racaCor'] == filtro_raca
    if filtro_sexo:
        filtros &= df['sexo'] == filtro_sexo
    
    df_filtrado = df[filtros]

   
    grouped_df = df_filtrado.groupby(['sintomas', 'classificacaoFinal']).size().reset_index(name='count')

   
    fig_classificacao = px.bar(
        grouped_df, 
        x='sintomas', 
        y='count', 
        color='classificacaoFinal',
        title='Classificação Final X Sintomas',
        labels={'count': 'Número de Casos', 'sintomas': 'Sintomas'},
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    
    fig_classificacao.update_layout(
        title={'text': '<b>Classificação Final por Sintomas</b>', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis=dict(categoryorder='total descending', title_font=dict(size=16, family='Poppins, sans-serif', color='black')),
        yaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black')),
        legend=dict(title='<b>Classificação Final:</b>', font=dict(size=14, family='Poppins, sans-serif', color='black'), bgcolor='rgba(240,240,240,0.8)', bordercolor='gray', borderwidth=1),
        margin=dict(l=50, r=50, t=80, b=50),
        bargap=0.2,
        bargroupgap=0.1,
        plot_bgcolor='rgba(240,240,240,0.5)',
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'  
        }
    )

    fig_classificacao.update_traces(marker=dict(line=dict(color='black', width=1)))

    
    evolucao_count = df_filtrado['evolucaoCaso'].value_counts().reset_index()
    evolucao_count.columns = ['evolucaoCaso', 'Contagem']  

    
    fig_evolucao = px.bar(
        evolucao_count, 
        x='evolucaoCaso',  
        y='Contagem', 
        title='<b>Contagem de Evolução de Casos</b>',
        labels={'Contagem': 'Número de Casos', 'evolucaoCaso': 'Evolução do Caso'},
        color='evolucaoCaso',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    
    fig_evolucao.update_layout(
        template='plotly_white',
        title=dict(y=0.95, x=0.5, xanchor='center', yanchor='top', font=dict(size=20, family='Poppins, sans-serif', color="black", weight='bold')),
        xaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black'), tickangle=-45),
        yaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black')),
        legend=dict(title='<b>Evolução:</b>', font=dict(size=14, family='Poppins, sans-serif', color='black'), bgcolor='rgba(240,240,240,0.8)', bordercolor='gray', borderwidth=1),
        margin=dict(l=50, r=50, t=80, b=50),
        bargap=0.2,
        plot_bgcolor='rgba(240,240,240,0.5)',
        transition={'duration': 500, 'easing': 'cubic-in-out'}
    )

    
    fig_evolucao.update_traces(marker_line=dict(color='black', width=1))

    
    top_10_condicoes = df_filtrado['condicoes'].value_counts().reset_index(name='Contagem').nlargest(10, 'Contagem')
    top_10_condicoes.columns = ['Condicao', 'Contagem']  

    
    fig_condicoes = px.bar(
        top_10_condicoes, 
        x='Condicao', 
        y='Contagem', 
        title='<b>Top 10 Condições mais Frequentes</b>',
        labels={'Contagem': 'Número de Casos', 'Condicao': 'Condição'},
        color='Contagem',
        color_continuous_scale=px.colors.sequential.Viridis
    )

    
    fig_condicoes.update_layout(
        template='plotly_white',
        title=dict(y=0.95, x=0.5, xanchor='center', yanchor='top', font=dict(size=20, family='Poppins, sans-serif', weight='bold', color="black")),
        xaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black'), tickangle=-45),
        yaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black')),
        legend=dict(title='<b>Contagem</b>', font=dict(size=14, family='Poppins, sans-serif', color='black'), bgcolor='rgba(240,240,240,0.8)', bordercolor='gray', borderwidth=1),
        margin=dict(l=50, r=50, t=80, b=50),
        bargap=0.2,
        plot_bgcolor='rgba(240,240,240,0.5)',
        transition={'duration': 500, 'easing': 'cubic-in-out'}
    )

    
    fig_condicoes.update_traces(marker_line=dict(color='black', width=1))


    return fig_classificacao, fig_evolucao, fig_condicoes

if __name__ == '__main__':
    app.run_server(debug=True)
