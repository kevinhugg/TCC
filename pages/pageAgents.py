import dash
from dash import html, dcc, Input, Output, callback, State, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    import firebase_functions as fb
    FIREBASE_AVAILABLE = True
except ImportError as e:
    FIREBASE_AVAILABLE = False

dash.register_page(__name__, path='/pageAgents', name='Agentes')

def layout():
    try:
        viaturas = fb.get_all_vehicles() if FIREBASE_AVAILABLE else []
        viaturas_options = [{'label': v.get('numero', ''), 'value': v.get('numero', '')} for v in viaturas] if viaturas else []
        agents = fb.get_all_agents() if FIREBASE_AVAILABLE else []
    except Exception as e:
        viaturas_options = []
        return html.Div([
            html.H3("Erro ao carregar dados"),
            html.P("Não foi possível conectar ao banco de dados."),
            html.P(f"Erro: {str(e)}")
        ])

    equipe_options = [{'label': equipe.capitalize(), 'value': equipe} for equipe in fb.get_equipe_options()] if FIREBASE_AVAILABLE else []
    funcao_options = [{'label': funcao.capitalize(), 'value': funcao} for funcao in fb.get_funcao_options()] if FIREBASE_AVAILABLE else []
    patente_options = [{'label': patente.capitalize(), 'value': patente} for patente in fb.get_patente_options()] if FIREBASE_AVAILABLE else []
    
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
                style={'width': '700px'},
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
                            html.Div(className='form-row', style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}, children=[
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Nome:*", style={'fontWeight': 'bold'}),
                                    dcc.Input(
                                        id='add-agent-name', 
                                        placeholder="Nome completo do agente", 
                                        className='modal-input',
                                        required=True
                                    ),
                                ]),
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Matrícula:*", style={'fontWeight': 'bold'}),
                                    dcc.Input(
                                        id='add-agent-matricula', 
                                        placeholder="Número da matrícula", 
                                        className='modal-input',
                                        required=True
                                    ),
                                ]),
                            ]),
                            html.Div(className='form-row', style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}, children=[
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Idade:*", style={'fontWeight': 'bold'}),
                                    dcc.Input(
                                        id='add-agent-idade', 
                                        type='number', 
                                        placeholder="Idade", 
                                        className='modal-input',
                                        min=18,
                                        max=70
                                    ),
                                ]),
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Patente:", style={'fontWeight': 'bold'}),
                                    dcc.Dropdown(
                                        id='add-agent-patente',
                                        options=patente_options,
                                        placeholder="Selecione a patente...",
                                        className='modal-input'
                                    ),
                                ]),
                            ]),
                            html.Div(className='form-row', style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}, children=[
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Equipe:", style={'fontWeight': 'bold'}),
                                    dcc.Dropdown(
                                        id='add-agent-equipe',
                                        options=equipe_options,
                                        placeholder="Selecione a equipe...",
                                        className='modal-input'
                                    ),
                                ]),
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Função:", style={'fontWeight': 'bold'}),
                                    dcc.Dropdown(
                                        id='add-agent-funcao',
                                        options=funcao_options,
                                        placeholder="Selecione a função...",
                                        className='modal-input'
                                    ),
                                ]),
                            ]),
                            html.Div(className='form-row', style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}, children=[
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Turno:", style={'fontWeight': 'bold'}),
                                    dcc.Dropdown(
                                        id='add-agent-turno',
                                        options=turno_options,
                                        placeholder="Selecione o turno...",
                                        className='modal-input'
                                    ),
                                ]),
                                html.Div(className='form-group', style={'flex': '1'}, children=[
                                    html.Label("Veículo:", style={'fontWeight': 'bold'}),
                                    dcc.Dropdown(
                                        id='add-agent-veiculo',
                                        options=viaturas_options,
                                        placeholder="Selecione o veículo...",
                                        className='modal-input'
                                    ),
                                ]),
                            ]),
                            html.Div(id='upload-error-message-agent', style={'color': 'red', 'marginBottom': '15px'}),
                            html.Div(className='form-group', children=[
                                html.Label("Foto do Agente:", style={'fontWeight': 'bold'}),
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
        dcc.Interval(
            id='interval-agents',
            interval=10*1000,
            n_intervals=0
        ),
        confirm_remove,
        add_agent_modal,
        html.Div([
            html.Div([
                html.Div([
                    dcc.Input(id='input-search', type='text', placeholder='Buscar por nome, função, equipe ou patente...',
                              className='input-search'),
                ], className='searchbar'),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Selecionar', id='select-header', style={'display': 'none'}),
                            html.Th('Nome'),
                            html.Th('Patente'),
                            html.Th('Função'),
                            html.Th('Equipe'),
                            html.Th('Veículo'),
                            html.Th('Turno'),
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
    Input('submit-add-agent', 'n_clicks'),
    State('modal-add-agent', 'style'),
    prevent_initial_call=True
)
def toggle_agent_modal(add_clicks, cancel_clicks, cancel_x_clicks, submit_clicks, style):
    triggered_id = ctx.triggered_id
    
    if triggered_id in ['add_agents']:
        return {'display': 'flex'}
    
    if triggered_id in ['cancel-add-agent', 'cancel-add-agent-x', 'submit-add-agent']:
        return {'display': 'none'}
    
    return style

@callback(
    [Output('url-agents', 'pathname', allow_duplicate=True),
     Output('modal-add-agent', 'style', allow_duplicate=True),
     Output('add-agent-name', 'value'),
     Output('add-agent-matricula', 'value'),
     Output('add-agent-idade', 'value'),
     Output('add-agent-patente', 'value'),
     Output('add-agent-equipe', 'value'),
     Output('add-agent-funcao', 'value'),
     Output('add-agent-turno', 'value'),
     Output('add-agent-veiculo', 'value'),
     Output('upload-error-message-agent', 'children')],
    Input('submit-add-agent', 'n_clicks'),
    [State('add-agent-name', 'value'),
     State('add-agent-matricula', 'value'),
     State('add-agent-idade', 'value'),
     State('add-agent-patente', 'value'),
     State('add-agent-equipe', 'value'),
     State('add-agent-funcao', 'value'),
     State('add-agent-turno', 'value'),
     State('add-agent-veiculo', 'value'),
     State('upload-agent-image', 'contents'),
     State('upload-agent-image', 'filename')],
    prevent_initial_call=True
)
def handle_add_agent(n_clicks, name, matricula, idade, patente, equipe, funcao, turno, veiculo, contents, filename):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, ""
    
    if not all([name, matricula, idade]):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Por favor, preencha os campos obrigatórios (Nome, Matrícula e Idade)."

    if not matricula.isalnum():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Matrícula deve conter apenas letras e números."

    foto_url = 'https://firebasestorage.googleapis.com/v0/b/tcc-semurb-2ea61.appspot.com/o/agentes%2Fpersona.png?alt=media&token=c23068da-25a5-45elyn-846c-d2a637886358'
    foto_path = ''
    
    if contents and filename:
        try:
            if FIREBASE_AVAILABLE:
                foto_url, foto_path = fb.upload_image_to_storage(contents, filename, folder="agentes")
                if not foto_url:
                    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Erro no upload da imagem."
            else:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Firebase não disponível para upload de imagem."
        except Exception as e:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, f"Erro no upload da imagem: {e}"

    new_agent = {
        'nome': name.strip(),
        'matricula': matricula.strip(),
        'idade': idade,
        'patente': patente or '',
        'equipe': equipe or '',
        'funcao': funcao or '',
        'turno': turno or '',
        'viatura': veiculo or '',
        'ocorrencias': "0",
        'foto_agnt': foto_url,  
        'foto_path': foto_path,
        'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        if FIREBASE_AVAILABLE:
            success = fb.add_agent(new_agent)
            if success:
                email = f"{matricula.strip()}@gmail.com"
                senha_inicial = "123456"
                
                credenciais_msg = html.Div([
                    html.P("✅ Agente cadastrado com sucesso!", 
                        style={'color': 'green', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                    html.Div([
                    html.Strong("Credenciais de acesso (Firebase Authentication):"),
                    html.Br(),
                    html.Strong("Email: "), email,
                    html.Br(),
                    html.Strong("Senha inicial: "), senha_inicial
                ], style={
                    'backgroundColor': '#f8f9fa', 
                    'padding': '15px', 
                    'borderRadius': '5px',
                    'border': '1px solid #dee2e6',
                    'marginTop': '10px',
                    'fontSize': '14px'
                }),
                    html.P("⚠️ Estas credenciais foram criadas no Firebase Authentication e podem ser usadas para login no app mobile.", 
                    style={'color': '#856404', 'marginTop': '10px', 'fontSize': '13px'})
                ])
                
                return '/dashboard/pageAgents', {'display': 'none'}, '', '', '', None, None, None, None, None, credenciais_msg
            else:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Erro ao adicionar agente ao banco de dados."
        else:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Firebase não disponível."
            
    except Exception as e:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, f"Erro ao adicionar agente: {e}"

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
        button_text = "Confirmar Remoção" if new_mode else "Remover Agentes"
        return new_mode, button_text
    return current_mode, "Remover Agentes"

@callback(
    Output('url-agents', 'pathname', allow_duplicate=True),
    Output('selected-agents', 'data', allow_duplicate=True),
    Output('edit-mode', 'data', allow_duplicate=True),
    Input('confirm-remove-agent', 'submit_n_clicks'),
    State('selected-agents', 'data'),
    prevent_initial_call=True
)
def remove_selected_agents(submit_clicks, selected_agents):
    if submit_clicks and selected_agents:
        success_count = 0
        for agent_id in selected_agents:
            if FIREBASE_AVAILABLE:
                if fb.delete_agent(agent_id):
                    success_count += 1
        return '/dashboard/pageAgents', [], False
    return no_update, no_update, no_update

@callback(
    Output('agents-table', 'children'),
    Output('pdf_agentes_gerar', 'href'),
    Output('select-header', 'style'),
    [Input('input-search', 'value'),
     Input('edit-mode', 'data'),
     Input('url-agents', 'pathname'),
     Input('interval-agents', 'n_intervals')],
    prevent_initial_call=True
)
def update_list(search_value, edit_mode, pathname, n_intervals):
    try:
        if FIREBASE_AVAILABLE:
            agents = fb.get_all_agents()
        else:
            agents = []
    except Exception as e:
        return [html.Tr([html.Td("Erro ao carregar agentes!", colSpan=8)])], "/gerar_pdf_agentes", {'display': 'none'}

    if search_value:
        search_term = search_value.lower()
        filtered = [a for a in agents if
                    search_term in a.get('nome', '').lower() or
                    search_term in a.get('funcao', '').lower() or
                    search_term in a.get('patente', '').lower() or
                    search_term in a.get('equipe', '').lower() or
                    search_term in a.get('viatura', '').lower() or
                    search_term in a.get('turno', '').lower()]
    else:
        filtered = agents

    if not filtered:
        return [html.Tr([html.Td("Nenhum agente encontrado!", colSpan=8)])], "/gerar_pdf_agentes", {'display': 'none'}

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

        patente_display = item.get('patente', 'N/A').capitalize() if item.get('patente') else 'N/A'
        equipe_display = item.get('equipe', 'N/A').capitalize() if item.get('equipe') else 'N/A'
        funcao_display = item.get('funcao', 'N/A').capitalize() if item.get('funcao') else 'N/A'
        turno_display = item.get('turno', 'N/A').capitalize() if item.get('turno') else 'N/A'

        veiculo = item.get('viatura', 'N/A')
        veiculo_cell = html.Td(
            dcc.Link(
                veiculo, 
                href=f"/dashboard/veiculo/{veiculo}",
                className='btn_veh'
            ) if veiculo and veiculo != 'N/A' else html.Td(veiculo)
        )

        nome_cell = html.Td(
            dcc.Link(
                item.get('nome', 'N/A'), 
                href=f"/dashboard/agent/{agent_id}",
                className='btn_ag'
            )
        )

        ver_mais_cell = html.Td(
            dcc.Link(
                'Ver Mais', 
                href=f"/dashboard/agent/{agent_id}",
                className='btn_view'
            )
        )

        rows.append(html.Tr([
            checkbox_cell,
            nome_cell,
            html.Td(patente_display),
            html.Td(funcao_display),
            html.Td(equipe_display),
            veiculo_cell,
            html.Td(turno_display),
            ver_mais_cell,
        ]))

    pdf_link = f"/gerar_pdf_agentes?filtro={search_value or ''}"
    header_style = {'display': 'table-cell' if edit_mode else 'none'}

    return rows, pdf_link, header_style