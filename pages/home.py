import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.graph_objects as go
import plotly.express as px
import random

from data.dados import Ocur_Neighborhoods, time_response, Most_common_Ocu

dash.register_page(__name__, path='/', name='Home')

# VEÍCULOS
vehiclesTot = 521
damagedVehic = 152
perfectVehic = vehiclesTot - damagedVehic

# SERVIÇOS
services = 20000
servDones = 15000

# agentes
Agents_loged = 2930

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/home.css'),
    html.Link(rel='stylesheet', href='/static/css/.css'),

    html.Div([

        html.Div([
            html.H4('Viaturas'),
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
        ], className="vehicles card"),

        html.Div([
            html.H4('Agentes Logados'),
            html.Div([
                html.Div(id='value-agents'),
                html.Div(id='flux'),
            ], className='agents-info'),
            dcc.Interval(id='interval', interval=3000, n_intervals=0)
        ], className="agents card"),

        html.Div([
            html.H4('Serviços Feitos'),
            html.Div([
                dcc.Graph(
                    id='graph-pie',
                    config={'displayModeBar': False},
                ),
            ], className='category-graphs'),
        ], className="pizza card"),

        html.Div([
            html.H4('Ocorrências no Mês'),
            html.Div([
                html.P('1950', className='NumOcuMonth'),
            ], className='category'),
        ], className="ocuMonthly card"),

        html.Div([
            dcc.Graph(
                id='bar-chart',
                config={
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                        'autoScale2d', 'resetScale2d',
                        'zoomIn', 'zoomOut'
                    ],
                    'displaylogo': False
                }
            )
        ], className="GraphIndOcu card"),

        html.Div([
            dcc.Dropdown(
                id='dropdown-year',
                options=[{'label': ano, 'value': ano} for ano in time_response.keys()],
                value='2025',
                clearable=False,
                style={'width': '70px'}
            ),
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
        ], className="GraphTimeRes card"),

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

        ], className="Ranking_Ocu card"),

        html.Div([
            html.H4('Distrubuição Geográfica das Ocorrências'),

            html.Div([
                dcc.Graph(
                    id='map-chart',
                    config={'displayModeBar': False},
                )
            ]),
        ], className='GraphMap card'),

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
        ], className='NgbhInfos card'),

    ], className='page-content home-grid'),
])


@callback(
    Output('graph-pie', 'figure'),
    Output('bar-chart', 'figure'),
    Output('map-chart', 'figure'),
    Input('theme-mode', 'data')
)
def update_static_graphs(theme):
    is_dark = theme == 'dark'

    # Theme colors corresponding to the new CSS variables
    if is_dark:
        plot_bg_color = '#1f293b'
        paper_bg_color = '#1f293b'
        font_color = '#f9fafb'
        marker_color = '#60a5fa'
        pie_marker_colors = ['#60a5fa', '#374151']
    else:
        plot_bg_color = '#ffffff'
        paper_bg_color = '#ffffff'
        font_color = '#1f2937'
        marker_color = '#3b82f6'
        pie_marker_colors = ['#3b82f6', '#e5e7eb']

    map_style = 'carto-darkmatter' if is_dark else 'open-street-map'

    # Gráfico de Pizza
    graphPieServices = go.Figure(
        data=[
            go.Pie(
                labels=['Realizados', 'Pendentes'],
                values=[servDones, services - servDones],
                hole=0.6,
                sort=False,
                marker=dict(colors=pie_marker_colors, line=dict(color='white', width=2)),
                textinfo='none',
                textfont=dict(size=14, family='Segoe UI', color=font_color),
                hoverinfo='label+percent+value',
                direction='clockwise',
                rotation=45,
                pull=[0.05, 0],
            )
        ],
        layout=go.Layout(
            height=120,
            width=300,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=20, l=0, r=0),
            transition={'duration': 700, 'easing': 'cubic-in-out'},
            font_color=font_color
        )
    )

    # Gráfico de Barras
    graphOcurrence = go.Figure(
        data=[go.Bar(x=['Jan', 'Fev', 'Mar', 'Abr', 'Mai'], y=[10, 20, 30, 15, 45], marker=dict(color=marker_color))],
        layout=go.Layout(
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={"text": "Índice de ocorrências", "x": 0.5, "xanchor": "center", "font": {"color": font_color}},
            margin=dict(t=40, b=30, l=30, r=30),
            font_color=font_color
        )
    )

    GraphMapOcurrence = px.scatter_mapbox(
        Ocur_Neighborhoods,
        lat=[b['latitude'] for b in Ocur_Neighborhoods],
        lon=[b['longitude'] for b in Ocur_Neighborhoods],
        size=[b['quantidade'] for b in Ocur_Neighborhoods],
        hover_name=[b['bairro'] for b in Ocur_Neighborhoods],
        zoom=12,
        color_discrete_sequence=[marker_color]
    )
    GraphMapOcurrence.update_layout(
        mapbox_style=map_style,
        margin=dict(t=0, b=0, l=0, r=0)
    )

    return graphPieServices, graphOcurrence, GraphMapOcurrence


@callback(
    Output('Graph_Time_Line', 'figure'),
    Input('dropdown-year', 'value'),
    Input('theme-mode', 'data')
)
def att_graph(year_selected, theme):
    is_dark = theme == 'dark'

    if is_dark:
        plot_bg_color = '#1f293b'
        paper_bg_color = '#1f293b'
        font_color = '#f9fafb'
        marker_color = '#60a5fa'
    else:
        plot_bg_color = '#ffffff'
        paper_bg_color = '#ffffff'
        font_color = '#1f2937'
        marker_color = '#3b82f6'

    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    tempos = time_response[year_selected]

    fig = go.Figure(
        data=[go.Scatter(x=meses, y=tempos, mode='lines+markers', line=dict(color=marker_color))],
        layout=go.Layout(
            margin=dict(t=30, b=20, l=20, r=20),
            plot_bgcolor=plot_bg_color,
            paper_bgcolor=paper_bg_color,
            title={'text': f'Tempo Médio de Resposta em {year_selected}', 'x': 0.5, "xanchor": "center",
                   "font": {"color": font_color}},
            yaxis_title='Tempo (minutos)',
            xaxis_title='Mês',
            font_color=font_color
        )
    )
    return fig


@callback(
    Output('value-agents', 'children'),
    Output('flux', 'children'),
    Input('interval', 'n_intervals'),
    State('theme-mode', 'data')
)
def att_flux(n, theme):
    # Simulate agent flux without using global variables for incrementing
    entered = random.randint(10, 50)
    logouted = random.randint(10, 50)

    current_agents = Agents_loged + (entered - logouted)

    is_dark = theme == 'dark'

    if entered > logouted:
        icon_class = 'fas fa-arrow-up'
        cor = '#10B981'  # Green for increase
    else:
        icon_class = 'fas fa-arrow-down'
        cor = '#ef4444'  # Red for decrease

    flux_text = f'{entered - logouted:+}'

    return (
        html.Span(f'{current_agents}', style={'color': 'var(--primary-text-color)'}),
        html.Div([
            html.I(className=icon_class, style={'color': cor, 'margin-right': '8px'}),
            html.Span(flux_text, style={'color': cor})
        ])
    )
