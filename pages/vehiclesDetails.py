import dash
from dash import html, dcc, Input, Output, callback, State
from datetime import datetime
import dash_bootstrap_components as dbc
import firebase_functions as fb

dash.register_page(__name__, path_template='/veiculo/<numero>', name=None)


def layout(numero=None):
    dados = fb.get_vehicle_by_number(numero)
    partes_avariadas = fb.get_damage_reports_by_vehicle(numero)

    if not (dados):
        return html.H3("Veículo não encontrado")

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/detailsVehicles.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Location(id='url-redirect', refresh=True),
        dcc.Store(id='vehicle-store', data=numero),
        dcc.Store(id='agent-assignment-trigger', data=0),

        html.Div([
            html.H3(f"Viatura - {dados['numero']}", className='tittle'),

            html.Div([
                html.Img(src=dados.get('imagem', '/static/assets/img/imageNot.png'), className='img'),
                html.Div([
                    html.P(f"Placa: {dados.get('placa', '---')}", className='det placa'),
                    html.P(f"Tipo: {dados.get('veiculo', '---')}", className='det tipo'),
                    html.P(
                        f"Situação: {'Avariada' if dados.get('avariada') else 'Operante'}",
                        className='det avariada' if dados.get('avariada') else 'det operante'
                    ),
                    html.P(f"Partes Avariadas: {', '.join(sorted(list(set(p['parte'] for p in partes_avariadas))))}" if partes_avariadas else "Partes Avariadas: Sem avarias",
                           className='det loc_av'),
                ], className='texts-det'),
            ], className='details-items'),

            html.Div([
                html.Div([
                    html.A(id='rem_vehicle_btn', children='Remover Veículo', className='btn rem_vehicle')
                ], className='btn_rem'),
            ], className='btn_rem_add'),

        ], className='details-container card'),

        html.Div(
            id='modal-delete-vehicle',
            className='modal',
            style={'display': 'none'},
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.Div(className='modal-header', children=[
                            html.H5('Confirmar Exclusão', className='modal-title'),
                            html.Button('×', id='cancel-delete-vehicle-x', className='modal-close-button')
                        ]),
                        html.Div(className='modal-body', children=[
                            html.P("Você tem certeza que quer remover esta viatura?")
                        ]),
                        html.Div(className='modal-footer', children=[
                            html.Button('Cancelar', id='cancel-delete-vehicle', className='modal-button cancel'),
                            html.Button('Confirmar', id='confirm-delete-vehicle', className='modal-button submit')
                        ])
                    ]
                )
            ]
        ),

        html.Div([
            html.H4("Histórico da Viatura"),
            dcc.RadioItems(
                id='history-filter',
                options=[
                    {'label': 'Todos', 'value': 'todos'},
                    {'label': 'Ocorrências', 'value': 'ocorrencia'},
                    {'label': 'Serviços', 'value': 'serviço'},
                    {'label': 'Danos', 'value': 'dano'},
                ],
                value='todos',
                labelStyle={'display': 'inline-block', 'margin-right': '20px'}
            ),
            html.Div(id='history-table-div'),
        ], className='ocurrences card'),

        html.Div([
            html.Div([
                html.H3(f"Responsáveis do Mês", className='tittle'),
                dcc.Dropdown(
                    id='dropdown-turnos',
                    options=[
                        {'label': 'Todos os Turnos', 'value': 'todos'},
                        {'label': 'Manhã', 'value': 'manha'},
                        {'label': 'Tarde', 'value': 'tarde'},
                        {'label': 'Noite', 'value': 'noite'},
                    ],
                    value='todos',
                    clearable=False,
                    className='dropdown-turnos',
                    style={'height': '40px', 'width': '200px'}
                ),
            ], className='dropdown-title'),

            html.Div(id='agents-grid', className='agents-grid'),

        ], className='agents-container card'),

        html.Div(
            id='agent-modal',
            className='modal',
            style={'display': 'none'},
            children=[
                html.Div(
                    className='modal-content',
                    children=[
                        html.Div(className='modal-header', children=[
                            html.H5('Adicionar Agente'),
                            html.Button('×', id='modal-close-button', className='modal-close-button'),
                        ]),
                        html.Div(className='modal-body', children=[
                            html.Div(className='form-group', children=[
                                html.Label('Filtar Agentes por:'),
                                dcc.Dropdown(
                                    id='agent-filter-dropdown',
                                    options=[
                                        {'label': 'Todos os Agentes', 'value': 'all'},
                                        {'label': 'Agentes Sem Função', 'value': 'unassigned'},
                                    ],
                                    value='all',
                                    clearable=False
                                ),
                            ]),
                            html.Div(className='form-group', children=[
                                html.Label('Agente:'),
                                dcc.Dropdown(id='agent-list', placeholder="Selecione um agente...", multi=False),
                            ]),
                            html.Hr(),
                            html.Div(className='form-group', children=[
                                html.Label('Turno:'),
                                dcc.Dropdown(
                                    id='assign-shift-dropdown',
                                    options=[
                                        {'label': 'Manhã', 'value': 'manha'},
                                        {'label': 'Tarde', 'value': 'tarde'},
                                        {'label': 'Noite', 'value': 'noite'},
                                    ],
                                    placeholder="Selecione um turno...",
                                ),
                            ]),
                            html.Div(className='form-group', children=[
                                html.Label('Função:'),
                                dcc.Dropdown(
                                    id='assign-role-dropdown',
                                    options=[
                                        {'label': 'Motorista', 'value': 'Motorista'},
                                        {'label': 'Encarregado', 'value': 'Encarregado'},
                                        {'label': 'Auxiliar', 'value': 'Auxiliar'},
                                    ],
                                    placeholder="Selecione uma função...",
                                ),
                            ]),
                        ]),
                        html.Div(className='modal-footer', children=[
                            html.Button('Atribuir Agente', id='assign-agent-button', className='btn btn-primary')
                        ]),
                    ]
                )
            ]
        ),

    ], className='page-content'),

@callback(
    Output('history-table-div', 'children'),
    [Input('history-filter', 'value'),
     Input('vehicle-store', 'data')]
)
def update_history_table(filter_value, numero):
    # 1. Fetch all data
    occurrences_and_services = fb.get_occurrences_and_services_by_vehicle(numero)
    damages = fb.get_damage_reports_by_vehicle(numero)

    # 2. Combine and standardize data
    combined_history = []
    for item in occurrences_and_services:
        combined_history.append({
            'data': item.get('data'),
            'tipo': item.get('tipo'),
            'descricao': item.get('nomenclatura'),
            'class': item.get('class'),
            'id': item.get('id'),
            'path': item.get('path')
        })

    for item in damages:
        combined_history.append({
            'data': item.get('data'),
            'tipo': 'Dano',
            'descricao': f"{item.get('parte')}: {item.get('descricao')}",
            'class': 'dano',
            'id': None,  # No details page for damages yet
            'path': None
        })

    # 3. Sort by date (newest first)
    combined_history.sort(key=lambda x: x['data'], reverse=True)

    # 4. Filter data
    if filter_value != 'todos':
        filtered_history = [item for item in combined_history if item['class'] == filter_value]
    else:
        filtered_history = combined_history

    if not filtered_history:
        return html.P("Nenhum registro encontrado para este filtro.")

    # 5. Create table
    table_header = [
        html.Thead(html.Tr([html.Th("Data"), html.Th("Tipo"), html.Th("Descrição")]))
    ]
    table_body = [html.Tbody([
        html.Tr([
            html.Td(item['data']),
            html.Td(item['tipo']),
            html.Td(item['descricao']),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/{item['path']}/{item['id']}", className="btn_view")
            ) if item.get('id') else None
        ]) for item in filtered_history
    ])]

    return html.Table(table_header + table_body, className='table-ocurrences')

@callback(
    [Output('agent-list', 'options'),
     Output('agent-list', 'value')],
    [Input('agent-filter-dropdown', 'value'),
     Input('agent-modal', 'style')],
    State('agent-list', 'value')
)
def update_agent_list(filter_value, modal_style, current_value):
    if not modal_style or modal_style.get('display') != 'block':
        raise dash.exceptions.PreventUpdate

    if filter_value == 'unassigned':
        filtered_agents = fb.get_unassigned_agents()
    else:
        filtered_agents = fb.get_all_agents()

    options = [
        {'label': f"{a.get('nome')} ({a.get('funcao')})", 'value': a.get('id')}
        for a in filtered_agents
    ]

    values_in_options = [opt['value'] for opt in options]
    if current_value in values_in_options:
        return options, current_value
    else:
        return options, None

@callback(
    [Output('agent-modal', 'style', allow_duplicate=True),
     Output('agent-assignment-trigger', 'data')],
    Input('assign-agent-button', 'n_clicks'),
    [State('agent-list', 'value'),
     State('vehicle-store', 'data'),
     State('assign-shift-dropdown', 'value'),
     State('assign-role-dropdown', 'value'),
     State('agent-assignment-trigger', 'data')],
    prevent_initial_call=True
)
def assign_agent(n_clicks, agent_id, vehicle_numero, shift, role, trigger):
    if n_clicks and agent_id and vehicle_numero and shift and role:
        fb.update_agent(agent_id, {
            'viatura ': vehicle_numero,
            'turno': shift,
            'funcao': role
        })
        print(f"Assigned agent {agent_id} to vehicle {vehicle_numero} with shift {shift} and role {role}")
        return {'display': 'none'}, trigger + 1
    return dash.no_update, dash.no_update


@callback(
    Output('agents-grid', 'children'),
    [Input('dropdown-turnos', 'value'),
     Input('agent-assignment-trigger', 'data')],
    State('vehicle-store', 'data')
)
def update_agents_by_shift(selected_shift, trigger, vehicle_numero):
    if not vehicle_numero:
        return []

    all_agents_for_vehicle = fb.get_agents_by_vehicle(vehicle_numero)

    # 2. Filtra por turno
    if selected_shift and selected_shift != 'todos':
        agents_to_display = [a for a in all_agents_for_vehicle if a.get('turno') == selected_shift]
    else:
        agents_to_display = all_agents_for_vehicle

    # 3. Separa motorista e outros agentes
    motorista = next((a for a in agents_to_display if a.get('funcao', '').lower() == 'motorista'), None)
    another_agents = [a for a in agents_to_display if a != motorista]

    # 4. Cria os componentes HTML
    children = []

    # Box do Motorista
    if motorista:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=motorista.get('foto_agnt'), className='img_agent'),
                        html.P(f"{motorista.get('nome')}", className='agent-name'),
                        html.P(f"Função: {motorista.get('funcao', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {motorista.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{motorista.get('id')}", className='link-ag-vt'
                ),
                html.Button('Remover', id={'type': 'remove-agent-button', 'agent_id': motorista.get('id')},
                            className='btn-remover')
            ], className='agent-box motorista')
        )
    else:
        children.append(
            html.Div(
                html.Div([
                    html.P("Sem motorista para este turno", className='agent-name'),
                ], className='add-driver-box-content'),
                id='add-driver-button', className='agent-box add-driver-box', title='Adicionar motorista',
                style={'display': 'none' if motorista else 'block'}
            )
        )

    # Boxes dos outros agentes
    for agente in another_agents:
        children.append(
            html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(src=agente.get('foto_agnt'), className='img_agent'),
                        html.P(f"{agente.get('nome')}", className='agent-name'),
                        html.P(f"Função: {agente.get('funcao', '').capitalize()}", className='agent-role'),
                        html.P(f"Turno: {agente.get('turno', 'N/A').capitalize()}", className='turno-status'),
                    ], className='agent-box-link'),
                    href=f"/dashboard/agent/{agente.get('id')}", className='link-ag-vt'
                ),
                html.Button('Remover', id={'type': 'remove-agent-button', 'agent_id': agente.get('id')},
                            className='btn-remover')
            ], className='agent-box')
        )

    # Box para adicionar agente
    children.append(
        html.Button(
            "+",
            id='add-agent-button',
            className='agent-box add-agent-box',
            title='Adicionar agente',
            style={'font-size': '3rem', 'border': 'none', 'cursor': 'pointer'}
        )
    )

    return children

@callback(
    Output('agent-modal', 'style'),
    Input('add-agent-button', 'n_clicks'),
    Input('modal-close-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(add_agent_clicks, close_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'add-agent-button':
        print("Abrindo modal")
        return {'display': 'block'}

    if trigger_id == 'modal-close-button':
        return {'display': 'none'}

    return {'display': 'none'}


@callback(
    Output('agent-assignment-trigger', 'data', allow_duplicate=True),
    Input({'type': 'remove-agent-button', 'agent_id': dash.ALL}, 'n_clicks'),
    State('agent-assignment-trigger', 'data'),
    prevent_initial_call=True
)
def remove_agent(n_clicks, trigger):
    # Encontra qual botão foi clicado
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    agent_id_to_remove = eval(button_id)['agent_id']

    agent_to_remove = fb.get_agent_by_id(agent_id_to_remove)

    if agent_to_remove:
        fb.update_agent(agent_id_to_remove, {
            'viatura': '',
            'funcao': '',
            'turno': ''
        })
        print(f"Removed agent {agent_id_to_remove} from their vehicle.")
        return trigger + 1

    return dash.no_update


@callback(
    Output("modal-delete-vehicle", "style"),
    [Input("rem_vehicle_btn", "n_clicks"),
     Input("cancel-delete-vehicle", "n_clicks"),
     Input("cancel-delete-vehicle-x", "n_clicks")],
    [State("modal-delete-vehicle", "style")],
    prevent_initial_call=True,
)
def toggle_delete_modal(n_open, n_cancel, n_cancel_x, style):
    if n_open or n_cancel or n_cancel_x:
        if style and style.get('display') == 'flex':
            return {'display': 'none'}
        else:
            return {'display': 'flex'}
    return style


@callback(
    Output('url-redirect', 'pathname'),
    Input('confirm-delete-vehicle', 'n_clicks'),
    State('vehicle-store', 'data'),
    prevent_initial_call=True
)
def delete_vehicle(n_clicks, numero):
    if n_clicks:
        if fb.delete_vehicle(numero):
            return '/dashboard/pageVehicles'
    return dash.no_update