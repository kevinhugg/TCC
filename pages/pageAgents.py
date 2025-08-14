import dash
from dash import html, dcc, Input, Output, callback, State, no_update
from dash.exceptions import PreventUpdate
import firebase_functions as fb

# from data.dados import agents, viaturas

dash.register_page(__name__, path='/pageAgents', name='Agentes')

confirm_remove = dcc.ConfirmDialog(
    id='confirm-remove-agent',
    message='Deseja realmente remover os agentes selecionados?',
)


def layout():
    # Fetch vehicles for the dropdown inside the layout function
    try:
        viaturas = fb.get_all_vehicles()
        viaturas_options = [{'label': v.get('numero', ''), 'value': v.get('numero', '')} for v in viaturas]
    except Exception as e:
        # If firebase fails, show an error and prevent the page from crashing
        print(f"Error fetching vehicles from Firebase: {e}")
        viaturas_options = []
        return html.Div([
            html.H3("Erro ao carregar dados"),
            html.P("Não foi possível conectar ao banco de dados para buscar as viaturas.")
        ])

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
                                options=viaturas_options,
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

    return html.Div([

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
                        html.A(id='pdf_agentes_gerar', children='Gerar PDF', target="_blank",
                               className='btn btn-primary')
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
    selected_ids = [item for sublist in selected_values for item in sublist if sublist]
    return selected_ids


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
    if not submit_clicks or not selected_agents:
        raise PreventUpdate

    for agent_id in selected_agents:
        fb.delete_agent(agent_id)

    # The list will be refreshed by the update_list callback,
    # which is also listening to 'confirm-remove-agent.submit_n_clicks'
    return no_update


@callback(
    Output('agents-table', 'children'),
    Output('pdf_agentes_gerar', 'href'),
    Output('select-header', 'style'),
    Output('select-header', 'children'),
    Input('input-search', 'value'),
    Input('submit-add-agent', 'n_clicks'),
    Input('edit-mode', 'data'),
    Input('confirm-remove-agent', 'submit_n_clicks'),  # Add this to refresh list after deletion
    State('add-agent-name', 'value'),
    State('add-agent-cargo', 'value'),
    State('add-agent-funcao', 'value'),
    State('add-agent-veiculo', 'value'),
    prevent_initial_call=False
)
def update_list(search_value, submit_clicks, edit_mode, remove_clicks, name, cargo, funcao, veiculo):
    ctx = dash.callback_context

    # JULES: Add agent creation logic here later
    if ctx.triggered and 'submit-add-agent.n_clicks' in ctx.triggered[0]['prop_id']:
        if name and cargo and funcao:  # Basic validation
            new_agent = {
                'nome': name,
                'cargo_at': cargo,
                'funcao': funcao,
                'viatura': veiculo or "",  # Ensure it's not None
                'turno': "",  # Not specified in modal
                'foto_agnt': '/static/assets/img/persona.png'  # Default photo
            }
            fb.add_agent(new_agent)
        else:
            print("Agent not added, missing fields")

    try:
        agents = fb.get_all_agents()
    except Exception as e:
        print(f"Error fetching agents from Firebase: {e}")
        return [html.Tr([
            html.Td("Erro ao carregar agentes!", colSpan=6, className='not-found'),
        ])], "/gerar_pdf_agentes", {'display': 'none'}, ""

    if not search_value:
        filtered = agents
    else:
        search_value = search_value.lower()
        filtered = [
            a for a in agents
            if search_value in a.get('nome', '').lower() or
               search_value in a.get('funcao', '').lower() or  # Mapped to 'funcao' from firebase
               search_value in a.get('cargo_at', '').lower()  # Assuming 'cargo_at' exists
        ]

    if not filtered:
        return [html.Tr([
            html.Td("Agente não encontrado!", colSpan=6, className='not-found'),
        ])], f"/gerar_pdf_agentes?filtro={search_value}", {'display': 'none'}, ""

    rows = []
    for item in filtered:
        # Check for agent ID, 'id' is from firebase function, 'matricula' is another possibility
        agent_id = item.get('id') or item.get('matricula')
        if not agent_id:
            continue  # Skip agents without a unique identifier

        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'agent-select', 'index': agent_id},
                options=[{'label': '', 'value': agent_id}],
                value=[],
                className='agent-checkbox'
            ),
            className='select-cell',
            style={'display': 'none'} if not edit_mode else {}
        )

        rows.append(html.Tr([
            checkbox_cell,
            html.Td(item.get('nome', 'N/A')),
            html.Td(item.get('cargo_at', 'N/A')),  # Mapped to 'cargo_at'
            html.Td(item.get('funcao', 'N/A')),  # Mapped to 'funcao'
            html.Td(
                dcc.Link(item.get('viatura', 'N/A'), href=f"/dashboard/veiculo/{item.get('viatura', '')}"),
                # Mapped to 'viatura'
                className='btn_veh'
            ),
            html.Td(
                dcc.Link('Ver Mais', href=f"/dashboard/agent/{agent_id}"),
                className='btn_view'
            ),
        ]))

    pdf_link = f"/gerar_pdf_agentes?filtro={search_value}" if search_value else "/gerar_pdf_agentes"

    header_style = {'display': 'none'} if not edit_mode else {}
    header_text = "Selecionar" if edit_mode else ""

    return rows, pdf_link, header_style, header_text