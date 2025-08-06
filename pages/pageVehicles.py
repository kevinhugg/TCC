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
    marker=dict(
        color='#f5d100',
        line=dict(color='black', width=2)
    )
)

fig.update_layout(
    height=600,
    plot_bgcolor='white',
    paper_bgcolor='white',
    xaxis=dict(
        gridcolor='#d7d7d7',
        zerolinecolor='black'
    ),
)

graph_bar_horizontal = dcc.Graph(
    figure=fig,
    config={
        'modeBarButtonsToRemove': [
            'zoom2d', 'pan2d', 'select2d', 'lasso2d',
            'autoScale2d', 'resetScale2d',
            'zoomIn', 'zoomOut'
        ],
        'displaylogo': False
    },
    style={'height': '600px'},
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
                        href=f"/dashboard/veiculo/{v['numero']}"
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