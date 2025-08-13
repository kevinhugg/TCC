import dash
from dash import html, dcc, Input, Output, callback
from collections import Counter
import plotly.express as px
import pandas as pd
import firebase_functions as fb

dash.register_page(__name__, path='/pageVehicles', name='Veículos')


def create_damage_graph():
    """
    Creates the damage graph by fetching data from Firebase.
    Handles cases where no data is available.
    """
    data_damVeh = fb.get_damages_dates()
    data_damVeh_filtered = [date for date in data_damVeh if date is not None]

    if not data_damVeh_filtered:
        fig = px.bar(title='Danos por Data')
        fig.update_layout(
            annotations=[dict(text="Nenhum dado de dano encontrado", xref="paper", yref="paper", showarrow=False,
                              font=dict(size=16))],
            xaxis_visible=False, yaxis_visible=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    count_data = Counter(data_damVeh_filtered)
    df = pd.DataFrame({'Data': list(count_data.keys()), 'Quantidade de Danos': list(count_data.values())})
    df = df.sort_values(by='Data', ascending=True)
    fig = px.bar(df, x='Quantidade de Danos', y='Data', orientation='h', title='Danos por Data',
                 text='Quantidade de Danos')
    fig.update_traces(
        textposition='outside', textfont=dict(color='black'),
        hovertemplate='<b>Data:</b> %{y}<br><b>Danos:</b> %{x}<extra></extra>'
    )
    fig.update_layout(
        height=600, title_font_size=26, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Segoe UI, Arial, sans-serif", size=14),
        xaxis=dict(title_text='Quantidade de Danos', tickfont=dict(size=12)),
        yaxis=dict(title_text='Data', tickfont=dict(size=12)),
        hoverlabel=dict(font_size=12)
    )
    return fig


def layout():
    viaturas = fb.get_all_vehicles()
    viaturas_sorted = sorted(viaturas, key=lambda x: not x.get('avariada', False))

    damVehicles = fb.get_all_damage_reports()

    fig = create_damage_graph()

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

    return html.Div([

        html.Link(rel='stylesheet', href='/static/css/styleVehicles.css'),

        html.Div([

            html.Div([
                dcc.Input(id='input-search', type='text', placeholder='Buscar por placa ou número...',
                          className='input-search'),
            ], className='searchbar'),

            html.Div([
                html.Div('Imagem', className='header-item'),
                html.Div('Placa', className='header-item'),
                html.Div('Número', className='header-item'),
                html.Div('Veículo', className='header-item'),
                html.Div('Situação', className='header-item'),
            ], className='list-header'),

            html.Div(id='list-vehicles', className='list-vehicles', children=[
                html.Div([
                    dcc.Link(
                        html.Img(src=v.get('imagem', '/static/assets/img/imageNot.png'), className='img-vehicle'),
                        href=f"/dashboard/veiculo/{v.get('numero', '').upper()}"
                    ),
                    html.P(f"{v.get('placa')}", className='infoVehicle'),
                    html.P(f"{v.get('numero')}", className='infoVehicle'),
                    html.P(f"{v.get('veiculo')}", className='infoVehicle'),
                    html.P(
                        f"{'Avariada' if v.get('avariada') else 'Operante'}",
                        className='situation-ava' if v.get('avariada') else 'situation-op'
                    ),
                ], className='card-vehicles')
                for v in viaturas_sorted
            ]),

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
                html.Thead([
                    html.Tr([
                        html.Th('N°'),
                        html.Th('Desc'),
                        html.Th('Status'),
                        html.Th('Data'),
                    ])
                ]),
                html.Tbody(id='table_dam_body', children=[
                    html.Tr([
                        html.Td(item.get('viatura')),
                        html.Td(item.get('descricao')),
                        html.Td(item.get('status')),
                        html.Td(item.get('data')),
                    ]) for item in damVehicles
                ])
            ], className='table_ocu'),
            html.Div([
                html.A(id='link-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')
            ], style={'margin': '1rem 10rem'})
        ], className="Ranking_Ocu card"),

        html.Div([
            html.H4('Danos por Data'),
            graph_bar_horizontal
        ], className='graph-line card'),

    ], className='page-content')


@callback(
    Output('list-vehicles', 'children'),
    Input('input-search', 'value')
)
def update_list(search_value):
    viaturas = fb.get_all_vehicles()
    viaturas_sorted = sorted(viaturas, key=lambda x: not x.get('avariada', False))

    if not search_value:
        filtered = viaturas_sorted
    else:
        search_value = search_value.lower()
        filtered = [
            v for v in viaturas_sorted if
            search_value in v.get('placa', '').lower() or
            search_value in v.get('numero', '').lower()
        ]

    return [
        html.Div([
            dcc.Link(
                html.Img(src=v.get('imagem', '/static/assets/img/imageNot.png'), className='img-vehicle'),
                href=f"/dashboard/veiculo/{v.get('numero')}"
            ),
            html.P(v.get('placa'), className='infoVehicle'),
            html.P(v.get('numero'), className='infoVehicle'),
            html.P(v.get('veiculo'), className='infoVehicle'),
            html.P(
                'Avariada' if v.get('avariada') else 'Operante',
                className='situation-ava' if v.get('avariada') else 'situation-op'
            )
        ], className='card-vehicles')
        for v in filtered
    ]


@callback(
    Output('table_dam_body', 'children'),
    Input('status-filter', 'value')
)
def filtrar_ocorrencias(status):
    damVehicles = fb.get_all_damage_reports()
    if status == 'all':
        filtradas = damVehicles
    else:
        filtradas = [o for o in damVehicles if o.get('status') == status]

    return [
        html.Tr([
            html.Td(item.get('viatura')),
            html.Td(item.get('descricao')),
            html.Td(item.get('status')),
            html.Td(item.get('data')),
        ]) for item in filtradas
    ]


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
    fig = create_damage_graph()

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

    if 'xaxis' in fig_copy['layout']:
        fig_copy['layout']['xaxis']['gridcolor'] = grid_color
        fig_copy['layout']['xaxis']['zerolinecolor'] = grid_color
        fig_copy['layout']['xaxis']['linecolor'] = grid_color
    if 'yaxis' in fig_copy['layout']:
        fig_copy['layout']['yaxis']['gridcolor'] = grid_color
        fig_copy['layout']['yaxis']['linecolor'] = grid_color

    fig_copy['layout']['hoverlabel']['bgcolor'] = hover_bg_color
    fig_copy['layout']['hoverlabel']['bordercolor'] = hover_border_color

    if fig_copy.get('data'):
        fig_copy['data'][0]['marker']['color'] = bar_color
        fig_copy['data'][0]['textfont']['color'] = text_color

    return fig_copy