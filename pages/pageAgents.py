import dash
from dash import html, dcc, Input, Output, callback, State, no_update
from dash.exceptions import PreventUpdate
from data.dados import agents, viaturas

dash.register_page(__name__, path='/pageAgents', name='Agentes')

add_agent_modal = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Adicionar Agente", className="modal-title"),
                        dcc.Input(
                            id='add-agent-name',
                            type='text',
                            placeholder='Nome',
                            className='modal-input'
                        ),
                        dcc.Input(
                            id='add-agent-cargo',
                            type='text',
                            placeholder='Cargo',
                            className='modal-input'
                        ),
                        dcc.Input(
                            id='add-agent-funcao',
                            type='text',
                            placeholder='Função',
                            className='modal-input'
                        ),
                        dcc.Dropdown(
                            id='add-agent-veiculo',
                            options=[{'label': v['numero'], 'value': v['numero']} for v in viaturas],
                            placeholder='Selecione o Veículo',
                            className='modal-dropdown'
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "Cancelar",
                                    id="cancel-add-agent",
                                    className="modal-button cancel"
                                ),
                                html.Button(
                                    "Salvar",
                                    id="submit-add-agent",
                                    className="modal-button submit"
                                ),
                            ],
                            className="modal-buttons"
                        ),
                    ],
                    className="modal-content"
                ),
            ],
            className="modal",
            id="add-agent-modal",
            style={'display': 'none'}
        ),
    ],
    id="modal-container"
)

confirm_remove = dcc.ConfirmDialog(
    id='confirm-remove-agent',
    message='Deseja realmente remover os agentes selecionados?',
)

layout = html.Div([

    html.Link(rel='stylesheet', href='/static/css/dark_mode.css'),

    html.Link(rel='stylesheet', href='/static/css/styleAgents.css'),
    html.Link(rel='stylesheet', href='/static/css/modal.css'),
    dcc.Store(id='theme-mode', storage_type='local'),

    dcc.Store(id='filtro-search'),
    dcc.Store(id='selected-agents', data=[]),
    dcc.Store(id='edit-mode', data=False),

    confirm_remove,
    add_agent_modal,

    html.Div([
        html.Div([
            html.Div([
                dcc.Input(id='input-search', type='text', placeholder='Buscar por nome ou função...',
                          className='input-search'),
            ], className='searchbar'),

            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Selecionar', id='select-header', style={'display': 'none'}),
                        html.Th('Nome'),
                        html.Th('Cargo'),
                        html.Th('Função'),
                        html.Th('Veículo'),
                        html.Th('Ações')
                    ])
                ]),
                html.Tbody(id='agents-table')
            ], className='agents-table'),

            html.Div([
                html.Div([
                    html.Button(
                        id='rem_agents',
                        children='Remover Agentes',
                        className='btn btn-danger',
                        n_clicks=0
                    )
                ], className='btn'),

                html.Div([
                    html.A(id='pdf_agentes_gerar', children='Gerar PDF', target="_blank", className='btn btn-primary')
                ], className='btn-pdf-agent'),

                html.Div([
                    html.Button(
                        id='add_agents',
                        children='Adicionar Agente',
                        className='btn btn-success',
                        n_clicks=0
                    )
                ], className='btn'),
            ], className='btn_rem_add_pdf'),
        ], className='agents_container'),
    ])
], className='page-content')


@callback(
    Output('add-agent-modal', 'style'),
    Input('add_agents', 'n_clicks'),
    Input('cancel-add-agent', 'n_clicks'),
    Input('submit-add-agent', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(add_clicks, cancel_clicks, submit_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add_agents':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@callback(
    Output('confirm-remove-agent', 'displayed'),
    Input('rem_agents', 'n_clicks'),
    State('selected-agents', 'data'),
    State('edit-mode', 'data'),
    prevent_initial_call=True
)
def confirm_removal(n_clicks, selected_agents, edit_mode):
    if n_clicks > 0 and edit_mode:
        if not selected_agents:
            raise PreventUpdate
        return True
    return False


@callback(
    Output('selected-agents', 'data'),
    Input({'type': 'agent-select', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def update_selected_agents(selected_values):
    return [item for sublist in selected_values for item in sublist]


@callback(
    Output('edit-mode', 'data'),
    Input('rem_agents', 'n_clicks'),
    State('edit-mode', 'data'),
    prevent_initial_call=True
)
def toggle_edit_mode(n_clicks, current_mode):
    if n_clicks > 0:
        return not current_mode
    return current_mode


@callback(
    Output('agents-table', 'children', allow_duplicate=True),
    Input('confirm-remove-agent', 'submit_n_clicks'),
    State('selected-agents', 'data'),
    prevent_initial_call=True
)
def remove_selected_agents(submit_clicks, selected_agents):
    if submit_clicks:
        global agents
        agents = [agent for agent in agents if agent['id'] not in selected_agents]

        rows = []
        for item in agents:
            rows.append(html.Tr([
                html.Td(
                    dcc.Checklist(
                        id={'type': 'agent-select', 'index': item['id']},
                        options=[{'label': '', 'value': item['id']}],
                        value=[],
                        className='agent-checkbox'
                    ),
                    className='select-cell',
                    style={'display': 'none'}
                ),
                html.Td(item['nome']),
                html.Td(item['cargo_at']),
                html.Td(item['func_mes']),
                html.Td(
                    dcc.Link(item['viatura_mes'], href=f"/dashboard/veiculo/{item['viatura_mes']}"),
                    className='btn_veh'
                ),
                html.Td(
                    dcc.Link('Ver Mais', href=f"/dashboard/agent/{item['id']}"),
                    className='btn_view'
                ),
            ]))
        return rows
    raise PreventUpdate


@callback(
    Output('agents-table', 'children'),
    Output('pdf_agentes_gerar', 'href'),
    Output('select-header', 'style'),
    Output('select-header', 'children'),
    Input('input-search', 'value'),
    Input('submit-add-agent', 'n_clicks'),
    Input('edit-mode', 'data'),
    State('add-agent-name', 'value'),
    State('add-agent-cargo', 'value'),
    State('add-agent-funcao', 'value'),
    State('add-agent-veiculo', 'value'),
    prevent_initial_call=False
)
def update_list(search_value, submit_clicks, edit_mode, name, cargo, funcao, veiculo):
    ctx = dash.callback_context

    initial_load = not ctx.triggered or ctx.triggered[0]['prop_id'] == '.'

    if initial_load:
        edit_mode = False
        if not search_value:
            filtered = agents
        else:
            search_value = search_value.lower()
            filtered = [
                a for a in agents
                if search_value in a['nome'].lower() or
                   search_value in a['func_mes'].lower() or
                   search_value in a['cargo_at'].lower()
            ]
    else:
        if 'submit-add-agent.n_clicks' in ctx.triggered[0]['prop_id']:
            new_agent = {
                'id': len(agents) + 1,
                'nome': name,
                'cargo_at': cargo,
                'func_mes': funcao,
                'viatura_mes': veiculo,
                'foto_agnt': '/static/img/default-user.png'
            }
            agents.append(new_agent)

        if not search_value:
            filtered = agents
        else:
            search_value = search_value.lower()
            filtered = [
                a for a in agents
                if search_value in a['nome'].lower() or
                   search_value in a['func_mes'].lower() or
                   search_value in a['cargo_at'].lower()
            ]

    if not filtered:
        return [html.Tr([
            html.Td("Agente não encontrado!", colSpan=6, className='not-found'),
        ])], f"/gerar_pdf_agentes?filtro={search_value}", {'display': 'none'}, ""

    rows = []
    for item in filtered:
        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'agent-select', 'index': item['id']},
                options=[{'label': '', 'value': item['id']}],
                value=[],
                className='agent-checkbox'
            ),
            className='select-cell',
            style={'display': 'none'} if not edit_mode else {}
        )

        rows.append(html.Tr([
            checkbox_cell,
            html.Td(item['nome']),
            html.Td(item['cargo_at']),
            html.Td(item['func_mes']),
            html.Td(
                dcc.Link(item['viatura_mes'], href=f"/dashboard/veiculo/{item['viatura_mes']}"),
                className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/agent/{item['id']}"),
                className='btn_view'
            ),
        ]))

    pdf_link = f"/gerar_pdf_agentes?filtro={search_value}" if search_value else "/gerar_pdf_agentes"

    header_style = {'display': 'none'} if not edit_mode else {}
    header_text = "Selecionar" if edit_mode else ""

    return rows, pdf_link, header_style, header_text