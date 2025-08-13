import dash
from dash import html, dcc, Input, Output, callback
from collections import Counter
import plotly.express as px

from data.dados import viaturas, damVehicles, data_damVeh

dash.register_page(__name__, path='/pageVehicles', name='Veículos')

viaturas_sorted = sorted(viaturas, key=lambda x: not x['avariada'])

count_data = Counter(data_damVeh)

fig = px.bar(
    x=list(count_data.values()),
    y=list(count_data.keys()),
    orientation='h',
    labels={'x': 'Quantidade de Danos', 'y': 'Data'},
    title='Danos por Data'
)


fig.update_traces(
    textposition='outside',
    textfont=dict(color='black'),
    hovertemplate=(
        '<b>Data:</b> %{y}<br>'
        '<b>Danos:</b> %{x}<extra></extra>'
    )
)

fig.update_layout(
    height=600,
    title_font_size=26,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(
        family="Segoe UI, Arial, sans-serif",
        size=14
    ),
    xaxis=dict(
        title_text='Quantidade de Danos',
        tickfont=dict(size=12)
    ),
    yaxis=dict(
        title_text='Data',
        tickfont=dict(size=12),
        autorange="reversed"
    ),
    hoverlabel=dict(
        font_size=12
    )
)

graph_bar_horizontal = dcc.Graph(
    id='damage-graph',
    figure=fig,
    config={
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d'],
        'displaylogo': False
    },
    style={'height': '600px', 'width': '100%'},
    className='bar-damVeh'
)

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/styleVehicles.css'),

    html.Div([

        html.Div([
            dcc.Input(id='input-search', type='text', placeholder='Buscar por placa ou número...', className='input-search'),
        ], className='searchbar'),

        html.Div([
            html.Div('Imagem', className='header-item'),
            html.Div('Placa', className='header-item'),
            html.Div('Número', className='header-item'),
            html.Div('Veículo', className='header-item'),
            html.Div('Situação', className='header-item'),
        ], className='list-header'),

        html.Div([
            *[
                html.Div([
                    dcc.Link(
                        html.Img(src=v['imagem'], className='img-vehicle'),
                        href=f"/dashboard/veiculo/{v['numero'].upper()}"
                    ),
                    html.P(f"{v['placa']}", className='infoVehicle'),
                    html.P(f"{v['numero']}", className='infoVehicle'),
                    html.P(f"{v['veiculo']}", className='infoVehicle'),
                    html.P(
                        f"{'Avariada' if v['avariada'] else 'Operante'}",
                        className='situation-ava' if v['avariada'] else 'situation-op'
                    ),
                ], className='card-vehicles')
                for v in viaturas_sorted
            ],
        ],id='list-vehicles', className='list-vehicles'),

        html.Div([
            html.Div([
                html.A(id='rem_vehicle', children='Remover Veículos', className='btn rem_vehicle')
            ], className='btn_rem'),

            html.Div([
                html.A(id='add_vehicle', children='Adicionar Veículo', className='btn add_vehicle')
            ], className='btn_add'),
        ], className='btn_rem_add'),

    ], className='vehicles card'),

    html.Div([
        html.H4('Viaturas danificadas'),

        html.Div([
            dcc.Dropdown(
                id='status-filter',
                options=[
                    {'label': 'Todas', 'value': 'all'},
                    {'label': 'Aberta', 'value': 'Aberta'},
                    {'label': 'Fechada', 'value': 'Fechada'},
                ],
                value='all',
                style={'width': '200px'}
            ),
        ], className='drop-date'),

            html.Table([
                html.Tbody([
                    html.Tr([
                        html.Td(item['viatura']),
                        html.Td(item['descricao']),
                        html.Td(item['status']),
                        html.Td(item['data']),
                    ]) for item in damVehicles
            ], id='table_dam', className='table_ocu'),
            ]),
            html.Div([
                html.A(id='link-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')
            ], style={'margin': '1rem 10rem'})
    ], className="Ranking_Ocu card"),

    html.Div([
        html.H4('Danos por Data'),
        graph_bar_horizontal
    ], className='graph-line card'),

], className='page-content'),

@callback(
    Output('list-vehicles', 'children'),
    Input('input-search', 'value')
)
def update_list(search_value):
    if not search_value:
        filtered = viaturas
    else:
        search_value = search_value.lower()
        filtered = [v for v in viaturas if search_value in v['placa'].lower() or search_value in v['numero'].lower()]

    return [
        html.Div([
            dcc.Link(
                html.Img(src=v['imagem'], className='img-vehicle'),
                href=f"/dashboard/veiculo/{v['numero']}"
            ),
            html.P(v['placa'], className='infoVehicle'),
            html.P(v['numero'], className='infoVehicle'),
            html.P(v['veiculo'], className='infoVehicle'),
            html.P(
                'Avariada' if v['avariada'] else 'Operante',
                className='situation-ava' if v['avariada'] else 'situation-op'
            )
        ], className='card-vehicles')
        for v in filtered
    ]

@callback(
    Output('table_dam', 'children'),
    Input('status-filter', 'value')
)
def filtrar_ocorrencias(status):
    if status == 'all':
        filtradas = damVehicles
    else:
        filtradas = [o for o in damVehicles if o['status'] == status]

    return html.Div([
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th('N°'),
                    html.Th('Desc'),
                    html.Th('Status'),
                    html.Th('Data'),
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(item['viatura']),
                    html.Td(item['descricao']),
                    html.Td(item['status']),
                    html.Td(item['data']),
                ]) for item in filtradas
            ])
        ], className='table_ocu'),
    ]),

#callback pdf
@callback(
    Output('link-pdf', 'href'),
    Input('status-filter', 'value')
)
def atualizar_link_pdf(filtro_status):
    return f"/pdf_viaturas_Danificadas?status={filtro_status}"


@callback(
    Output('damage-graph', 'figure'),
    Input('theme-store', 'data')
)
def update_graph_theme(theme):
    fig_copy = fig.to_dict()

    if theme == 'dark':
        title_color = '#ffffff'
        text_color = '#ffffff'
        grid_color = '#444444'
        bar_color = '#60a5fa'
        hover_bg_color = '#1f293b'
        hover_border_color = '#374151'
    else:
        title_color = '#295678'
        text_color = '#000000'
        grid_color = '#e5e7eb'
        bar_color = '#4682B4'
        hover_bg_color = 'white'
        hover_border_color = '#e5e7eb'

    fig_copy['layout']['title']['font']['color'] = title_color
    fig_copy['layout']['font']['color'] = text_color
    fig_copy['layout']['xaxis']['gridcolor'] = grid_color
    fig_copy['layout']['yaxis']['gridcolor'] = grid_color
    fig_copy['layout']['xaxis']['zerolinecolor'] = grid_color
    fig_copy['layout']['xaxis']['linecolor'] = grid_color
    fig_copy['layout']['yaxis']['linecolor'] = grid_color
    fig_copy['layout']['hoverlabel']['bgcolor'] = hover_bg_color
    fig_copy['layout']['hoverlabel']['bordercolor'] = hover_border_color

    fig_copy['data'][0]['marker']['color'] = bar_color
    fig_copy['data'][0]['textfont']['color'] = text_color

    return fig_copy