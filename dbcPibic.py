import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
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
        children="Plataforma interativa para visualização dos dados das notificações de síndrome gripal do estado de Pernambuco."
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
            ])
        ]),
        dbc.Row(
            dbc.Col(dcc.Graph(id='grafico-classificacao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id='grafico-evolucao', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id='grafico-condicoes', className="dash-graph"), width=8, lg={"size": 8, "offset": 2})
        ),
    ], fluid=True)
])

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
