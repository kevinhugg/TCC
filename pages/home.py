import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import random

from data.dados import Ocur_Neighborhoods, time_response, Most_common_Ocu

dash.register_page(__name__, path='/', name='Home')

#VEÍCULOS
vehiclesTot = 521
damagedVehic = 152
perfectVehic = vehiclesTot - damagedVehic

#SERVIÇOS
services = 20000
servDones = 15000

#agentes
Agents_loged = 2930
entered = 50
logouted = 30

graphPieServices = go.Figure(
    data=[
        go.Pie(
            labels = ['Realizados', 'Pendentes'],
            values = [servDones, services  - servDones],
            hole = 0.6,
            sort=False,
            marker=dict(colors=['#f5d100', '#d9d9d9'], line=dict(color='white', width=2)),
            textinfo='none',
            textfont=dict(size=14, family='Segoe UI', color='#333'),
            hoverinfo='label+percent+value',
            direction='clockwise',
            rotation=45,
            pull=[0.05, 0],
        )
    ],

layout=go.Layout(
        height=140,
        width=250,
        showlegend=False,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(size=12)
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=25, l=70, r=20),
        transition={'duration': 700, 'easing': 'cubic-in-out'},
    )
)

graphOcurrence = go.Figure(
    data=[go.Bar(x=['Jan', 'Fev', 'Mar', 'Abr', 'Mai'], y=[10, 20, 30, 15, 45], marker=dict(color='#f5d100'))],

    layout=go.Layout(
        height=350,
        width=430,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title={"text": "Índice de ocorrências", "x": 0.5, "xanchor": "center"},
        margin=dict(t=40, b=30, l=30, r=30)
    )
)

#Gerar Mapa
GraphMapOcurrence = px.scatter_mapbox(
    Ocur_Neighborhoods,
    lat=[b['latitude'] for b in Ocur_Neighborhoods],
    lon=[b['longitude'] for b in Ocur_Neighborhoods],
    size=[b['quantidade'] for b in Ocur_Neighborhoods],
    hover_name=[b['bairro'] for b in Ocur_Neighborhoods],
    zoom=12,
    color_discrete_sequence=['#f5d100']
)

GraphMapOcurrence.update_layout(
    mapbox_style="open-street-map",
    height=350,
    margin=dict(t=20, b=0, l=0, r=0)
)

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/home.css'),

    html.Div([

        html.Div([
            html.H4('Viaturas'),  # Título
            html.Div([
                html.Div([
                html.H5('Com avarias:'),
                html.P(damagedVehic, className='NumsVehicles'),
                    ], className='info-vehic'),
                html.Div([
                html.H5('Sem avarias:'),
                html.P(perfectVehic, className='NumsVehicles'),
                    ], className='info-vehic')
            ], className='category'),
        ], className="vehicles"),

        html.Div([
            html.H4('Agentes Logados'),
            html.Div([
                html.Div(id='value-agents', style={'color': '#fff', 'z-index': '1000'}),
                html.Div(id='flux'),
            ], className='agents-info'),
            dcc.Interval(id='interval', interval=3000, n_intervals=0)
        ], className="agents"),

        html.Div([
            html.H4('Serviços Feitos'),
            html.Div([
                dcc.Graph(
                    id='graph-pie',
                    figure=graphPieServices,
                    config={
                        'displayModeBar': False,
                    },
                ),
            ], className='category-graphs'),
           ], className="pizza"),

        html.Div([
            html.H4('Ocorrências no Mês'),
            html.Div([
            html.P('1950', className='NumOcuMonth'),
            ], className='category'),
            ], className="ocuMonthly"),

        html.Div([
            dcc.Graph(
                id='bar-chart',
                figure=graphOcurrence,
                config={
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                        'autoScale2d', 'resetScale2d',
                        'zoomIn', 'zoomOut'
                    ],
                    'displaylogo': False
                }
            )
        ], className="GraphIndOcu"),

        html.Div([
            dcc.Graph(
                id='Graph_Time_Line',
                config={
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                        'autoScale2d', 'resetScale2d',
                        'zoomIn', 'zoomOut'
                    ],
                    'displaylogo': False
                }
            ),

            dcc.Dropdown(
                id='dropdown-year',
                options=[{'label': ano, 'value': ano} for ano in time_response.keys()],
                value='2025',
                clearable=False,
                style={'width': '70px'}
            )
        ], className="GraphTimeRes"),

        html.Div([
            html.H4('Ocorrências Mais Comuns'),

            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Tipo de Ocorrência'),
                        html.Th('Quantidade')
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(item['tipo']),
                        html.Td(item['quantidade'])
                    ]) for item in Most_common_Ocu
                ])
            ], className='table_ocu')

        ], className="Ranking_Ocu"),

        html.Div([
            html.H4('Distrubuição Geográfica das Ocorrências'),

            html.Div([
                dcc.Graph(
                    figure=GraphMapOcurrence,
                    config={'displayModeBar': False},
                )
            ]),
        ], className='GraphMap'),

        html.Div([
            html.H4('Bairros com mais ocorrências'),
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Bairro'),
                        html.Th('Quantidade de Ocorrências')
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(bairro['bairro']),
                        html.Td(bairro['quantidade'])
                    ]) for bairro in Ocur_Neighborhoods
                ])
            ], className='table_neighborhoods'),
        ], className='NgbhInfos'),

    ], className='page-content'),  # AQUI precisa estar a grid
])

@callback(
    Output('Graph_Time_Line', 'figure'),
    Input('dropdown-year', 'value')
)

def att_graph(year_selected):
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    tempos = time_response[year_selected]

    fig = go.Figure(
        data=[go.Scatter(x=meses, y=tempos, mode='lines+markers', line=dict(color='#f5d100'))],
        layout=go.Layout(
            height=350,
            margin=dict(t=30, b=20, l=20, r=20),
            plot_bgcolor='white',
            paper_bgcolor='white',
            title={'text': f'Tempo Médio de Resposta em {year_selected}', 'x': 0.5, "xanchor": "center"},
            yaxis_title='Tempo (minutos)',
            xaxis_title='Mês'
        )
    )
    return fig

@callback(
    Output('value-agents', 'children'),
    Output('flux', 'children'),
    Input('interval', 'n_intervals')
)
def att_flux(n):
    global Agents_loged, entered, logouted

    entered = random.randint(10, 100)
    logouted = random.randint(10, 100)
    Agents_loged += (entered - logouted)

    if entered > logouted:
        icon_class = 'fas fa-arrow-up'
        cor = 'green'
        flux_text = f'{Agents_loged + entered}'
    else:
        icon_class = 'fas fa-arrow-down'
        cor = 'red'
        flux_text = f'{Agents_loged - logouted}'

    return (
        f'{Agents_loged}',
        html.Div([
            html.I(className=icon_class, style={'color': cor, 'transition': 'color 0.5s ease'}),
            html.Span(flux_text, style={'color': cor, 'transition': 'color 0.5s ease'})
        ])
    )