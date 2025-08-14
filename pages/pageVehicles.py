import dash
from dash import html, dcc, Input, Output, callback, State, ctx
from collections import Counter
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import firebase_functions as fb
from datetime import datetime

dash.register_page(__name__, path='/pageVehicles', name='Veículos')


def create_damage_graph():
    data_damVeh = fb.get_damages_dates()
    data_damVeh_filtered = [date for date in data_damVeh if date is not None]

    if not data_damVeh_filtered:
        fig = px.bar(title='Danos por Data')
        fig.update_layout(
            annotations=[dict(text="Nenhum dado de dano encontrado", xref="paper", yref="paper", showarrow=False, font=dict(size=16))],
            xaxis_visible=False, yaxis_visible=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in data_damVeh_filtered]
    count_data = Counter(date_objects)
    df = pd.DataFrame({'Data': list(count_data.keys()), 'Quantidade de Danos': list(count_data.values())})
    df = df.sort_values(by='Data', ascending=True)
    df['Data'] = df['Data'].dt.strftime("%d/%m/%Y")

    fig = px.bar(df, x='Quantidade de Danos', y='Data', orientation='h', title='Danos por Data', text='Quantidade de Danos')
    fig.update_traces(textposition='outside', textfont=dict(color='black'), hovertemplate='<b>Data:</b> %{y}<br><b>Danos:</b> %{x}<extra></extra>')
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
    damVehicles = fb.get_all_damage_reports()

    damage_counts = {}
    for damage in damVehicles:
        num_viatura = damage.get('viatura')
        if num_viatura:
            damage_counts[num_viatura] = damage_counts.get(num_viatura, 0) + 1
    for v in viaturas:
        v['damage_count'] = damage_counts.get(v.get('numero'), 0)
    viaturas_sorted = sorted(viaturas, key=lambda x: x.get('damage_count', 0), reverse=True)

    fig = create_damage_graph()
    graph_bar_horizontal = dcc.Graph(id='damage-graph', figure=fig, config={'displayModeBar': True, 'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d'], 'displaylogo': False}, style={'height': '600px', 'width': '100%'}, className='bar-damVeh')

    all_parts = sorted(list(set(d['parte'] for d in damVehicles if d.get('parte'))))
    damage_part_options = [{'label': 'Partes', 'value': 'all'}] + [{'label': part.capitalize(), 'value': part} for part in all_parts]

    add_vehicle_modal = html.Div(
        id='modal-add-vehicle',
        className='modal',
        style={'display': 'none'},
        children=[
            html.Div(
                className='modal-content',
                children=[
                    html.Div(
                        className='modal-header',
                        children=[
                            html.H5('Adicionar Novo Veículo', className='modal-title'),
                            html.Button('×', id='cancel-add-vehicle-x', className='modal-close-button')
                        ]
                    ),
                    html.Div(
                        className='modal-body',
                        children=[
                            html.Div(className='form-group', children=[
                                html.Label("Placa:"),
                                dcc.Input(id='add-vehicle-placa', placeholder="ABC-1234", className='modal-input'),
                            ]),
                            html.Div(className='form-group', children=[
                                html.Label("Número:"),
                                dcc.Input(id='add-vehicle-numero', placeholder="Número de identificação", className='modal-input'),
                            ]),
                            html.Div(className='form-group', children=[
                                html.Label("Tipo de Veículo:"),
                                dcc.Input(id='add-vehicle-tipo', placeholder="Ex: Carro, Moto", className='modal-input'),
                            ]),
                            html.Div(id='upload-error-message', style={'color': 'red'}),
                            html.Div(className='form-group', children=[
                                html.Label("Imagem da Viatura:"),
                                dcc.Upload(
                                    id='upload-vehicle-image',
                                    children=html.Div([
                                        'Arraste e solte ou ',
                                        html.A('Selecione uma imagem')
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'margin': '10px 0'
                                    },
                                    accept='image/*'
                                ),
                            ]),
                        ]
                    ),
                    html.Div(
                        className='modal-footer',
                        children=[
                            html.Button("Cancelar", id="cancel-add-vehicle", className='modal-button cancel'),
                            html.Button("Salvar", id="submit-add-vehicle", className='modal-button submit'),
                        ]
                    )
                ]
            )
        ]
    )

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleVehicles.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Location(id='url-vehicles', refresh=True),
        add_vehicle_modal,
        html.Div(
            id='modal-delete-all-vehicles',
            className='modal',
            style={'display': 'none'},
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.Div(className='modal-header', children=[
                            html.H5('Confirmar Exclusão Total', className='modal-title'),
                            html.Button('×', id='cancel-delete-all-vehicles-x', className='modal-close-button')
                        ]),
                        html.Div(className='modal-body', children=[
                            html.P("Você tem certeza que quer remover TODAS as viaturas? Esta ação não pode ser desfeita.")
                        ]),
                        html.Div(className='modal-footer', children=[
                            html.Button('Cancelar', id='cancel-delete-all-vehicles', className='modal-button cancel'),
                            html.Button('Confirmar', id='confirm-delete-all-vehicles', className='modal-button submit')
                        ])
                    ]
                )
            ]
        ),
        html.Div([
            html.Div([
                dcc.Input(id='input-search', type='text', placeholder='Buscar por placa ou número...', className='input-search'),
            ], className='searchbar'),
            html.Div([
                html.Div('Imagem', className='header-item'),
                html.Div('Placa', className='header-item'),
                html.Div('Número', className='header-item'),
                html.Div('Veículo', className='header-item'),
                html.Div('Avarias', className='header-item'),
            ], className='list-header'),
            html.Div(id='list-vehicles', className='list-vehicles', children=[
                html.Div([
                    dcc.Link(html.Img(src=v.get('imagem', '/static/assets/img/imageNot.png'), className='img-vehicle'), href=f"/dashboard/veiculo/{v.get('numero', '').upper()}"),
                    html.P(f"{v.get('placa')}", className='infoVehicle'),
                    html.P(f"{v.get('numero')}", className='infoVehicle'),
                    html.P(f"{v.get('veiculo')}", className='infoVehicle'),
                    html.P(f"{v.get('damage_count', 0)}", className='situation-ava' if v.get('damage_count', 0) > 0 else 'situation-op'),
                ], className='card-vehicles')
                for v in viaturas_sorted
            ]),
            html.Div([
                html.Div([html.A(id='rem_all_vehicles', children='Remover Veículos', className='btn rem_vehicle')], className='btn_rem'),
                html.Div([html.A(id='add_vehicle', children='Adicionar Veículo', className='btn add_vehicle')], className='btn_add'),
            ], className='btn_rem_add'),
        ], className='vehicles card'),

        html.Div([
            html.H4('Viaturas danificadas'),
            html.Div([
                dcc.Dropdown(id='status-filter', options=[{'label': 'Todas', 'value': 'all'}, {'label': 'Aberta', 'value': 'Aberta'}, {'label': 'Fechada', 'value': 'Fechada'}], value='all', style={'width': '200px'}),
                dcc.Dropdown(id='damage-part-filter', options=damage_part_options, value='all', clearable=False, style={'width': '200px'}),
            ], className='drop-date'),
            html.Table([
                html.Thead(html.Tr([html.Th('N°'), html.Th('Área Avariada'), html.Th('Desc'), html.Th('Status'), html.Th('Data')])),
                html.Tbody(id='table_dam_body', children=[
                    html.Tr([html.Td(item.get('viatura')), html.Td(item.get('parte')), html.Td(item.get('descricao')), html.Td(item.get('status')), html.Td(item.get('data'))]) for item in damVehicles
                ])
            ], className='table_ocu'),
            html.Div([html.A(id='link-pdf', children='Gerar PDF', target="_blank", className='btn-pdf')], style={'margin': '1rem 10rem'})
        ], className="Ranking_Ocu card"),

        html.Div([html.H4('Danos por Data'), graph_bar_horizontal], className='graph-line card'),
    ], className='page-content')


@callback(
    Output('list-vehicles', 'children'),
    [Input('input-search', 'value'), Input('damage-part-filter', 'value'), Input('url-vehicles', 'pathname')]
)
def update_list(search_value, selected_part, pathname):
    viaturas = fb.get_all_vehicles()
    damVehicles = fb.get_all_damage_reports()

    if selected_part != 'all':
        vehicles_with_part = {d['viatura'] for d in damVehicles if d.get('parte') == selected_part}
        viaturas = [v for v in viaturas if v.get('numero') in vehicles_with_part]

    damage_counts = {}
    for damage in damVehicles:
        num_viatura = damage.get('viatura')
        if num_viatura:
            damage_counts[num_viatura] = damage_counts.get(num_viatura, 0) + 1
    for v in viaturas:
        v['damage_count'] = damage_counts.get(v.get('numero'), 0)
    viaturas_sorted = sorted(viaturas, key=lambda x: x.get('damage_count', 0), reverse=True)

    if search_value:
        search_value = search_value.lower()
        filtered_vehicles = [v for v in viaturas_sorted if search_value in v.get('placa', '').lower() or search_value in v.get('numero', '').lower()]
    else:
        filtered_vehicles = viaturas_sorted

    if not filtered_vehicles:
        return html.P("Nenhum veículo encontrado.", style={'text-align': 'center', 'padding': '20px'})

    return [
        html.Div([
            dcc.Link(html.Img(src=v.get('imagem', '/static/assets/img/imageNot.png'), className='img-vehicle'), href=f"/dashboard/veiculo/{v.get('numero')}"),
            html.P(v.get('placa'), className='infoVehicle'),
            html.P(v.get('numero'), className='infoVehicle'),
            html.P(v.get('veiculo'), className='infoVehicle'),
            html.P(f"{v.get('damage_count', 0)}", className='situation-ava' if v.get('damage_count', 0) > 0 else 'situation-op')
        ], className='card-vehicles')
        for v in filtered_vehicles
    ]


@callback(
    Output('table_dam_body', 'children'),
    [Input('status-filter', 'value'), Input('damage-part-filter', 'value')]
)
def filter_damage_reports(status, selected_part):
    damVehicles = fb.get_all_damage_reports()
    if status != 'all':
        damVehicles = [o for o in damVehicles if o.get('status') == status]
    if selected_part != 'all':
        damVehicles = [o for o in damVehicles if o.get('parte') == selected_part]
    return [html.Tr([html.Td(item.get('viatura')), html.Td(item.get('parte')), html.Td(item.get('descricao')), html.Td(item.get('status')), html.Td(item.get('data'))]) for item in damVehicles]


@callback(Output('link-pdf', 'href'), Input('status-filter', 'value'))
def atualizar_link_pdf(filtro_status):
    return f"/pdf_viaturas_Danificadas?status={filtro_status}"


@callback(Output('damage-graph', 'figure'), Input('theme-store', 'data'))
def update_graph_theme(theme):
    fig = create_damage_graph()
    fig_copy = fig.to_dict()
    # ... (theme update logic remains the same)
    return fig_copy


@callback(
    Output('modal-add-vehicle', 'style'),
    Input('add_vehicle', 'n_clicks'),
    Input('cancel-add-vehicle', 'n_clicks'),
    Input('cancel-add-vehicle-x', 'n_clicks'),
    State('modal-add-vehicle', 'style'),
    prevent_initial_call=True
)
def toggle_vehicle_modal(add_clicks, cancel_clicks, cancel_x_clicks, style):
    if ctx.triggered_id in ['add_vehicle', 'cancel-add-vehicle', 'cancel-add-vehicle-x']:
        if style and style.get('display') == 'flex':
            return {'display': 'none'}
        else:
            return {'display': 'flex'}
    return style


@callback(
    Output('url-vehicles', 'pathname'),
    Output('modal-add-vehicle', 'style', allow_duplicate=True),
    Output('upload-error-message', 'children'),
    Input('submit-add-vehicle', 'n_clicks'),
    State('add-vehicle-placa', 'value'),
    State('add-vehicle-numero', 'value'),
    State('add-vehicle-tipo', 'value'),
    State('upload-vehicle-image', 'contents'),
    State('upload-vehicle-image', 'filename'),
    prevent_initial_call=True
)
def handle_add_vehicle(n_clicks, placa, numero, tipo, contents, filename):
    if n_clicks:
        if not all([placa, numero, tipo]):
            return dash.no_update, {'display': 'flex'}, "Por favor, preencha todos os campos."

        image_url = '/static/assets/img/viatura1.png'  # Default image
        if contents:
            uploaded_url = fb.upload_image_to_storage(contents, filename)
            if uploaded_url:
                image_url = uploaded_url
            # If upload fails, silently use the default image_url

        vehicle_data = {
            'placa': placa,
            'numero': numero,
            'veiculo': tipo,
            'imagem': image_url
        }
        fb.add_vehicle(vehicle_data)
        return '/pageVehicles', {'display': 'none'}, ""
    return dash.no_update, dash.no_update, ""


@callback(
    Output("modal-delete-all-vehicles", "style"),
    [Input("rem_all_vehicles", "n_clicks"),
     Input("cancel-delete-all-vehicles", "n_clicks"),
     Input("cancel-delete-all-vehicles-x", "n_clicks")],
    [State("modal-delete-all-vehicles", "style")],
    prevent_initial_call=True,
)
def toggle_delete_all_modal(n_open, n_cancel, n_cancel_x, style):
    if n_open or n_cancel or n_cancel_x:
        if style and style.get('display') == 'flex':
            return {'display': 'none'}
        else:
            return {'display': 'flex'}
    return style


@callback(
    Output('url-vehicles', 'pathname', allow_duplicate=True),
    Input('confirm-delete-all-vehicles', 'n_clicks'),
    prevent_initial_call=True
)
def delete_all_vehicles(n_clicks):
    if n_clicks:
        if fb.delete_all_vehicles():
            return '/dashboard/pageVehicles'
    return dash.no_update