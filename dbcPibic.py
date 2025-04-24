import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State
import random
import geopandas as gpd
import unicodedata
from shapely.geometry import Point, Polygon


app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ], 
    suppress_callback_exceptions=True
)

app.title = "Dashboard de Análise"


df = pd.read_csv('df/dataset_IC_certoV2.csv', sep=';')
df_piramide = pd.read_csv('df/dataset_IC_certoV2.csv', sep=';', usecols=['racaCor', 'sexo', 'faixa_etaria'])


def normalizar_nome(nome):
   
        if isinstance(nome, str):
            return ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')
        else:
            
            return nome


df['municipio'] = df['municipio'].apply(normalizar_nome)

df['municipioIBGE'] = df['municipioIBGE'].astype(str).str.zfill(7).fillna('Desconhecido')

df['dataNotificacao'] = pd.to_datetime(df['dataNotificacao'], errors='coerce')
df['ano'] = df['dataNotificacao'].dt.year.astype('Int64')

valid_years = [2020, 2021, 2022, 2023, 2024]
df = df[df['ano'].isin(valid_years) | df['ano'].isna()]

anos_disponiveis = sorted(df['ano'].dropna().unique())

def preprocessar_dados():
    df_piramide = df[['racaCor', 'sexo', 'faixa_etaria', 'ano']].copy()
    df_piramide['faixa_etaria'] = df_piramide['faixa_etaria'].astype(str).fillna('Desconhecido')
    df_piramide = df_piramide[df_piramide['faixa_etaria'] != 'nan']

   
    def agrupar_idades(faixa):
        if ' a ' in faixa:
            inicio_faixa = int(faixa.split(' a ')[0])
        elif '+' in faixa:
            inicio_faixa = int(faixa.split('+')[0])
        else:
            return faixa
        return '55+' if inicio_faixa >= 55 else faixa

    df_piramide['faixa_etaria'] = df_piramide['faixa_etaria'].apply(agrupar_idades)
    categorias_ordenadas = sorted(
        df_piramide['faixa_etaria'].unique(),
        key=lambda x: int(x.split(' a ')[0]) if ' a ' in x and x != '55+' else (float('inf') if x == '55+' else int(x.split('+')[0]))
    )
    df_piramide['faixa_etaria'] = pd.Categorical(df_piramide['faixa_etaria'], categories=categorias_ordenadas, ordered=True)

    
    df_sankey = df[['sintomas', 'classificacaoFinal', 'evolucaoCaso', 'racaCor', 'sexo', 'ano']].copy()
    df_sankey.fillna({
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
    df_sankey['classificacaoFinal'] = (
        df_sankey['classificacaoFinal'].str.strip().str.lower()
        .replace(mapeamento_classificacao)
        .str.capitalize()
    )

    
    df_mapa = df[['municipioNotificacao', 'racaCor', 'sexo', 'ano']].copy()
    df_mapa['municipioNotificacao'] = df_mapa['municipioNotificacao'].apply(normalizar_nome)

    df_classificacao = df[['sintomas', 'classificacaoFinal', 'racaCor', 'sexo', 'ano']].copy()
    df_evolucao = df[['evolucaoCaso', 'racaCor', 'sexo', 'ano']].copy()
    df_condicoes = df[['condicoes', 'racaCor', 'sexo', 'ano']].copy()

    return {
        'df_piramide': df_piramide,
        'df_sankey': df_sankey,
        'df_mapa': df_mapa,  
        'df_classificacao': df_classificacao,
        'df_evolucao': df_evolucao,
        'df_condicoes': df_condicoes
    }


dados_preprocessados = preprocessar_dados()

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

    
    html.Div(
        html.Button(
            html.I(className="fas fa-sliders-h"), 
            id="sidebar-toggle",
            className="sidebar-toggle-btn"
        ),
        className="sidebar-toggle-container"
    ),

    
    html.Div([
        html.Div([
            html.H4("Filtros", className="sidebar-title"),
            html.Hr(),
            
            html.Div([
                html.Label("Ano:", className="filter-label"),
                dcc.Dropdown(
                    id='filtro-ano',
                    options=[{'label': str(int(ano)), 'value': ano} for ano in anos_disponiveis if not pd.isna(ano)],
                    placeholder="Selecione o ano",
                    className="filter-dropdown"
                )
            ], className="filter-group"),
            
            html.Div([
                html.Label("Raça:", className="filter-label"),
                dcc.Dropdown(
                    id='filtro-raca',
                    options=[{'label': raca, 'value': raca} for raca in df['racaCor'].dropna().unique()],
                    placeholder="Selecione a raça",
                    className="filter-dropdown"
                )
            ], className="filter-group"),
            
            html.Div([
                html.Label("Sexo:", className="filter-label"),
                dcc.Dropdown(
                    id='filtro-sexo',
                    options=[{'label': sexo, 'value': sexo} for sexo in df['sexo'].dropna().unique()],
                    placeholder="Selecione o sexo",
                    className="filter-dropdown"
                )
            ], className="filter-group"),
            
            html.Hr(),
            
            html.H4("Páginas", className="sidebar-title"),
            html.Div([
                dbc.Button(
                    [html.I(className="fas fa-chart-pie mr-2"), " Classificação e Evolução"],
                    id="botao-pagina-1", 
                    color="primary", 
                    className="navigation-button",
                    outline=False,
                    
                ),
                dbc.Button(
                    [html.I(className="fas fa-chart-bar mr-2"), " Demografia e Geolocalização"],
                    id="botao-pagina-2", 
                    color="secondary", 
                    className="navigation-button",
                    outline=True,
                    
                ),
            ], className="navigation-buttons-container"),
            
            html.Hr(),
            
            html.Div([
                dbc.Button(
                    [html.I(className="fas fa-undo mr-2"), " Resetar Filtros"],
                    id="reset-filters",
                    color="warning",
                    className="reset-button",
                    
                )
            ], className="sidebar-footer")
        ], className="sidebar-content")
    ], className="sidebar", id="sidebar"),

    html.Div([
        dbc.Container([
            html.Div(id='conteudo-pagina', children=[
                dcc.Loading(
                    id="loading-pagina",
                    type="circle",
                    children=html.Div(id="pagina-conteudo")
                )
            ])
        ], style={'fontFamily': 'Poppins, sans-serif'}, fluid=True)
    ], className="main-content"),

    
    html.Div(
        className="footer",
        children=[
            html.Div(
                className="footer-content",
                children=[
                    html.Img(src='/assets/unifavipLogo.png', className="footer-logo"),
                    html.P(
                        """Os dados de Síndrome Gripal mostrados neste painel estão completos para o períod͏o de 2020 a 2023. Mas, os ͏dados acerca de 2024 ainda estão incompletos acerca da constante atualização pelo MS.
                            Portanto, aconselhamos qu͏e vejam com atençã͏o o ano de 2024, es͏pecialm͏ente quando com͏p͏ararem ͏c͏om ͏os ano͏s͏ anteriores.""",
                        className="footer-text"
                    ),
                    html.Div(className="footer-divider"),
                    html.P(
                        "Projeto desenvolvido em parceria com o grupo de pesquisa DotLab e Unifavip WYDEN.",
                        className="footer-text"
                    ),
                    html.Div(
                        className="footer-links",
                        children=[
                            html.A("Contato", href="#"),
                        ]
                    ),  
                    html.P(
                        "© 2023 DotLab - Todos os direitos reservados",
                        className="footer-copyright"
                    )
                ]
            )
        ]
    )
])



@app.callback(
    Output("sidebar", "className"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")]
)
def toggle_sidebar(n_clicks, current_class):
    if n_clicks:
        if current_class == "sidebar":
            return "sidebar active"
        return "sidebar"
    return "sidebar"

@app.callback(
    [Output('filtro-ano', 'value'),
     Output('filtro-raca', 'value'),
     Output('filtro-sexo', 'value')],
    [Input('reset-filters', 'n_clicks')]
)
def reset_filters(n_clicks):
    if n_clicks:
        return None, None, None
   
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output('pagina-conteudo', 'children'),
     Output('botao-pagina-1', 'outline'),
     Output('botao-pagina-2', 'outline')],
    [Input('botao-pagina-1', 'n_clicks'),
     Input('botao-pagina-2', 'n_clicks')]
)
def navegar_paginas(botao1, botao2):
    ctx = dash.callback_context
    pagina = 'pagina1'  
    outline_pagina1 = False  
    outline_pagina2 = True   

    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == "botao-pagina-2":
            pagina = 'pagina2'
            outline_pagina1 = True   
            outline_pagina2 = False  

    if pagina == 'pagina1':
        return [
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-classificacao'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-evolucao'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-condicoes'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ])
        ], outline_pagina1, outline_pagina2
    else:  # pagina2
        return [
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-piramide-etaria'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-sankey'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-mapa-calor'), width=12, lg={"size": 10, "offset": 1}, className="mb-4"),
            ])
        ], outline_pagina1, outline_pagina2    

@app.callback(
    [Output('grafico-piramide-etaria', 'figure'),
     Output('grafico-sankey', 'figure'),
     Output('grafico-mapa-calor', 'figure')],
    [Input('filtro-ano', 'value'),
     Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def criar_graficos(filtro_ano, filtro_raca, filtro_sexo):
    
    df_piramide = dados_preprocessados['df_piramide']
    df_sankey = dados_preprocessados['df_sankey']
    df_mapa = dados_preprocessados['df_mapa']

    if filtro_ano:
        df_piramide = df_piramide[df_piramide['ano'] == filtro_ano]
        df_sankey = df_sankey[df_sankey['ano'] == filtro_ano]
        df_mapa = df_mapa[df_mapa['ano'] == filtro_ano]
    if filtro_raca:
        df_piramide = df_piramide[df_piramide['racaCor'] == filtro_raca]
        df_sankey = df_sankey[df_sankey['racaCor'] == filtro_raca]
        df_mapa = df_mapa[df_mapa['racaCor'] == filtro_raca]
    if filtro_sexo:
        df_piramide = df_piramide[df_piramide['sexo'] == filtro_sexo]
        df_sankey = df_sankey[df_sankey['sexo'] == filtro_sexo]
        df_mapa = df_mapa[df_mapa['sexo'] == filtro_sexo]


    casos_por_municipio = df_mapa.groupby('municipioNotificacao', as_index=False).size()
    casos_por_municipio.columns = ['municipioNotificacao', 'casos']

    piramide_data = df_piramide.groupby(['faixa_etaria', 'sexo']).size().reset_index(name='contagem')
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


    colunas_sankey = ['sintomas', 'classificacaoFinal', 'evolucaoCaso']

    sankey_data = pd.concat([
        df_sankey.groupby([colunas_sankey[i], colunas_sankey[i + 1]])
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


    
    gdf_municipios = gpd.read_file('df/PE_Municipios_2023.shp')

    
    gdf_mapa = gdf_municipios.merge(casos_por_municipio, left_on='NM_MUN', right_on='municipioNotificacao', how='left')

    
    gdf_mapa['casos'] = gdf_mapa['casos'].fillna(0)

    
    fig_mapa_calor = go.Figure(go.Choroplethmapbox(
        geojson=gdf_mapa.__geo_interface__,  
        locations=gdf_mapa.index,  
        z=gdf_mapa['casos'],  
        colorscale='Viridis',  
        marker_opacity=0.8,
        marker_line_width=0.5,
        colorbar_title="Casos",
        hovertemplate=(
            "<b>Município:</b> %{customdata[0]}<br>"
            "<b>Casos:</b> %{z}<extra></extra>"
        ),
        customdata=gdf_mapa[['NM_MUN']].values  
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
    [Input('filtro-ano', 'value'),
     Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def atualizar_graficos(filtro_ano, filtro_raca, filtro_sexo):
    
    df_classificacao = dados_preprocessados['df_classificacao']
    df_evolucao = dados_preprocessados['df_evolucao']
    df_condicoes = dados_preprocessados['df_condicoes']

    if filtro_ano:
        df_classificacao = df_classificacao[df_classificacao['ano'] == filtro_ano]
        df_evolucao = df_evolucao[df_evolucao['ano'] == filtro_ano]
        df_condicoes = df_condicoes[df_condicoes['ano'] == filtro_ano]
    if filtro_raca:
        df_classificacao = df_classificacao[df_classificacao['racaCor'] == filtro_raca]
        df_evolucao = df_evolucao[df_evolucao['racaCor'] == filtro_raca]
        df_condicoes = df_condicoes[df_condicoes['racaCor'] == filtro_raca]
    if filtro_sexo:
        df_classificacao = df_classificacao[df_classificacao['sexo'] == filtro_sexo]
        df_evolucao = df_evolucao[df_evolucao['sexo'] == filtro_sexo]
        df_condicoes = df_condicoes[df_condicoes['sexo'] == filtro_sexo]
    
    df_classificacao_agg = df_classificacao.groupby(['sintomas', 'classificacaoFinal']).size().reset_index(name='count')
    df_evolucao_agg = df_evolucao.groupby('evolucaoCaso').size().reset_index(name='Contagem')
    df_condicoes_agg = df_condicoes.groupby('condicoes').size().reset_index(name='Contagem').nlargest(10, 'Contagem')

    
    
    fig_classificacao = px.bar(
        df_classificacao_agg, 
        y='sintomas',  
        x='count',     
        color='classificacaoFinal',
        title='Classificação Final X Sintomas',
        labels={'count': 'Número de Casos', 'sintomas': 'Sintomas'},
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Set2,
        orientation='h'  
    )
   
    fig_classificacao.update_layout(
        title={'text': '<b>Classificação Final por Sintomas</b>', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        yaxis=dict(categoryorder='total ascending', title_font=dict(size=16, family='Poppins, sans-serif', color='black')),  
        xaxis=dict(title_font=dict(size=16, family='Poppins, sa ns-serif', color='black')),  
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

    fig_evolucao = px.bar(
        df_evolucao_agg, 
        y='evolucaoCaso',  
        x='Contagem',      
        title='<b>Contagem de Evolução de Casos</b>',
        labels={'Contagem': 'Número de Casos', 'evolucaoCaso': 'Evolução do Caso'},
        color='evolucaoCaso',
        color_discrete_sequence=px.colors.qualitative.Pastel,
        orientation='h'  
    )

    fig_evolucao.update_layout(
        showlegend=False,
        template='plotly_white',
        title=dict(y=0.95, x=0.5, xanchor='center', yanchor='top', font=dict(size=20, family='Poppins, sans-serif', color="black", weight='bold')),
        yaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black')),  
        xaxis=dict(title_font=dict(size=16, family='Poppins, sans-serif', color='black'), tickfont=dict(size=12, family='Poppins, sans-serif', color='black')),  
        margin=dict(l=50, r=50, t=80, b=50),
        bargap=0.2,
        plot_bgcolor='rgba(240,240,240,0.5)',
        transition={'duration': 500, 'easing': 'cubic-in-out'}
    )

    fig_evolucao.update_traces(marker_line=dict(color='black', width=1))
    
    fig_condicoes = px.bar(
    df_condicoes_agg,
    y='condicoes',
    x='Contagem',
    title='Top 10 Condições mais Frequentes',
    labels={'Contagem': 'Número de Casos', 'condicoes': 'Condição'},
    color='Contagem',
    color_continuous_scale=px.colors.sequential.Viridis,
    orientation='h',
    text='Contagem'  
    )

    fig_condicoes.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        template='plotly_white',
        title=dict(
            y=0.95, 
            x=0.5, 
            xanchor='center', 
            yanchor='top', 
            font=dict(size=20, family='Poppins, sans-serif', weight='bold', color="black")
        ),
        yaxis=dict(
            title_font=dict(size=16, family='Poppins, sans-serif', color='black'), 
            tickfont=dict(size=12, family='Poppins, sans-serif', color='black'),
            automargin=True  
        ),
        xaxis=dict(
            title_font=dict(size=16, family='Poppins, sans-serif', color='black'), 
            tickfont=dict(size=12, family='Poppins, sans-serif', color='black')
        ),
        margin=dict(l=100, r=50, t=80, b=50),  
        bargap=0.2,
        plot_bgcolor='rgba(240,240,240,0.5)',
        transition={'duration': 500, 'easing': 'cubic-in-out'},
        uniformtext_minsize=10,  
        uniformtext_mode='hide'  
    )

    
    fig_condicoes.update_traces(
        marker_line=dict(color='black', width=1),
        texttemplate='%{x}',  
        textposition='outside',  
        textfont=dict(
            size=12,
            family='Poppins, sans-serif',
            color='black'
        ),
        cliponaxis=False  
    )

    
    fig_condicoes.update_xaxes(rangemode="tozero", autorange=True)

    return fig_classificacao, fig_evolucao, fig_condicoes

if __name__ == '__main__':
    app.run_server(debug=True)
