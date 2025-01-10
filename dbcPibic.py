import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output

# Inicializando o aplicativo
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    suppress_callback_exceptions=True
)

app.title = "Dashboard de Análise"

# Carregando o DataFrame
df = pd.read_csv('df/dataset_IC_certoV2.csv', sep=';')

# Layout do aplicativo
app.layout = html.Div([
    html.Div(
        className="header",
        children=[
            html.Img(src='/assets/DotLab.png', className="header-image"),  # Caminho da imagem
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
            # Página 1 (gráficos)
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-classificacao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-evolucao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-condicoes', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            )
        ])
    ], fluid=True)
])

# Callback para alternar entre páginas
@app.callback(
    Output('conteudo-pagina', 'children'),
    [Input('botao-pagina-1', 'n_clicks'),
     Input('botao-pagina-2', 'n_clicks')]
)
def navegar_paginas(botao1, botao2):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [
            # Página 1: Gráficos principais
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-classificacao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-evolucao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-condicoes', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            )
        ]

    if ctx.triggered[0]['prop_id'].startswith('botao-pagina-1'):
        return [
            # Página 1: Gráficos principais
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-classificacao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-evolucao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-condicoes', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
            )
        ]
    elif ctx.triggered[0]['prop_id'].startswith('botao-pagina-2'):
        return [
            # Página 2: Gráfico de pirâmide etária e Sankey
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-piramide-etaria', className="dash-graph"), width=12, lg={"size": 8, "offset": 2})
            ),
            dbc.Row(
                dbc.Col(dcc.Graph(id='grafico-sankey', className="dash-graph"), width=12, lg={"size": 8, "offset": 2})
            )
        ]

@app.callback(
    [Output('grafico-piramide-etaria', 'figure'),
     Output('grafico-sankey', 'figure')],
    [Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def criar_graficos(filtro_raca, filtro_sexo):
    # Filtragem do DataFrame
    df_filtrado = df.copy()
    if filtro_raca:
        df_filtrado = df_filtrado[df_filtrado['racaCor'] == filtro_raca]
    if filtro_sexo:
        df_filtrado = df_filtrado[df_filtrado['sexo'] == filtro_sexo]

    # Garantir que a coluna "faixa_etaria" seja string e lidar com valores ausentes
    df_filtrado['faixa_etaria'] = df_filtrado['faixa_etaria'].astype(str).fillna('Desconhecido')

    # Ordenar faixas etárias numericamente
    def extrair_inicio_faixa(faixa):
        try:
            return int(faixa.split(' a ')[0]) if ' a ' in faixa else float('inf')
        except ValueError:
            return float('inf')

    categorias_ordenadas = sorted(
        df_filtrado['faixa_etaria'].unique(),
        key=extrair_inicio_faixa
    )

    df_filtrado['faixa_etaria'] = pd.Categorical(
        df_filtrado['faixa_etaria'], 
        categories=categorias_ordenadas, 
        ordered=True
    )

    # Pirâmide Etária
    piramide_data = (
        df_filtrado.groupby(['faixa_etaria', 'sexo']).size().reset_index(name='contagem')
    )
    piramide_data['contagem_negativa'] = piramide_data.apply(
        lambda row: -row['contagem'] if row['sexo'] == 'Feminino' else row['contagem'],
        axis=1
    )

    fig_piramide = px.bar(
        piramide_data,
        x='contagem_negativa',
        y='faixa_etaria',
        color='sexo',
        orientation='h',
        title='Pirâmide Etária',
        labels={'faixa_etaria': 'Faixa Etária', 'contagem_negativa': 'Contagem', 'sexo': 'Sexo'},
        color_discrete_map={'Masculino': 'blue', 'Feminino': 'pink'}
    )

    fig_piramide.update_layout(
        template='plotly_white',
        height=700
    )

    # Gráfico Sankey
    # Exemplo de colunas para as categorias do Sankey
    # Certifique-se de substituir pelos dados reais
    df_filtrado['categoria_origem'] = df_filtrado['codigoResultadoTeste1']  # Exemplo: coluna de origem
    df_filtrado['categoria_destino'] = df_filtrado['codigoResultadoTeste4']  # Exemplo: coluna de destino

    sankey_data = (
        df_filtrado.groupby(['categoria_origem', 'categoria_destino']).size().reset_index(name='fluxo')
    )

    categorias_origem = sankey_data['categoria_origem'].unique().tolist()
    categorias_destino = sankey_data['categoria_destino'].unique().tolist()

    # Criar os índices para os nós
    todos_os_nos = categorias_origem + categorias_destino
    indices_nos = {nome: i for i, nome in enumerate(todos_os_nos)}

    # Dados do Sankey
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=todos_os_nos
        ),
        link=dict(
            source=sankey_data['categoria_origem'].map(indices_nos).tolist(),
            target=sankey_data['categoria_destino'].map(indices_nos).tolist(),
            value=sankey_data['fluxo'].tolist()
        )
    )])

    fig_sankey.update_layout(
        title_text="Fluxo de Resultados",
        font_size=12,
        height=700
    )

    return fig_piramide, fig_sankey



    
# Callbacks para atualizar os gráficos com base nos filtros
@app.callback(
    [Output('grafico-classificacao', 'figure'),
     Output('grafico-evolucao', 'figure'),
     Output('grafico-condicoes', 'figure')],
    [Input('filtro-raca', 'value'),
     Input('filtro-sexo', 'value')]
)
def atualizar_graficos(filtro_raca, filtro_sexo):
    # Filtrar o DataFrame com base nos filtros selecionados
    df_filtrado = df.copy()
    if filtro_raca:
        df_filtrado = df_filtrado[df_filtrado['racaCor'] == filtro_raca]
    if filtro_sexo:
        df_filtrado = df_filtrado[df_filtrado['sexo'] == filtro_sexo]

    # Atualizando os gráficos com o DataFrame filtrado
    grouped_df = df_filtrado.groupby(['sintomas', 'classificacaoFinal']).size().reset_index(name='count')
    # Criando o gráfico de barras para Classificação Final X Sintomas com melhorias visuais
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
    fig_classificacao.update_xaxes(
        categoryorder='total descending'
    )
    fig_classificacao.update_layout(
        template='plotly_white',
        title={
            'text': 'Classificação Final por Sintomas',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Sintomas',
        yaxis_title='Número de Casos',
       
    )

    evolucao_count = df_filtrado['evolucaoCaso'].value_counts().reset_index()
    evolucao_count.columns = ['Evolucao', 'Contagem']
    # Criando o gráfico de barras para Evolução de Casos
    fig_evolucao = px.bar(
        evolucao_count, 
        x='Evolucao', 
        y='Contagem', 
        title='Contagem de Evolução de Casos',
        labels={'Contagem': 'Número de Casos', 'Evolucao': 'Evolução do Caso'},
        color='Evolucao',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_evolucao.update_layout(
        template='plotly_white',
        title={
            'text': 'Contagem de Evolução de Casos',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    condicoes_count = df_filtrado['condicoes'].value_counts().reset_index()
    condicoes_count.columns = ['Condicao', 'Contagem']
    top_10_condicoes = condicoes_count.head(10)

    # Criando o gráfico de barras para as 10 maiores condições
    fig_condicoes = px.bar(
        top_10_condicoes, 
        x='Condicao', 
        y='Contagem', 
        title='Top 10 Condições mais Frequentes',
        labels={'Contagem': 'Número de Casos', 'Condicao': 'Condição'},
        color='Contagem',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_condicoes.update_layout(
        template='plotly_white',
        title={
            'text': 'Top 10 Condições mais Frequentes',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    return fig_classificacao, fig_evolucao, fig_condicoes

if __name__ == '__main__':
    app.run_server(debug=True)
