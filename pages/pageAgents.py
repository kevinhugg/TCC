import dash
from dash import html, dcc, Input, Output, callback, State, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import firebase_functions as fb

dash.register_page(__name__, path='/pageAgents', name='Agentes')

def layout():
    try:
        viaturas = fb.get_all_vehicles()
        viaturas_options = [{'label': v.get('numero', ''), 'value': v.get('numero', '')} for v in viaturas] if viaturas else []
    except Exception as e:
        print(f"Error fetching vehicles from Firebase: {e}")
        viaturas_options = []
        return html.Div([
            html.H3("Erro ao carregar dados"),
            html.P("Não foi possível conectar ao banco de dados para buscar as viaturas.")
        ])

    funcao_options = [
        {'label': 'Encarregado', 'value': 'Encarregado'},
        {'label': 'Motorista', 'value': 'Motorista'},
        {'label': 'Agente', 'value': 'Agente'},
    ]
    turno_options = [
        {'label': 'Manhã', 'value': 'manha'},
        {'label': 'Tarde', 'value': 'tarde'},
        {'label': 'Noite', 'value': 'noite'},
    ]

    add_agent_modal = html.Div(
    id='modal-add-agent',
    className='modal',
    style={'display': 'none'},
    children=[
        html.Div(
            className='modal-content',
            children=[
                html.Div(
                    className='modal-header',
                    children=[
                        html.H5('Adicionar Novo Agente', className='modal-title'),
                        html.Button('×', id='cancel-add-agent-x', className='modal-close-button')
                    ]
                ),
                html.Div(
                    className='modal-body',
                    children=[
                        html.Div(className='form-group', children=[
                            html.Label("Nome:"),
                            dcc.Input(id='add-agent-name', placeholder="Nome completo do agente", className='modal-input'),
                        ]),
                        html.Div(className='form-group', children=[
                            html.Label("Matrícula:"),
                            dcc.Input(id='add-agent-matricula', placeholder="Matrícula do agente", className='modal-input'),
                        ]),
                        html.Div(className='form-group', children=[
                            html.Label("Idade:"),
                            dcc.Input(id='add-agent-idade', type='number', placeholder="Idade", className='modal-input'),
                        ]),
                        html.Div(id='upload-error-message-agent', style={'color': 'red'}),
                        html.Div(className='form-group', children=[
                            html.Label("Foto do Agente:"),
                            html.Div(
                                id='upload-container-agent',
                                style={'position': 'relative', 'padding': '10px'},
                                children=[
                                    dcc.Upload(
                                        id='upload-agent-image',
                                        children=html.Div([
                                            html.I(className="fas fa-camera", style={'fontSize': '2rem', 'marginBottom': '0.5rem'}),
                                            html.Br(),
                                            'Arraste e solte ou ',
                                            html.A('Selecione uma imagem')
                                        ]),
                                        className='upload-area-agent',
                                        accept='image/*'
                                    ),
                                    html.Div(id='image-preview-container-agent', style={'display': 'none'}, children=[
                                        html.Img(id='image-preview-agent', style={'width': '200px', 'height': '120px', 'objectFit': 'cover'}),
                                        html.Button('×', id='remove-image-button-agent', className='remove-image-btn')
                                    ])
                                ]
                            )
                        ]),
                    ]
                ),
                html.Div(
                    className='modal-footer',
                    children=[
                        html.Button("Cancelar", id="cancel-add-agent", className='modal-button cancel'),
                        html.Button("Salvar", id="submit-add-agent", className='modal-button submit'),
                    ]
                )
            ]
        )
    ]
)

    confirm_remove = dcc.ConfirmDialog(
        id='confirm-remove-agent',
        message='Deseja realmente remover os agentes selecionados?',
    )

    return html.Div([
        html.Link(rel='stylesheet', href='/static/css/styleAgents.css'),
        html.Link(rel='stylesheet', href='/static/css/modal.css'),
        dcc.Store(id='selected-agents', data=[]),
        dcc.Store(id='edit-mode', data=False),
        dcc.Location(id='url-agents', refresh=True),

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
                            html.Th('Função'),
                            html.Th('Veículo'),
                            html.Th('Ações')
                        ])
                    ]),
                    html.Tbody(id='agents-table')
                ], className='agents-table'),

                html.Div([
                    html.Button(id='rem_agents', children='Remover Agentes', className='btn btn-danger'),
                    html.A(id='pdf_agentes_gerar', children='Gerar PDF', target="_blank",
                           className='btn btn-primary'),
                    html.Button(id='add_agents', children='Adicionar Agente', className='btn btn-success'),
                ], className='btn_rem_add'),
            ], className='agents_container'),
        ])
    ], className='page-content')


@callback(
    Output('image-preview-container-agent', 'style'),
    Output('image-preview-agent', 'src'),
    Output('upload-agent-image', 'style'),
    Input('upload-agent-image', 'contents'),
    Input('remove-image-button-agent', 'n_clicks'),
    prevent_initial_call=True
)
def update_image_preview_agent(contents, remove_clicks):
    triggered_id = ctx.triggered_id

    upload_style = {
        'width': '100%', 'height': '100px', 'lineHeight': '100px',
        'borderWidth': '2px', 'borderStyle': 'dashed',
        'borderRadius': '5px', 'textAlign': 'center', 'display': 'block'
    }
    hidden_upload_style = upload_style.copy()
    hidden_upload_style['display'] = 'none'

    if triggered_id == 'remove-image-button-agent':
        return {'display': 'none'}, '', upload_style

    if contents:
        return {'display': 'block', 'textAlign': 'center'}, contents, hidden_upload_style

    return {'display': 'none'}, '', upload_style


@callback(
    Output('modal-add-agent', 'style'),
    Input('add_agents', 'n_clicks'),
    Input('cancel-add-agent', 'n_clicks'),
    Input('cancel-add-agent-x', 'n_clicks'),
    State('modal-add-agent', 'style'),
    prevent_initial_call=True
)
def toggle_agent_modal(add_clicks, cancel_clicks, cancel_x_clicks, style):
    triggered_id = ctx.triggered_id
    if triggered_id in ['add_agents', 'cancel-add-agent', 'cancel-add-agent-x']:
        if style and style.get('display') == 'flex':
            return {'display': 'none'}
        else:
            return {'display': 'flex'}
    return style


@callback(
    Output('url-agents', 'pathname'),
    Output('modal-add-agent', 'style', allow_duplicate=True),
    Output('upload-error-message-agent', 'children'),
    Input('submit-add-agent', 'n_clicks'),
    State('add-agent-name', 'value'),
    State('add-agent-matricula', 'value'),
    State('add-agent-idade', 'value'),
    State('upload-agent-image', 'contents'),
    State('upload-agent-image', 'filename'),
    prevent_initial_call=True
)
def handle_add_agent(n_clicks, name, matricula, idade, contents, filename):
    if not n_clicks:
        return dash.no_update, dash.no_update, ""

    if not all([name, matricula, idade]):
        return dash.no_update, dash.no_update, "Por favor, preencha todos os campos."

    foto_url = 'https://firebasestorage.googleapis.com/v0/b/tcc-semurb-2ea61.appspot.com/o/agentes%2Fpersona.png?alt=media&token=c23068da-25a5-45elyn-846c-d2a637886358'
    foto_path = ''
    if contents and filename:
        try:
            foto_url, foto_path = fb.upload_image_to_storage(contents, filename, folder='agentes')
            if not foto_url:
                return dash.no_update, dash.no_update, "Erro no upload da imagem."
        except Exception as e:
            return dash.no_update, dash.no_update, f"Erro no upload da imagem: {e}"

    new_agent = {
        'nome': name,
        'matricula': matricula,
        'idade': idade,
        'cargo_at': "",
        'funcao': "",
        'turno': "",
        'viatura': "",
        'ocorrencias': "0",
        'foto_agnt': foto_url,
        'fotoPath': foto_path
    }
    fb.add_agent(new_agent)
    return '/dashboard/pageAgents', {'display': 'none'}, ""


@callback(
    Output('confirm-remove-agent', 'displayed'),
    Input('rem_agents', 'n_clicks'),
    State('selected-agents', 'data'),
    State('edit-mode', 'data'),
    prevent_initial_call=True
)
def confirm_removal(n_clicks, selected_agents, edit_mode):
    if n_clicks and edit_mode and selected_agents:
        return True
    return False


@callback(
    Output('selected-agents', 'data', allow_duplicate=True),
    Input({'type': 'agent-select', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def update_selected_agents(selected_values):
    return [item for sublist in selected_values for item in sublist if sublist]


@callback(
    Output('edit-mode', 'data'),
    Output('rem_agents', 'children'),
    Input('rem_agents', 'n_clicks'),
    State('edit-mode', 'data'),
    prevent_initial_call=True
)
def toggle_edit_mode(n_clicks, current_mode):
    if n_clicks:
        new_mode = not current_mode
        button_text = "Remover" if new_mode else "Remover Agentes"
        return new_mode, button_text
    return current_mode, "Remover Agentes"


@callback(
    Output('url-agents', 'pathname', allow_duplicate=True),
    Output('selected-agents', 'data', allow_duplicate=True),
    Input('confirm-remove-agent', 'submit_n_clicks'),
    State('selected-agents', 'data'),
    prevent_initial_call=True
)
def remove_selected_agents(submit_clicks, selected_agents):
    if submit_clicks and selected_agents:
        for agent_id in selected_agents:
            fb.delete_agent(agent_id)
        return '/pageAgents', []
    return no_update, no_update


@callback(
    Output('agents-table', 'children'),
    Output('pdf_agentes_gerar', 'href'),
    Output('select-header', 'style'),
    Input('input-search', 'value'),
    Input('edit-mode', 'data'),
    Input('url-agents', 'pathname')
)
def update_list(search_value, edit_mode, pathname):
    try:
        agents = fb.get_all_agents()
    except Exception as e:
        print(f"Error fetching agents from Firebase: {e}")
        return [html.Tr([html.Td("Erro ao carregar agentes!", colSpan=6)])], "/gerar_pdf_agentes", {'display': 'none'}

    if search_value:
        search_term = search_value.lower()
        filtered = [a for a in agents if
                    search_term in a.get('nome', '').lower() or
                    search_term in a.get('funcao', '').lower() or
                    search_term in a.get('cargo_at', '').lower()]
    else:
        filtered = agents

    if not filtered:
        return [html.Tr([html.Td("Agente não encontrado!", colSpan=6)])], "/gerar_pdf_agentes", {'display': 'none'}

    rows = []
    for item in filtered:
        agent_id = item.get('id')
        if not agent_id:
            continue

        checkbox_cell = html.Td(
            dcc.Checklist(
                id={'type': 'agent-select', 'index': agent_id},
                options=[{'label': '', 'value': agent_id}],
                value=[],
                className='agent-checkbox'
            ),
            style={'display': 'table-cell' if edit_mode else 'none'}
        )

        rows.append(html.Tr([
            checkbox_cell,
            html.Td(item.get('nome', 'N/A')),
            html.Td(item.get('funcao', 'N/A')),
            html.Td(dcc.Link(item.get('viatura', 'N/A'), href=f"/dashboard/veiculo/{item.get('viatura', '')}")),
            html.Td(dcc.Link('Ver Mais', href=f"/dashboard/agent/{agent_id}")),
        ]))

    pdf_link = f"/gerar_pdf_agentes?filtro={search_value or ''}"
    header_style = {'display': 'table-cell' if edit_mode else 'none'}

    return rows, pdf_link, header_style